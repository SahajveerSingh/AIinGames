# Goal Oriented Behaviour (GOB) — COS30002 AI for Games

A collection of Python scripts demonstrating **Simple Goal Insistence (SGI)** — a lightweight AI decision-making technique used in games.

---

## Files

| File | Description |
|------|-------------|
| `gob_simple.py` | ✅ Step 1 — Working SGI implementation |
| `gob_sgi_fail.py` | ❌ Step 2 — SGI failure demonstration (oscillation + ignored goals) |
| `gob_oop.py` | 🔷 Extension — Object-oriented refactor of SGI |
| `gob_rpg_combat.py` | ⚔️ Extension — Turn-based RPG combat using SGI |

---

## Requirements

- Python 3.10 or later (uses `list[Goal]` and `Action | None` type hints in `gob_oop.py`)
- No external libraries required

---

## Step 1 — Working SGI (`gob_simple.py`)

### How to Run

```bash
python gob_simple.py
```

### What to Expect

The agent starts with two goals: `Eat=4` and `Sleep=3`.

SGI selects the most insistent goal each turn and picks the action with the highest utility for it. The agent correctly eats first (highest need), then sleeps, converging to all goals = 0.

**Expected output (abbreviated):**

```
ACTIONS:
 * [get raw food]: {'Eat': -3}
 * [get snack]: {'Eat': -2}
 * [sleep in bed]: {'Sleep': -4}
 * [sleep on sofa]: {'Sleep': -2}
>> Start <<
----------------------------------------
GOALS: {'Eat': 4, 'Sleep': 3}
BEST_GOAL: Eat 4
BEST ACTION: get raw food
NEW GOALS: {'Eat': 1, 'Sleep': 3}
...
GOALS: {'Eat': 0, 'Sleep': 0}
>> Done! <<
```

SGI works correctly here because:
- Goals have distinct values (no persistent ties)
- Actions fully or sufficiently resolve their target goal
- No conflicting side effects

---

## Step 2 — SGI Failure (`gob_sgi_fail.py`)

### How to Run

```bash
python gob_sgi_fail.py
```

### What to Expect

The agent demonstrates **two failure modes**:

#### Failure 1: Oscillation
`Hunger` and `Thirst` both start at `5`. Each action only partially reduces its target goal (`-2`) but adds a side effect that increases the other goal (`+1`). The agent endlessly alternates between eating and drinking.

#### Failure 2: Ignored Critical Goal
A `Critical` goal starts at `10` — the highest value — but no action in the environment can address it. SGI skips it (it finds no action) and falls back to the next-most-insistent goal, silently ignoring the crisis.

**Expected output (abbreviated):**

```
ACTIONS (with side effects):
  * [eat small snack]: primary={'Hunger': -2}  side_effects={'Thirst': 1}
  * [drink small sip]: primary={'Thirst': -2}  side_effects={'Hunger': 1}

NOTE: "Critical" goal has NO matching action — SGI will ignore it!
NOTE: Symmetric goals + side effects will cause oscillation.
...
*** OSCILLATION DETECTED! ***
    Agent is stuck alternating: [eat small snack] <-> [drink small sip]
    "Critical" goal (value=10) is being permanently ignored.
    SGI has FAILED to find a stable solution.
```

---

## Extension — Object-Oriented Refactor (`gob_oop.py`)

### How to Run

```bash
python gob_oop.py
```

### What to Expect

Two independently configured agents (`Sleepy Harold` and `Famished Frida`) run sequentially, each using the same `Goal`, `Action`, and `Agent` classes but with different parameters. Both resolve their goals correctly.

### OOP Advantages

| Advantage | Detail |
|-----------|--------|
| **Encapsulation** | Each agent's goals and state are self-contained — no shared globals |
| **Multiple agents** | Instantiate as many NPCs as needed with one line of code |
| **Extensibility** | Subclass `Agent` to create specialised behaviours (e.g. `AggressiveAgent`) |
| **Readability** | Code maps directly to game design vocabulary (`Goal`, `Action`, `Agent`) |
| **Testability** | Individual classes can be unit-tested in isolation |

### OOP Disadvantages

| Disadvantage | Detail |
|--------------|--------|
| **Boilerplate** | More code for simple single-agent scenarios |
| **Memory overhead** | Each agent instance allocates its own goal/action objects |
| **Indirection** | Behaviour spread across multiple files/classes can be harder to trace |

---

## Extension — RPG Combat (`gob_rpg_combat.py`)

### How to Run

```bash
python gob_rpg_combat.py
```

### What to Expect

A **Knight** (high HP, low MP) and a **Mage** (low HP, high MP) fight until one is defeated. Each NPC uses SGI to select combat actions every turn based on three dynamically computed goals:

- **Survive** — increases as HP falls; triggers healing actions
- **Kill Enemy** — based on enemy's remaining HP; triggers damaging actions
- **Save MP** — increases as MP falls; triggers MP recovery actions

**Expected output (abbreviated):**

```
============================================================
        ⚔  RPG COMBAT SIMULATION  ⚔
============================================================
    Knight | HP:  40/40 | MP:  10/10
      Mage | HP:  25/25 | MP:  30/30
============================================================

  TURN 1
------------------------------------------------------------
  Knight's turn:
         Goals: [Survive=0, Kill Enemy=25, Save MP=0]
         Most insistent goal: Kill Enemy (25)
  → Action: Sword Strike
  ...
  🏆  WINNER: Knight!
```

---

## Algorithm Summary — Simple Goal Insistence (SGI)

```
1. Evaluate all goals → pick the one with the highest "insistence" value
2. For each available action:
     - Compute utility = how much it reduces that goal's insistence
3. Select the action with the highest utility
4. Apply the action → update goal values
5. Repeat until all goals = 0 (or stopping condition met)
```

SGI is simple and fast but fails when:
- Goals are **tied** (no stable preference)
- Actions have **symmetric side effects** (causing oscillation)
- Critical goals have **no matching action** (silently ignored)
