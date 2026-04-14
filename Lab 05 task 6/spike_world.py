'''
spike_world.py  -  Task 6 Spike: Navigation with Graphs
COS30002 AI for Games

Extends the Task 5 BoxWorld with:
  - Larger 20x15 map (300 tiles vs Task 5's ~30)
  - 6 passable terrain types + wall + rock (8 total)
  - MultiAgentManager: spawns and updates 4+ agents simultaneously
  - Two agent types: SpeedAgent (fast, ignores cost) and CautiousAgent (slow, avoids expensive tiles)
  - Dynamic environment: press D to randomly toggle terrain, press G to change all agent targets
'''

from math import hypot
from spike_graphics import COLOUR_NAMES, window
import pyglet
import random
from point2d import Point2D
from graph import SparseGraph, Node, Edge
from searches import SearchAStar, SearchDijkstra

# ── TERRAIN DEFINITION (Step 2: 6+ terrain types) ────────────────────────────
# Each passable terrain has a cost dict: {dest_terrain: cost}
# WALL and ROCK have no cost dict → excluded from nav graph

spike_box_types = {
    # symbol  cost-to-reach-from-any-tile       colour
    "CLEAR":  {"symbol": '.', "colour": "WHITE",
               "cost": {"CLEAR":1, "MUD":2, "WATER":5, "FOREST":3, "SAND":2, "GRASS":1}},
    "MUD":    {"symbol": 'm', "colour": "BROWN",
               "cost": {"CLEAR":2, "MUD":4, "WATER":9, "FOREST":5, "SAND":3, "GRASS":2}},
    "WATER":  {"symbol": '~', "colour": "AQUA",
               "cost": {"CLEAR":5, "MUD":9, "WATER":10,"FOREST":8, "SAND":6, "GRASS":4}},
    "FOREST": {"symbol": 'f', "colour": "FOREST_GREEN",
               "cost": {"CLEAR":3, "MUD":5, "WATER":8, "FOREST":6, "SAND":4, "GRASS":2}},
    "SAND":   {"symbol": 's', "colour": "SAND_YELLOW",
               "cost": {"CLEAR":2, "MUD":3, "WATER":6, "FOREST":4, "SAND":3, "GRASS":2}},
    "GRASS":  {"symbol": 'g', "colour": "LIGHT_GREEN",
               "cost": {"CLEAR":1, "MUD":2, "WATER":4, "FOREST":2, "SAND":2, "GRASS":1}},
    # Impassable
    "WALL":   {"symbol": 'X', "colour": "GREY"},
    "ROCK":   {"symbol": 'r', "colour": "ROCK_GREY"},
}

# minimum passable edge cost (for A* heuristic admissibility)
SPIKE_MIN_COST = 1.0

# ── AGENT COLOURS ─────────────────────────────────────────────────────────────
AGENT_COLOURS = [
    "YELLOW", "RED", "LIGHT_BLUE", "LIGHT_GREEN",
    "ORANGE", "PINK", "PURPLE", "AQUA",
]

