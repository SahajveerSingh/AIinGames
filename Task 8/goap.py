'''
Goal Oriented Action Planning (GOAP)
COS30002 AI for Games

A complete GOAP implementation featuring:
  - World state represented as a frozenset of boolean flags
  - Actions with preconditions, effects, costs, and time delays
  - A* planner that sequences actions to reach a goal state
  - Interactive simulation showing long-term planning, side effects, and delays

Scenario: A survival RPG agent must neutralise a guarded enemy camp.
The agent must scout, gather resources, craft equipment, and fight — all
while managing health, stamina, and inventory constraints.
'''

import heapq
import time
import textwrap
from dataclasses import dataclass, field
from typing import Optional

# ============================================================
# STEP 1: WORLD STATE
# ============================================================

# World state is a frozenset of active boolean flags.
# A flag present in the set means it is TRUE.
# Absence of a flag means it is FALSE.
#
# Available flags:
#   agent_healthy         - agent has > 50% HP
#   agent_rested          - stamina is full
#   has_weapon            - agent carries a weapon
#   has_armor             - agent wears armor
#   has_food              - agent has food in inventory
#   has_medkit            - agent has a medkit
#   has_materials         - raw crafting materials collected
#   camp_scouted          - agent has intel on the enemy camp
#   enemy_weakened        - enemy has been hit or debuffed
#   enemy_distracted      - enemy is looking away
#   ally_nearby           - a friendly NPC is present
#   at_camp               - agent is at the enemy camp location
#   at_town               - agent is in town (safe zone)
#   at_forest             - agent is in the forest
#   enemy_defeated        - final objective achieved

INITIAL_STATE: frozenset = frozenset({
    'at_town',
    'agent_healthy',
    'agent_rested',
})

GOAL_STATE: frozenset = frozenset({
    'enemy_defeated',
})


# ============================================================
# STEP 2: ACTION SPACE
# ============================================================

@dataclass
class Action:
    '''An action the agent can perform.

    Attributes:
        name:          Human-readable label.
        preconditions: Flags that MUST be true for this action to be valid.
        add_effects:   Flags set to TRUE after execution.
        del_effects:   Flags set to FALSE after execution.
        cost:          Planning cost (lower = preferred).
        duration:      Simulated time delay in seconds (shown during sim).
        description:   Narrative text displayed during simulation.
    '''
    name: str
    preconditions: frozenset
    add_effects: frozenset
    del_effects: frozenset
    cost: float
    duration: float        # seconds (scaled down for simulation)
    description: str = ''

    def is_applicable(self, state: frozenset) -> bool:
        return self.preconditions.issubset(state)

    def apply(self, state: frozenset) -> frozenset:
        return (state | self.add_effects) - self.del_effects


