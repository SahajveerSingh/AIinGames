# Goal Oriented Behaviour & Action Planning — COS30002 AI for Games

A collection of Python scripts demonstrating SGI (Simple Goal Insistence) and GOAP (Goal Oriented Action Planning).

---

## Files

| File | Description |
|------|-------------|
| `gob_simple.py` | ✅ Step 1 — Working SGI implementation |
| `gob_sgi_fail.py` | ❌ Step 2 — SGI failure demonstration |
| `gob_oop.py` | 🔷 Extension — Object-oriented SGI refactor |
| `gob_rpg_combat.py` | ⚔️ Extension — Turn-based RPG combat using SGI |
| `goap.py` | 🧠 **GOAP** — Full A* planning system with simulation |
| `goap_design_report.pdf` | 📄 Design report with action graph |

---

## Requirements

- Python 3.10 or later
- No external libraries required for `.py` scripts

---

## SGI Scripts (Lab 1)

### Step 1 — Working SGI
```bash
python gob_simple.py
```
**Expected:** Agent starts with `Eat=4`, `Sleep=3`. SGI picks highest-insistence goal each turn. All goals reach 0 in 3 turns.

### Step 2 — SGI Failure
```bash
python gob_sgi_fail.py
```
**Expected:** Oscillation detected within 6 steps. `Critical=10` goal permanently ignored.

### Extension — OOP Refactor
```bash
python gob_oop.py
```
**Expected:** Two independent agents run using shared `Goal`, `Action`, `Agent` classes.

### Extension — RPG Combat
```bash
python gob_rpg_combat.py
```
**Expected:** Knight vs Mage combat. Knight wins by turn ~4.

---

## GOAP System — Lab 2

### How to Run
```bash
python goap.py
```
No dependencies. Python 3.10+ required.

### What to Expect

Three scenarios run in sequence:

**Scenario 1 — Main (from scratch):**
- A* planner generates 10-step plan in ~2ms
- Agent: travel → gather → craft weapon → gather again → scout → travel to camp → diversion → ambush
- Total cost: 15.5. Goal achieved at step 10.

**Scenario 2 — Pre-armed agent:**
- 3-step plan (cost 7.0): travel forest → travel camp → direct assault
- Shows planner adapts to different initial states automatically.

**Scenario 3 — Ally present:**
- 1-step plan (cost 1.0): call for aid
- Demonstrates A* always finds the cheapest complete path.

### Architecture

| Component | Implementation |
|-----------|---------------|
| World State | `frozenset` of boolean string flags |
| Actions | `Action` dataclass — preconditions, add/del effects, cost, duration |
| Planner | A* forward search, heuristic = unsatisfied goal count |
| Simulation | Step-through loop with narrative + real time delays |

### GOAP vs SGI

| Property | SGI | GOAP |
|----------|-----|------|
| Planning horizon | 1 step | N steps ahead |
| Side effect handling | No | Yes (del_effects) |
| Cost optimisation | No | Yes (A*) |
| Oscillation risk | High | None |
| Unsatisfiable goals | Silently ignored | Planner reports failure |

---

## Design Report

`goap_design_report.pdf` contains system architecture, action table, A* pseudocode, algorithm comparison, and the action dependency graph.