# ── BASE SPIKE AGENT ─────────────────────────────────────────────────────────
class SpikeAgent:
    '''
    Base agent class. Walks a pre-calculated path node-by-node.
    Subclasses override step_interval and plan() to get different behaviour.
    '''
    STEP_INTERVAL = 0.30   # seconds per step (overridden by subclasses)
    TYPE_LABEL    = "Base"

    def __init__(self, agent_id, colour_name, world):
        self.id       = agent_id
        self.colour   = colour_name
        self.world    = world
        self.path     = []
        self.step_idx = 0
        self.active   = False
        self.elapsed  = 0.0
        self.start_idx  = 0
        self.target_idx = 0

        cx, cy = -200 - agent_id * 30, -200
        self.marker = pyglet.shapes.Circle(
            cx, cy, radius=10,
            color=COLOUR_NAMES[colour_name],
            batch=window.get_batch("agents")
        )
        self.outline = pyglet.shapes.Arc(
            cx, cy, radius=10, segments=24,
            color=COLOUR_NAMES["BLACK"],
            batch=window.get_batch("agents"),
            thickness=2
        )
        # small label showing agent id and type
        self.label_shape = pyglet.text.Label(
            "%d" % agent_id,
            font_name='Arial', font_size=8,
            x=cx, y=cy,
            anchor_x='center', anchor_y='center',
            color=COLOUR_NAMES["BLACK"],
            batch=window.get_batch("agents")
        )

    def plan(self, start_idx, target_idx):
        '''Plan a path. Override in subclasses to change algorithm or graph.'''
        self.start_idx  = start_idx
        self.target_idx = target_idx
        result = SearchAStar(self.world.graph, start_idx, target_idx)
        self.path     = result.path
        self.step_idx = 0
        self.elapsed  = 0.0
        self.active   = len(self.path) > 1
        if self.active:
            self._move_to(0)
        else:
            print("Agent %d (%s): no path found %d->%d" % (self.id, self.TYPE_LABEL, start_idx, target_idx))

    def update(self, dt):
        if not self.active:
            return
        self.elapsed += dt
        if self.elapsed >= self.STEP_INTERVAL:
            self.elapsed = 0.0
            self.step_idx += 1
            if self.step_idx >= len(self.path):
                self.active = False
                self._hide()
                return
            self._move_to(self.step_idx)

    def _move_to(self, idx):
        box = self.world.boxes[self.path[idx]]
        cx, cy = box.center().x, box.center().y
        self.marker.x = cx;  self.marker.y = cy
        self.outline.x = cx; self.outline.y = cy
        self.label_shape.x = cx; self.label_shape.y = cy

    def _hide(self):
        self.marker.x = -200 - self.id * 30
        self.marker.y = -200
        self.outline.x = self.marker.x
        self.outline.y = self.marker.y
        self.label_shape.x = self.marker.x
        self.label_shape.y = self.marker.y

    def reset(self):
        self.active = False
        self.path = []
        self.step_idx = 0
        self._hide()


# ── AGENT TYPE 1: SpeedAgent ──────────────────────────────────────────────────
class SpeedAgent(SpikeAgent):
    '''
    Moves FAST (short step interval).
    Uses standard A* on the normal cost graph.
    Prefers the quickest path by time, not necessarily the cheapest by cost.
    '''
    STEP_INTERVAL = 0.15   # twice as fast as base
    TYPE_LABEL    = "Speed"


# ── AGENT TYPE 2: CautiousAgent ───────────────────────────────────────────────
class CautiousAgent(SpikeAgent):
    '''
    Moves SLOWLY and plans on a modified graph where water and mud costs
    are multiplied by an avoidance factor, so it strongly prefers clear/grass.
    Demonstrates different agent behaviour using the same search algorithm.
    '''
    STEP_INTERVAL = 0.45   # slower
    TYPE_LABEL    = "Caution"
    AVOID_FACTOR  = 3      # multiply expensive terrain costs

    def plan(self, start_idx, target_idx):
        self.start_idx  = start_idx
        self.target_idx = target_idx
        # Build a temporary cautious graph with inflated costs for bad terrain
        cautious_graph = self._build_cautious_graph()
        result = SearchAStar(cautious_graph, start_idx, target_idx)
        self.path     = result.path
        self.step_idx = 0
        self.elapsed  = 0.0
        self.active   = len(self.path) > 1
        if self.active:
            self._move_to(0)
        else:
            print("CautiousAgent %d: no path found %d->%d" % (self.id, start_idx, target_idx))

    def _build_cautious_graph(self):
        '''Return a copy of the world graph with inflated water/mud costs.'''
        g = SparseGraph()
        g.cost_h = self.world.graph.cost_h
        # copy nodes
        for idx, node in self.world.graph.nodes.items():
            g.add_node(Node(idx=idx))
        # copy edges with inflation for expensive terrain
        avoid = {"WATER", "MUD"}
        boxes = self.world.boxes
        for from_idx, targets in self.world.graph.edgelist.items():
            for to_idx, edge in targets.items():
                cost = edge.cost
                if boxes[to_idx].type in avoid:
                    cost *= self.AVOID_FACTOR
                g.edgelist[from_idx][to_idx] = Edge(from_idx, to_idx, cost)
        return g


