'''Goal Oriented Behaviour - RPG Combat Simulation (Extension)

A console-based, turn-based RPG where two NPCs fight each other.
Each NPC uses Simple Goal Insistence (SGI) to choose their combat action.

NPCs:
  - Knight: Tank fighter. Goals: Survive, Deal Damage, Conserve Mana.
  - Mage:   Spell caster. Goals: Survive, Deal Damage, Conserve Mana.

Each NPC's goals update each turn based on their current HP, MP, and
the enemy's HP. SGI selects the most urgent goal and the best action
to address it.

Works with Python 3+
'''

import time

VERBOSE = True
DELAY = 0.3   # seconds between turns (set to 0 for instant output)


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

class Combatant:
    def __init__(self, name, hp, max_hp, mp, max_mp, actions):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.mp = mp
        self.max_mp = max_mp
        self.actions = actions  # list of Action dicts

    @property
    def alive(self):
        return self.hp > 0

    def status(self):
        return (f'{self.name:>10} | HP: {self.hp:>3}/{self.max_hp}'
                f' | MP: {self.mp:>3}/{self.max_mp}')


# ---------------------------------------------------------------------------
# SGI helpers
# ---------------------------------------------------------------------------

def compute_goals(combatant: Combatant, enemy: Combatant) -> dict:
    '''
    Derive goal insistence values from the combatant's current state.

    Survive    — higher when HP is low (= max_hp - current_hp)
    Kill Enemy — higher when enemy HP is high (want to reduce it)
    Save MP    — higher when MP is low (want to preserve mana)
    '''
    survive    = combatant.max_hp - combatant.hp        # 0 when full HP, high when injured
    kill_enemy = enemy.hp                               # high when enemy has lots of HP left
    save_mp    = combatant.max_mp - combatant.mp        # 0 when full MP, high when drained

    return {
        'Survive':    survive,
        'Kill Enemy': kill_enemy,
        'Save MP':    save_mp,
    }


def action_utility(action: dict, goal: str) -> float:
    '''Return the positive utility of this action for the specified goal.'''
    return -action['effects'].get(goal, 0)


def choose_action(combatant: Combatant, enemy: Combatant):
    '''SGI: pick the action that best addresses the most insistent goal.'''
    goals = compute_goals(combatant, enemy)

    if VERBOSE:
        goal_str = ', '.join(f'{k}={v}' for k, v in goals.items())
        print(f'         Goals: [{goal_str}]')

    # Filter to only affordable actions (enough MP)
    affordable = [a for a in combatant.actions if combatant.mp >= a.get('mp_cost', 0)]

    if not affordable:
        # Fallback: rest (do nothing)
        print(f'         {combatant.name} has no MP! Forced to rest.')
        return None

    # Find the most pressing goal
    best_goal = max(goals, key=lambda g: goals[g])

    if VERBOSE:
        print(f'         Most insistent goal: {best_goal} ({goals[best_goal]})')

    # Find the best affordable action for that goal
    best_action = None
    best_util   = -1

    for action in affordable:
        util = action_utility(action, best_goal)
        if util > best_util:
            best_util   = util
            best_action = action

    # If no action helps this goal, just pick the highest-damage affordable action
    if best_action is None or best_util == 0:
        best_action = max(affordable, key=lambda a: action_utility(a, 'Kill Enemy'))

    return best_action


# ---------------------------------------------------------------------------
# Combat resolution
# ---------------------------------------------------------------------------

def apply_action(actor: Combatant, target: Combatant, action: dict):
    '''Apply an action's effects to actor and/or target.'''
    # MP cost to actor
    actor.mp = max(actor.mp - action.get('mp_cost', 0), 0)

    # Damage to target
    dmg = action['effects'].get('Kill Enemy', 0)   # stored as negative
    if dmg < 0:
        target.hp = max(target.hp + dmg, 0)        # dmg is negative, so this reduces HP

    # Healing to actor (Survive effect is positive = restore HP)
    heal = action['effects'].get('Survive', 0)
    if heal > 0:
        actor.hp = min(actor.hp + heal, actor.max_hp)

    # MP recovery (Save MP effect is positive = restore MP)
    mp_gain = action['effects'].get('Save MP', 0)
    if mp_gain > 0:
        actor.mp = min(actor.mp + mp_gain, actor.max_mp)


def run_combat(fighter_a: Combatant, fighter_b: Combatant):
    HR  = '=' * 60
    HR2 = '-' * 60

    print(HR)
    print('        ⚔  RPG COMBAT SIMULATION  ⚔')
    print(HR)
    print(f'{fighter_a.status()}')
    print(f'{fighter_b.status()}')
    print(HR)

    turn = 1
    while fighter_a.alive and fighter_b.alive:
        print(f'\n  TURN {turn}')
        print(HR2)

        for attacker, defender in [(fighter_a, fighter_b), (fighter_b, fighter_a)]:
            if not attacker.alive or not defender.alive:
                continue

            print(f'\n  {attacker.name}\'s turn:')
            action = choose_action(attacker, defender)

            if action is None:
                print(f'  {attacker.name} rests and recovers 2 MP.')
                attacker.mp = min(attacker.mp + 2, attacker.max_mp)
            else:
                print(f'  → Action: {action["name"]}')
                apply_action(attacker, defender, action)

            print(f'  {attacker.status()}')
            print(f'  {defender.status()}')

            if DELAY:
                time.sleep(DELAY)

        turn += 1
        if turn > 50:
            print('\n*** DRAW — combat exceeded 50 turns! ***')
            return

    print('\n' + HR)
    if fighter_a.alive:
        print(f'  🏆  WINNER: {fighter_a.name}!')
    elif fighter_b.alive:
        print(f'  🏆  WINNER: {fighter_b.name}!')
    else:
        print('  💀  Both combatants fell simultaneously — DRAW!')
    print(HR)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == '__main__':

    knight = Combatant(
        name='Knight',
        hp=40, max_hp=40,
        mp=10, max_mp=10,
        actions=[
            # name, mp_cost, effects on goals (negative = damages that goal insistence)
            {
                'name': 'Sword Strike',
                'mp_cost': 0,
                'effects': { 'Kill Enemy': -8 }    # deals 8 dmg to enemy HP
            },
            {
                'name': 'Shield Bash',
                'mp_cost': 2,
                'effects': { 'Kill Enemy': -5 }    # deals 5 dmg
            },
            {
                'name': 'Heal Self',
                'mp_cost': 4,
                'effects': { 'Survive': +10, 'Save MP': -4 }  # restores 10 HP, costs MP
            },
            {
                'name': 'War Cry',
                'mp_cost': 0,
                'effects': { 'Save MP': +3 }        # rests / regains 3 MP
            },
        ]
    )

    mage = Combatant(
        name='Mage',
        hp=25, max_hp=25,
        mp=30, max_mp=30,
        actions=[
            {
                'name': 'Fireball',
                'mp_cost': 6,
                'effects': { 'Kill Enemy': -12 }    # heavy damage
            },
            {
                'name': 'Magic Missile',
                'mp_cost': 2,
                'effects': { 'Kill Enemy': -5 }
            },
            {
                'name': 'Mana Shield',
                'mp_cost': 5,
                'effects': { 'Survive': +8, 'Save MP': -5 }
            },
            {
                'name': 'Meditate',
                'mp_cost': 0,
                'effects': { 'Save MP': +6 }        # recover 6 MP
            },
        ]
    )

    run_combat(knight, mage)
