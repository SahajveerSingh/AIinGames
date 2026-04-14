game = None

from enum import Enum
import pyglet
from box_world import BoxWorld, Agent, search_modes
from graphics import window

# Mouse mode indicates what the mouse "click" should do...
class MouseModes(Enum):
		CLEAR  = pyglet.window.key._1
		MUD    = pyglet.window.key._2
		WATER  = pyglet.window.key._3
		WALL   = pyglet.window.key._4
		START  = pyglet.window.key._5
		TARGET = pyglet.window.key._6
		# ── NEW TERRAIN BRUSHES (Feature 2) ──────────────────────────
		FOREST = pyglet.window.key._7   # press 7 to paint Forest tiles
		SAND   = pyglet.window.key._8   # press 8 to paint Sand tiles

class SearchModes(Enum):
		DFS      = 1
		BFS      = 2
		Dijkstra = 3
		AStar    = 4

class Game():
	def __init__(self, map):
		self.world = BoxWorld.FromFile(map)
		# Mouse mode indicates what the mouse "click" should do...
		self.mouse_mode = MouseModes.MUD
		window._update_label('mouse', 'Click to place: '+self.mouse_mode.name)

		# search mode cycles through the search algorithm used by box_world
		self.search_mode = 1
		window._update_label('search', 'Search Type: '+SearchModes(self.search_mode).name)
		# search limit
		self.search_limit = 0 # unlimited.
		window._update_label('status', 'Status: Loaded')

		# ── AGENT (Feature 3) ─────────────────────────────────────────
		# Press A to launch the agent walk along the current path.
		# Press R to reset/hide the agent.
		self.agent = Agent()

	def plan_path(self):
		self.world.plan_path(self.search_mode, self.search_limit)
		# Reset agent whenever a new path is planned so it doesn't walk stale data
		self.agent.reset()
		window._update_label('status', 'Status: Path Planned (press A to walk)')

	def input_mouse(self, x, y, button, modifiers):
		box = self.world.get_box_by_pos(x,y)
		if box:
			if self.mouse_mode == MouseModes.START:
				self.world.set_start(box.node.idx)
			elif self.mouse_mode == MouseModes.TARGET:
				self.world.set_target(box.node.idx)
			else:
				box.set_type(self.mouse_mode.name)
			self.world.reset_navgraph()
			self.plan_path()
			window._update_label('status','Status: Graph Changed')

	def input_keyboard(self, symbol, modifiers):
		# mode change?
		if symbol in MouseModes:
			self.mouse_mode = MouseModes(symbol)
			window._update_label('mouse', 'Click to place: '+self.mouse_mode.name)

		# Change search mode? (Algorithm)
		elif symbol == pyglet.window.key.M:
			self.search_mode += 1
			if self.search_mode > len(search_modes):
				self.search_mode = 1
			self.world.plan_path(self.search_mode, self.search_limit)
			self.agent.reset()
			window._update_label('search', 'Search Type: '+SearchModes(self.search_mode).name)
		elif symbol == pyglet.window.key.N:
			self.search_mode -= 1
			if self.search_mode <= 0:
				self.search_mode = len(search_modes)
			self.world.plan_path(self.search_mode, self.search_limit)
			self.agent.reset()
			window._update_label('search', 'Search Type: '+SearchModes(self.search_mode).name)

		# Plan a path using the current search mode?
		elif symbol == pyglet.window.key.SPACE:
			self.world.plan_path(self.search_mode, self.search_limit)
			self.agent.reset()

		elif symbol == pyglet.window.key.UP:
			self.search_limit += 1
			window._update_label('status', 'Status: limit=%d' % self.search_limit)
			self.world.plan_path(self.search_mode, self.search_limit)
			self.agent.reset()
		elif symbol == pyglet.window.key.DOWN:
			if self.search_limit > 0:
				self.search_limit -= 1
				window._update_label('status', 'Status: limit=%d' % self.search_limit)
				self.world.plan_path(self.search_mode, self.search_limit)
				self.agent.reset()
		elif symbol == pyglet.window.key._0:
			self.search_limit = 0
			window._update_label('status', 'Status: limit=%d' % self.search_limit)
			self.world.plan_path(self.search_mode, self.search_limit)
			self.agent.reset()

		# ── AGENT CONTROLS (Feature 3) ────────────────────────────────
		# A  ->  start / restart the agent walking the current path
		elif symbol == pyglet.window.key.A:
			if self.world.path and self.world.path.path:
				self.agent.start(self.world.boxes, self.world.path.path)
				window._update_label('status', 'Status: Agent walking...')
			else:
				print("Agent: no path available. Run a search first (SPACE).")
				window._update_label('status', 'Status: No path to walk!')
		# R  ->  reset / hide the agent
		elif symbol == pyglet.window.key.R:
			self.agent.reset()
			window._update_label('status', 'Status: Agent reset')