# ── MULTI-AGENT MANAGER ───────────────────────────────────────────────────────
class MultiAgentManager:
    '''
    Manages 4+ agents with different start/target pairs and types.
    Step 5: multiple independent agents
    Step 6: two agent types (SpeedAgent, CautiousAgent)
    Step 7: dynamic - call shuffle_targets() or toggle_terrain() at runtime
    '''

    # Predefined agent configs: (start_idx, target_idx, type, colour)
    # For a 20-wide 15-tall map (indices 0-299)
    CONFIGS = [
        # SpeedAgents  (fast, standard A*)
        (0,   299, SpeedAgent,    "YELLOW"),
        (19,  280, SpeedAgent,    "RED"),
        # CautiousAgents (slow, inflated cost for water/mud)
        (20,  279, CautiousAgent, "LIGHT_BLUE"),
        (40,  259, CautiousAgent, "ORANGE"),
        # More SpeedAgents
        (1,   298, SpeedAgent,    "PINK"),
        (38,  261, CautiousAgent, "LIGHT_GREEN"),
    ]

    def __init__(self, world):
        self.world  = world
        self.agents = []
        for i, (s, t, cls, col) in enumerate(self.CONFIGS):
            agent = cls(i, col, world)
            # clamp to valid non-wall tiles
            s = self._nearest_passable(s)
            t = self._nearest_passable(t)
            agent.plan(s, t)
            self.agents.append(agent)
        print("MultiAgentManager: %d agents spawned (%d Speed, %d Cautious)" % (
            len(self.agents),
            sum(1 for a in self.agents if isinstance(a, SpeedAgent)),
            sum(1 for a in self.agents if isinstance(a, CautiousAgent)),
        ))

    def _nearest_passable(self, idx):
        '''If idx is a wall/rock, find the nearest passable tile.'''
        if "cost" in spike_box_types.get(self.world.boxes[idx].type, {}):
            return idx
        for delta in range(1, 20):
            for d in [delta, -delta]:
                ni = idx + d
                if 0 <= ni < len(self.world.boxes):
                    if "cost" in spike_box_types.get(self.world.boxes[ni].type, {}):
                        return ni
        return idx

    def update(self, dt):
        for agent in self.agents:
            agent.update(dt)

    def start_all(self):
        '''Re-plan and restart all agents from their current start/target.'''
        for agent in self.agents:
            s = self._nearest_passable(agent.start_idx)
            t = self._nearest_passable(agent.target_idx)
            agent.plan(s, t)

    def reset_all(self):
        for agent in self.agents:
            agent.reset()

    def shuffle_targets(self):
        '''
        Step 7 - Dynamic: randomise each agent's target to a random passable tile.
        Demonstrates path recalculation when targets change.
        '''
        passable = [i for i, b in enumerate(self.world.boxes)
                    if "cost" in spike_box_types.get(b.type, {})]
        for agent in self.agents:
            new_target = random.choice(passable)
            agent.target_idx = new_target
            s = self._nearest_passable(agent.start_idx)
            agent.plan(s, new_target)
        print("MultiAgentManager: targets shuffled, all agents replanned.")

    @property
    def all_done(self):
        return all(not a.active for a in self.agents)