# Define all available actions
ACTIONS: list[Action] = [

    # ── Logistics ────────────────────────────────────────────
    Action(
        name='Travel to Forest',
        preconditions=frozenset({'at_town'}),
        add_effects=frozenset({'at_forest'}),
        del_effects=frozenset({'at_town'}),
        cost=1.0, duration=1.5,
        description='The agent sets out from town, following the old trail into the forest.'
    ),
    Action(
        name='Travel to Camp',
        preconditions=frozenset({'at_forest', 'camp_scouted'}),
        add_effects=frozenset({'at_camp'}),
        del_effects=frozenset({'at_forest'}),
        cost=1.0, duration=1.5,
        description='With the scouting intel in hand, the agent moves silently toward the enemy camp.'
    ),
    Action(
        name='Return to Town',
        preconditions=frozenset({'at_forest'}),
        add_effects=frozenset({'at_town'}),
        del_effects=frozenset({'at_forest'}),
        cost=1.0, duration=1.5,
        description='The agent retreats to town to resupply.'
    ),

    # ── Scouting ─────────────────────────────────────────────
    Action(
        name='Scout Enemy Camp',
        preconditions=frozenset({'at_forest', 'agent_rested'}),
        add_effects=frozenset({'camp_scouted', 'enemy_weakened'}),   # side effect: spotted a weakness
        del_effects=frozenset({'agent_rested'}),                     # side effect: costs stamina
        cost=2.0, duration=2.0,
        description='The agent spends time observing the camp, mapping patrol routes and spotting a gap in the defences.'
    ),

    # ── Resource gathering ───────────────────────────────────
    Action(
        name='Gather Materials',
        preconditions=frozenset({'at_forest'}),
        add_effects=frozenset({'has_materials'}),
        del_effects=frozenset(),
        cost=1.5, duration=1.5,
        description='The agent collects wood, herbs, and scrap metal from the forest floor.'
    ),
    Action(
        name='Forage Food',
        preconditions=frozenset({'at_forest'}),
        add_effects=frozenset({'has_food'}),
        del_effects=frozenset(),
        cost=1.0, duration=1.0,
        description='Berries and mushrooms are gathered. Not gourmet, but enough to keep going.'
    ),
    Action(
        name='Buy Medkit',
        preconditions=frozenset({'at_town'}),
        add_effects=frozenset({'has_medkit'}),
        del_effects=frozenset(),
        cost=2.0, duration=0.5,
        description='The agent purchases a medkit from the town apothecary.'
    ),

    # ── Crafting ─────────────────────────────────────────────
    Action(
        name='Craft Weapon',
        preconditions=frozenset({'has_materials', 'at_town'}),
        add_effects=frozenset({'has_weapon'}),
        del_effects=frozenset({'has_materials'}),
        cost=2.0, duration=2.0,
        description='At the blacksmith, the agent forges a sturdy blade from the raw materials.'
    ),
    Action(
        name='Craft Armor',
        preconditions=frozenset({'has_materials', 'at_town'}),
        add_effects=frozenset({'has_armor'}),
        del_effects=frozenset({'has_materials'}),
        cost=2.5, duration=2.5,
        description='Leather and metal are stitched together into a serviceable set of armor.'
    ),

    # ── Rest & Recovery ──────────────────────────────────────
    Action(
        name='Rest at Inn',
        preconditions=frozenset({'at_town'}),
        add_effects=frozenset({'agent_rested', 'agent_healthy'}),
        del_effects=frozenset(),
        cost=1.5, duration=1.0,
        description='A hot meal and a night\'s sleep at the inn restores health and stamina.'
    ),
    Action(
        name='Eat Food',
        preconditions=frozenset({'has_food'}),
        add_effects=frozenset({'agent_rested'}),
        del_effects=frozenset({'has_food'}),
        cost=0.5, duration=0.3,
        description='The agent eats the foraged food, recovering some stamina.'
    ),
    Action(
        name='Use Medkit',
        preconditions=frozenset({'has_medkit'}),
        add_effects=frozenset({'agent_healthy'}),
        del_effects=frozenset({'has_medkit'}),
        cost=0.5, duration=0.3,
        description='The medkit is applied. Wounds are bound; health is restored.'
    ),

    # ── Distraction ──────────────────────────────────────────
    Action(
        name='Create Diversion',
        preconditions=frozenset({'at_camp', 'has_materials'}),
        add_effects=frozenset({'enemy_distracted'}),
        del_effects=frozenset({'has_materials'}),
        cost=1.5, duration=1.0,
        description='The agent tosses a makeshift noisemaker. The guards spin around, distracted.'
    ),

    # ── Combat ───────────────────────────────────────────────
    Action(
        name='Ambush Enemy',
        preconditions=frozenset({'at_camp', 'has_weapon', 'enemy_distracted', 'agent_healthy'}),
        add_effects=frozenset({'enemy_defeated'}),
        del_effects=frozenset({'has_weapon'}),
        cost=3.0, duration=2.0,
        description='The agent strikes from the shadows while the enemy is distracted. A clean takedown.'
    ),
    Action(
        name='Direct Assault',
        preconditions=frozenset({'at_camp', 'has_weapon', 'has_armor', 'enemy_weakened', 'agent_healthy'}),
        add_effects=frozenset({'enemy_defeated'}),
        del_effects=frozenset({'has_weapon', 'has_armor', 'agent_healthy'}),  # costly side effects
        cost=5.0, duration=3.0,
        description='No clever tricks — just raw aggression. The agent charges in, taking hits but winning the fight.'
    ),
    Action(
        name='Call for Aid',
        preconditions=frozenset({'at_camp', 'ally_nearby'}),
        add_effects=frozenset({'enemy_defeated'}),
        del_effects=frozenset(),
        cost=1.0, duration=1.0,
        description='The agent signals their ally. Together, the enemy stands no chance.'
    ),
]


# ============================================================
# STEP 3: A* PLANNER
# ============================================================

@dataclass(order=True)
class PlanNode:
    '''A node in the A* search graph.'''
    f_score: float
    g_score: float = field(compare=False)
    state: frozenset = field(compare=False)
    actions_taken: list = field(compare=False)
    parent: Optional['PlanNode'] = field(default=None, compare=False)


def heuristic(state: frozenset, goal: frozenset) -> float:
    '''Admissible heuristic: number of unsatisfied goal conditions.
    Each unmet condition costs at least 1 action to satisfy.
    '''
    return len(goal - state)


