'''Goal Oriented Behaviour - SGI FAILURE DEMONSTRATION

Demonstrates a situation where Simple Goal Insistence (SGI) fails.

FAILURE MODE: Oscillation
Two goals (Hunger, Thirst) are set to the same value and each action only
partially satisfies its goal. Because neither goal ever pulls clearly ahead,
the agent alternates between eating and drinking indefinitely — oscillating
and never resolving either need fully before the other surpasses it.

Additionally, a "Critical" goal starts very high but no action satisfies it
at all (misconfigured environment), so it is perpetually ignored because the
agent always picks the most insistent *actionable* goal. This shows SGI's
inability to handle unsatisfiable goals gracefully.

Works with Python 3+
'''

VERBOSE = True

MAX_STEPS = 20  # Safety cap to prevent true infinite loops

# Goals set to identical values — SGI cannot break the tie deterministically
goals = {
    'Hunger': 5,
    'Thirst': 5,
    'Critical': 10,   # Very high insistence but NO action can address it
}

# Actions are symmetric and only partially satisfy goals, causing oscillation.
# Notice: nothing touches 'Critical' at all.
actions = {
    'eat small snack':  { 'Hunger': -2 },   # Reduces Hunger by 2 only
    'drink small sip':  { 'Thirst': -2 },   # Reduces Thirst by 2 only
}

# Side effects: eating makes you thirstier; drinking makes you hungrier.
# This amplifies oscillation.
SIDE_EFFECTS = {
    'eat small snack': { 'Thirst': +1 },
    'drink small sip': { 'Hunger': +1 },
}


def apply_action(action):
    '''Apply action effects AND side effects to goals.'''
    # Primary effect
    for goal, change in actions[action].items():
        goals[goal] = max(goals[goal] + change, 0)
    # Side effects (make the oscillation worse)
    for goal, change in SIDE_EFFECTS[action].items():
        goals[goal] = max(goals[goal] + change, 0)


def action_utility(action, goal):
    '''Return utility of action for the given goal (ignoring side effects).'''
    if goal in actions[action]:
        return -actions[action][goal]
    return 0


def choose_action():
    '''SGI: pick action for the most insistent goal.'''
    assert len(goals) > 0, 'Need at least one goal'
    assert len(actions) > 0, 'Need at least one action'

    # Sort goals by insistence (highest first)
    sorted_goals = sorted(goals.items(), key=lambda item: item[1], reverse=True)

    for best_goal, best_goal_value in sorted_goals:
        if VERBOSE:
            print(f'  Trying goal: {best_goal} (value={best_goal_value})')

        best_action = None
        best_utility = None

        for key, value in actions.items():
            if best_goal in value:
                utility = action_utility(key, best_goal)
                if best_action is None or utility > best_utility:
                    best_action = key
                    best_utility = utility

        if best_action is not None:
            if VERBOSE:
                print(f'BEST_GOAL: {best_goal} ({best_goal_value})')
            return best_action

    # No action can address any goal — SGI is completely stuck
    return None


def print_actions():
    print('ACTIONS (with side effects):')
    for name, effects in actions.items():
        side = SIDE_EFFECTS.get(name, {})
        print(f'  * [{name}]: primary={effects}  side_effects={side}')


def run_simulation():
    HR = '-' * 50
    print_actions()
    print()
    print('NOTE: "Critical" goal has NO matching action — SGI will ignore it!')
    print('NOTE: Symmetric goals + side effects will cause oscillation.')
    print()
    print('>> Start <<')
    print(HR)

    action_history = []

    for step in range(MAX_STEPS):
        print(f'Step {step + 1}')
        print('GOALS:', goals)

        action = choose_action()

        if action is None:
            print('STUCK: No action can satisfy any goal! SGI has failed.')
            break

        print('BEST ACTION:', action)
        apply_action(action)
        print('NEW GOALS:', goals)

        # Detect oscillation: same two actions repeating
        action_history.append(action)
        if len(action_history) >= 6:
            last_6 = action_history[-6:]
            # Check if it's a repeating pair
            if last_6[0] == last_6[2] == last_6[4] and last_6[1] == last_6[3] == last_6[5]:
                print()
                print('*** OSCILLATION DETECTED! ***')
                print(f'    Agent is stuck alternating: [{last_6[0]}] <-> [{last_6[1]}]')
                print(f'    "Critical" goal (value={goals["Critical"]}) is being permanently ignored.')
                print(f'    SGI has FAILED to find a stable solution.')
                break

        if all(value == 0 for value in goals.values()):
            print('All goals zero — done.')
            break

        print(HR)

    else:
        print()
        print('*** MAX STEPS REACHED — SGI could not resolve goals! ***')

    print(HR)
    print('>> Simulation ended. SGI failure demonstrated. <<')
    print()
    print('WHY SGI FAILED HERE:')
    print('  1. Oscillation: Symmetric goals + side effects cause the agent to')
    print('     ping-pong between eating and drinking forever.')
    print('  2. Ignored critical need: The "Critical" goal has no available action,')
    print('     so SGI skips it and never flags it as a problem.')


if __name__ == '__main__':
    run_simulation()