# ── SPIKE BOX (tile that knows spike_box_types) ───────────────────────────────
class SpikeBox:
    def __init__(self, index, x, y, width, height, symbol='.'):
        self.index  = index
        self.x, self.y = x, y
        self.width, self.height = width, height
        self.type = "CLEAR"
        for k, v in spike_box_types.items():
            if v["symbol"] == symbol:
                self.type = k
                break
        self.node = None
        self.box = pyglet.shapes.BorderedRectangle(
            x, y, width, height, border=1,
            color=COLOUR_NAMES[spike_box_types[self.type]["colour"]],
            border_color=COLOUR_NAMES["LIGHT_GREY"],
            batch=window.get_batch()
        )

    def set_type(self, type_name):
        if type_name in spike_box_types:
            self.type = type_name
            self.box.color = COLOUR_NAMES[spike_box_types[self.type]["colour"]]
        else:
            for k, v in spike_box_types.items():
                if v["symbol"] == type_name:
                    self.type = k
                    self.box.color = COLOUR_NAMES[spike_box_types[k]["colour"]]
                    return
            print("SpikeBox: unknown type '%s'" % type_name)

    def center(self):
        return Point2D(self.x + self.width // 2, self.y + self.height // 2)

    @property
    def pos(self):
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value


# ── SPIKE WORLD ───────────────────────────────────────────────────────────────
class SpikeWorld:
    '''
    Step 1: Larger navigation grid.
    Loads from a text file, builds a SparseGraph, manages MultiAgentManager.
    '''

    def __init__(self, nx, ny, window_width, window_height):
        self.x_boxes = nx
        self.y_boxes = ny
        bw = window_width  // nx
        bh = window_height // ny
        self.wx = (window_width  - 1) // nx
        self.wy = (window_height - 1) // ny

        self.boxes = []
        for i in range(nx * ny):
            self.boxes.append(SpikeBox(i, (i % nx) * bw, (i // nx % ny) * bh, bw, bh))

        self.graph   = None
        self.manager = None
        self._build_graph()

    # ── graph ──────────────────────────────────────────────────────────────
    def _manhattan(self, idx1, idx2):
        x1, y1 = self.boxes[idx1].pos
        x2, y2 = self.boxes[idx2].pos
        return (abs(x1 - x2) + abs(y1 - y2)) * SPIKE_MIN_COST

    def _add_edge(self, fi, ti, dist=1.0):
        bt = spike_box_types
        fb = self.boxes[fi].type
        tb = self.boxes[ti].type
        if "cost" in bt[fb] and tb in bt[fb]["cost"]:
            cost = bt[fb]["cost"][tb] * dist
            self.graph.add_edge(Edge(fi, ti, cost))

    def _build_graph(self):
        self.graph = SparseGraph()
        self.graph.cost_h = self._manhattan
        nx = self.x_boxes
        for i, box in enumerate(self.boxes):
            box.pos = (i % nx, i // nx)
            box.node = self.graph.add_node(Node(idx=i))
        for i, box in enumerate(self.boxes):
            if "cost" not in spike_box_types.get(box.type, {}):
                continue
            if (i + nx) < len(self.boxes): self._add_edge(i, i + nx)
            if (i - nx) >= 0:              self._add_edge(i, i - nx)
            if (i % nx + 1) < nx:         self._add_edge(i, i + 1)
            if (i % nx - 1) >= 0:         self._add_edge(i, i - 1)

    def rebuild_graph_and_replan(self):
        '''Step 7: rebuilds graph after terrain change, replans all agents.'''
        self._build_graph()
        if self.manager:
            self.manager.world = self  # update reference
            self.manager.start_all()

    def spawn_agents(self):
        '''Create the MultiAgentManager after the world is fully built.'''
        self.manager = MultiAgentManager(self)

    def update(self, dt):
        if self.manager:
            self.manager.update(dt)

    def toggle_random_terrain(self):
        '''
        Step 7 - Dynamic environment: randomly flip 5 random passable tiles
        to a different passable terrain and rebuild the nav graph.
        '''
        passable_keys = [k for k, v in spike_box_types.items() if "cost" in v and k != "WALL"]
        candidates = [b for b in self.boxes if "cost" in spike_box_types.get(b.type, {})]
        for box in random.sample(candidates, min(5, len(candidates))):
            new_type = random.choice([k for k in passable_keys if k != box.type])
            box.set_type(new_type)
        self.rebuild_graph_and_replan()
        print("SpikeWorld: random terrain toggled, graph rebuilt, agents replanned.")

    def get_box_by_pos(self, x, y):
        idx = int((self.x_boxes * (y // self.wy)) + (x // self.wx))
        return self.boxes[idx] if 0 <= idx < len(self.boxes) else None

    @classmethod
    def FromFile(cls, filename):
        with open(filename) as f:
            lines = [l.strip() for l in f if l.strip() and not l.strip().startswith('#')]
        nx, ny   = [int(x) for x in lines.pop(0).split()]
        world    = cls(nx, ny, window.width, window.height)
        _s, _t   = lines.pop(0).split()   # start/target in file (unused for multi-agent)
        assert len(lines) == ny, "Row count mismatch in map file."
        idx = 0
        for line in reversed(lines):
            bits = line.split()
            assert len(bits) == nx, "Column count mismatch in map file."
            for sym in bits:
                world.boxes[idx].set_type(sym.strip())
                idx += 1
        world._build_graph()
        return world
