'''Goal Oriented Behaviour - Object-Oriented Refactor (Extension)

Refactors the SGI system into classes: Goal, Action, and Agent.

Advantages for game developers/designers:
  - Encapsulation: Each agent owns its own goals/actions/state.
  - Multiple agents: Easily instantiate many NPCs with different configurations.
  - Extensibility: Subclass Agent to create specialist behaviours.
  - Readability: Code maps directly to game design concepts.

Disadvantages:
  - More boilerplate for simple scenarios.
  - Slightly higher memory overhead per agent.

Works with Python 3+
'''

VERBOSE = True


class Goal:
    '''Represents a single drive or need for an agent.'''

    def __init__(self, name: str, value: float):
        self.name = name
        self.value = value

    def apply_change(self, delta: float):
        '''Apply a delta, clamped to a minimum of 0.'''
        self.value = max(self.value + delta, 0)

    def __repr__(self):
        return f'Goal({self.name}={self.value:.1f})'


class Action:
    '''Represents a single action an agent can take, with goal effects.'''

    def __init__(self, name: str, effects: dict):
        '''
        Args:
            name: Human-readable action label.
            effects: Dict mapping goal names to delta values (negative = reduces goal).
        '''
        self.name = name
        self.effects = effects  # e.g. {'Eat': -3}

    def utility_for_goal(self, goal_name: str) -> float:
        '''Return the benefit this action provides towards a specific goal.
        Higher is better.
        '''
        if goal_name in self.effects:
            return -self.effects[goal_name]
        return 0.0

    def __repr__(self):
        return f'Action({self.name}: {self.effects})'


class Agent:
    '''An NPC agent that selects actions via Simple Goal Insistence (SGI).'''

    def __init__(self, name: str, goals: list[Goal], actions: list[Action]):
        self.name = name
        self.goals = {g.name: g for g in goals}
        self.actions = actions

    def most_insistent_goal(self) -> Goal:
        '''Return the goal with the highest current value.'''
        return max(self.goals.values(), key=lambda g: g.value)

    def choose_action(self) -> Action | None:
        '''SGI: pick the best action to satisfy the most insistent goal.'''
        best_goal = self.most_insistent_goal()

        if VERBOSE:
            print(f'  [{self.name}] BEST_GOAL: {best_goal.name} ({best_goal.value:.1f})')

        best_action = None
        best_utility = None

        for action in self.actions:
            utility = action.utility_for_goal(best_goal.name)
            if utility > 0:
                if best_utility is None or utility > best_utility:
                    best_action = action
                    best_utility = utility

        return best_action

    def apply_action(self, action: Action):
        '''Apply all effects of the given action to this agent's goals.'''
        for goal_name, delta in action.effects.items():
            if goal_name in self.goals:
                self.goals[goal_name].apply_change(delta)

    def all_goals_zero(self) -> bool:
        return all(g.value == 0 for g in self.goals.values())

    def print_goals(self):
        state = ', '.join(f'{n}={g.value:.1f}' for n, g in self.goals.items())
        print(f'  [{self.name}] GOALS: {state}')

    def __repr__(self):
        return f'Agent({self.name})'


def run_agent(agent: Agent):
    '''Run a single agent until all goals are zero.'''
    HR = '-' * 40
    print(f'\n=== Running Agent: {agent.name} ===')
    print('Actions:', [a.name for a in agent.actions])
    print('>> Start <<')
    print(HR)

    while not agent.all_goals_zero():
        agent.print_goals()
        action = agent.choose_action()
        if action is None:
            print(f'  [{agent.name}] No valid action found — stuck!')
            break
        print(f'  [{agent.name}] ACTION: {action.name}')
        agent.apply_action(action)
        agent.print_goals()
        print(HR)

    print(f'>> {agent.name} Done! <<')


if __name__ == '__main__':
    # --- Agent 1: The original scenario ---
    agent1 = Agent(
        name='Sleepy Harold',
        goals=[
            Goal('Eat', 4),
            Goal('Sleep', 3),
        ],
        actions=[
            Action('get raw food',  {'Eat':   -3}),
            Action('get snack',     {'Eat':   -2}),
            Action('sleep in bed',  {'Sleep': -4}),
            Action('sleep on sofa', {'Sleep': -2}),
        ]
    )
    run_agent(agent1)

    # --- Agent 2: Different personality, same action set ---
    agent2 = Agent(
        name='Famished Frida',
        goals=[
            Goal('Eat', 8),    # Very hungry
            Goal('Sleep', 1),  # Barely tired
        ],
        actions=[
            Action('get raw food',  {'Eat':   -3}),
            Action('get snack',     {'Eat':   -2}),
            Action('sleep in bed',  {'Sleep': -4}),
            Action('sleep on sofa', {'Sleep': -2}),
        ]
    )
    run_agent(agent2)

    print('\n--- OOP Advantages Demonstrated ---')
    print('* Two agents with different configs ran independently.')
    print('* Adding a new agent requires only a new Agent() instance.')
    print('* Goal and Action logic is reusable and encapsulated.')