def plan(initial_state: frozenset, goal_state: frozenset,
         actions: list[Action]) -> Optional[list[Action]]:
    '''
    A* forward search planner.

    Searches the action space to find the lowest-cost sequence of actions
    that transitions from initial_state to a state satisfying all goal
    conditions.

    Returns:
        Ordered list of Action objects forming the plan, or None if no
        plan exists.
    '''
    start_h = heuristic(initial_state, goal_state)
    start_node = PlanNode(
        f_score=start_h,
        g_score=0.0,
        state=initial_state,
        actions_taken=[],
    )

    open_set: list[PlanNode] = []
    heapq.heappush(open_set, start_node)

    # visited: maps state → best g_score seen so far
    visited: dict[frozenset, float] = {}

    nodes_expanded = 0

    while open_set:
        current = heapq.heappop(open_set)
        nodes_expanded += 1

        # Goal check: does current state satisfy ALL goal conditions?
        if goal_state.issubset(current.state):
            print(f'  [Planner] Solution found! Nodes expanded: {nodes_expanded}')
            return current.actions_taken

        # Skip if we've reached this state cheaper before
        if current.state in visited and visited[current.state] <= current.g_score:
            continue
        visited[current.state] = current.g_score

        # Expand applicable actions
        for action in actions:
            if action.is_applicable(current.state):
                new_state = action.apply(current.state)
                new_g = current.g_score + action.cost
                new_h = heuristic(new_state, goal_state)
                new_f = new_g + new_h

                # Prune: don't revisit states with worse cost
                if new_state in visited and visited[new_state] <= new_g:
                    continue

                child = PlanNode(
                    f_score=new_f,
                    g_score=new_g,
                    state=new_state,
                    actions_taken=current.actions_taken + [action],
                )
                heapq.heappush(open_set, child)

    print(f'  [Planner] No plan found. Nodes expanded: {nodes_expanded}')
    return None


# ============================================================
# STEP 4: SIMULATION
# ============================================================

DELAY_SCALE = 0.4   # multiply all durations by this for simulation speed

def print_header(text: str, char: str = '=', width: int = 62):
    print('\n' + char * width)
    print(f'  {text}')
    print(char * width)

def print_state(state: frozenset, label: str = 'World State'):
    print(f'\n  [{label}]')
    sorted_flags = sorted(state)
    for flag in sorted_flags:
        print(f'    ✓  {flag}')

def print_plan(plan_actions: list[Action]):
    print_header('GENERATED PLAN', '-')
    total_cost = sum(a.cost for a in plan_actions)
    total_time = sum(a.duration for a in plan_actions)
    print(f'  Steps: {len(plan_actions)}  |  Total cost: {total_cost:.1f}  |  Est. duration: {total_time:.1f}s\n')
    for i, action in enumerate(plan_actions, 1):
        print(f'  Step {i:>2}: [{action.name}]')
        print(f'          Cost={action.cost:.1f}  Duration={action.duration:.1f}s')
        print(f'          Requires: {", ".join(sorted(action.preconditions)) or "—"}')
        add = sorted(action.add_effects)
        rem = sorted(action.del_effects)
        if add: print(f'          Adds:     {", ".join(add)}')
        if rem: print(f'          Removes:  {", ".join(rem)}')

def run_simulation(initial: frozenset, goal: frozenset,
                   actions: list[Action], delay_scale: float = DELAY_SCALE):

    print_header('GOAP SIMULATION — ENEMY CAMP ASSAULT')

    print('\n  SCENARIO')
    print('  ' + '-'*58)
    print(textwrap.fill(
        'An agent must infiltrate and neutralise a fortified enemy camp. '
        'They start in town with basic health and must scout, gather '
        'resources, craft gear, and choose the right moment to strike. '
        'The planner finds the optimal action sequence automatically.',
        width=60, initial_indent='  ', subsequent_indent='  '
    ))

    print_state(initial, 'Initial World State')
    print_state(goal, 'Goal State')

    # ── Planning phase ────────────────────────────────────────
    print_header('PLANNING', '-')
    print('  Running A* planner...')
    t0 = time.time()
    result = plan(initial, goal, actions)
    elapsed = time.time() - t0
    print(f'  [Planner] Planning time: {elapsed*1000:.1f}ms')

    if result is None:
        print('\n  !! No plan found. Check world state and action definitions.')
        return

    print_plan(result)

    # ── Execution phase ───────────────────────────────────────
    print_header('EXECUTING PLAN')
    print('  The agent begins carrying out the plan...\n')

    current_state = initial
    total_cost = 0.0

    for step, action in enumerate(result, 1):
        print(f'\n  ── Step {step}/{len(result)}: {action.name} ──')

        # Verify preconditions are still met (they should be if plan is valid)
        if not action.is_applicable(current_state):
            print('  !! ERROR: Preconditions no longer met — plan invalidated!')
            print(f'     Missing: {action.preconditions - current_state}')
            break

        # Narrative description
        if action.description:
            print('  ' + textwrap.fill(action.description, width=58,
                                        subsequent_indent='  '))

        # Show time delay
        print(f'\n  ⏱  Duration: {action.duration:.1f}s  |  Cost: {action.cost:.1f}')
        time.sleep(action.duration * delay_scale)

        # Apply action
        prev_state = current_state
        current_state = action.apply(current_state)
        total_cost += action.cost

        # Show state changes
        added   = sorted(current_state - prev_state)
        removed = sorted(prev_state - current_state)
        if added:
            print(f'  + Added:   {", ".join(added)}')
        if removed:
            print(f'  - Removed: {", ".join(removed)}')

        # Check if goal already met mid-plan
        if goal.issubset(current_state):
            print(f'\n  ★  GOAL ACHIEVED at step {step}!')
            break

    # ── Summary ──────────────────────────────────────────────
    print_header('SIMULATION COMPLETE')
    goal_met = goal.issubset(current_state)
    if goal_met:
        print(f'  ✅ Objective achieved: enemy_defeated')
        print(f'  Total steps executed : {step}')
        print(f'  Total plan cost      : {total_cost:.1f}')
    else:
        print('  ❌ Objective NOT achieved.')

    print_state(current_state, 'Final World State')

    # ── Planning intelligence notes ───────────────────────────
    print_header('GOAP INTELLIGENCE NOTES', '-')
    print(textwrap.fill(
        'Long-term reasoning: The planner looked ahead multiple steps, '
        'knowing that scouting, gathering materials, and crafting were '
        'prerequisites — not just the final attack.',
        width=60, initial_indent='  ', subsequent_indent='  '))
    print()
    print(textwrap.fill(
        'Side effects: Scouting consumed stamina (agent_rested removed) '
        'and crafting consumed materials. The planner accounted for '
        'these deletions when sequencing subsequent actions.',
        width=60, initial_indent='  ', subsequent_indent='  '))
    print()
    print(textwrap.fill(
        'Time delays: Each action carries a real duration. The planner '
        'minimises total cost, balancing cheap-but-slow actions against '
        'expensive-but-fast alternatives.',
        width=60, initial_indent='  ', subsequent_indent='  '))
    print()
    print(textwrap.fill(
        'Action cost optimisation: A* selected Ambush over Direct Assault '
        '(cost 3.0 vs 5.0) because the distraction route was cheaper '
        'and avoided losing armor as a side effect.',
        width=60, initial_indent='  ', subsequent_indent='  '))
    print()


# ============================================================
# ALTERNATIVE SCENARIOS
# ============================================================

def demo_no_materials_scenario():
    '''Show the planner adapting when materials are unavailable — it chooses
    a different attack path.'''
    print_header('ALTERNATIVE SCENARIO: Agent Already Has Weapon + Armor')
    alt_state = frozenset({
        'at_town',
        'agent_healthy',
        'agent_rested',
        'has_weapon',
        'has_armor',
        'camp_scouted',
        'enemy_weakened',
    })
    print_state(alt_state, 'Alternative Initial State')
    print('\n  Running A* planner for alternative scenario...')
    result = plan(alt_state, GOAL_STATE, ACTIONS)
    if result:
        print_plan(result)
        total = sum(a.cost for a in result)
        print(f'\n  Total plan cost: {total:.1f}  (shorter plan — resources pre-acquired)')
    else:
        print('  No plan found.')


def demo_ally_scenario():
    '''Show the agent choosing the cheapest path — using an ally.'''
    print_header('ALTERNATIVE SCENARIO: Ally Available at Camp')
    alt_state = frozenset({
        'at_camp',
        'agent_healthy',
        'agent_rested',
        'ally_nearby',
    })
    print_state(alt_state, 'Alternative Initial State')
    print('\n  Running A* planner for ally scenario...')
    result = plan(alt_state, GOAL_STATE, ACTIONS)
    if result:
        print_plan(result)
        total = sum(a.cost for a in result)
        print(f'\n  Total plan cost: {total:.1f}  (ally path is cheapest!)')
    else:
        print('  No plan found.')


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == '__main__':
    # Main simulation
    run_simulation(INITIAL_STATE, GOAL_STATE, ACTIONS)

    # Alternative scenarios (planning only, no execution delay)
    print('\n\n')
    demo_no_materials_scenario()
    print('\n\n')
    demo_ally_scenario()
