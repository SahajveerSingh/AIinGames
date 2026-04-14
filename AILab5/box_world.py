''' Basic square grid based world (BoxWorld) to test/demo path planning.

Created for COS30002 AI for Games, Lab,
by Clinton Woodward <cwoodward@swin.edu.au>

For class use only. Do not publically share or post this code without
permission.

See readme.txt for details. Look for ### comment lines.

Note that the box world "boxes" (tiles) are created and assigned an index (idx)
value, starting from the origin in the bottom left corder. This matches the
convention of coordinates used by pyglet which uses OpenGL, rather than a
traditional 2D graphics with the origin in the top left corner.

   +   ...
   ^   5 6 7 8 9
   |   0 1 2 3 4
 (0,0) ---> +

A BoxWorld can be loaded from a text file. The file uses the following format.

* Values are separated by spaces or tabs (not commas)
* Blank lines or lines starting with # (comments) are ignored
* The first data line is two integer values to specify width and height
* The second row specifies the Start and the Target boxes as index values.
	S 10 T 15
* Each BowWorld row is the specified per line of the text file.
	- Each type is specified by a single character ".", "~", "m" or "#".
	- Number of tile values must match the number of columns
* The number of rows must match the number of specified rows.

Example BoxWorld map file.

# This is a comment and is ignored
# First specify the width x height values
6 5
# Second specify the start and target box indexes
0 17
# Now specify each row of column values
. . . . . .
~ ~ X . . .
. ~ X ~ . .
. . X . . .
. m m m . .
# Note the number of rows and column values match

'''
from math import hypot
from enum import Enum
from graphics import COLOUR_NAMES, window
import pyglet
from point2d import Point2D
from graph import SparseGraph, Node, Edge
from searches import SEARCHES

box_types = {
	"CLEAR":  {"symbol": '.', "cost": {"CLEAR": 1,  "MUD": 2,  "WATER": 5,  "FOREST": 3,  "SAND": 2},  "colour": "WHITE"},
	"MUD":    {"symbol": 'm', "cost": {"CLEAR": 2,  "MUD": 4,  "WATER": 9,  "FOREST": 5,  "SAND": 3},  "colour": "BROWN"},
	"WATER":  {"symbol": '~', "cost": {"CLEAR": 5,  "MUD": 9,  "WATER": 10, "FOREST": 8,  "SAND": 6},  "colour": "AQUA"},
	"WALL":   {"symbol": 'X', "colour": "GREY"},
	# ── NEW TERRAIN TYPES (Feature 2) ────────────────────────────────────
	# FOREST: dense trees — slower than clear, cheaper than water
	"FOREST": {"symbol": 'f', "cost": {"CLEAR": 3,  "MUD": 5,  "WATER": 8,  "FOREST": 6,  "SAND": 4},  "colour": "FOREST_GREEN"},
	# SAND:   loose ground — slightly harder than clear, easier than mud
	"SAND":   {"symbol": 's', "cost": {"CLEAR": 2,  "MUD": 3,  "WATER": 6,  "FOREST": 4,  "SAND": 3},  "colour": "SAND_YELLOW"},
}

min_edge_cost = 1.0 # must be <= the minimum possible edge cost for A* heuristic admissibility

search_modes = list(SEARCHES.keys())

# ── AGENT CLASS (Feature 3) ──────────────────────────────────────────────────
# Agent walks the calculated path node-by-node, one step per update tick.
# Controls: press A to start/restart the agent walk, press R to reset it.
# The agent is drawn as a filled yellow circle on the "agent" batch layer.
class Agent(object):
	'''Walks the found path one node at a time, animated each update tick.'''

	STEP_INTERVAL = 0.25  # seconds between each node step

	def __init__(self):
		self.path       = []       # list of box index values to walk
		self.step_index = 0        # which node we are currently at
		self.active     = False    # only moves when True
		self.elapsed    = 0.0      # time accumulator

		# Visual marker — a filled yellow circle drawn above everything else.
		# Starts off-screen; position is updated each step.
		self.marker = pyglet.shapes.Circle(
			-100, -100,
			radius=12,
			color=COLOUR_NAMES["YELLOW"],
			batch=window.get_batch("agent")
		)
		# Thin black outline ring so the agent stands out against light tiles.
		self.outline = pyglet.shapes.Arc(
			-100, -100,
			radius=12, segments=30,
			color=COLOUR_NAMES["BLACK"],
			batch=window.get_batch("agent"),
			thickness=2
		)

	def start(self, boxes, path_indices):
		'''Load a new path and begin walking from the first node.'''
		if not path_indices or len(path_indices) < 2:
			print("Agent: no valid path to walk.")
			return
		self.path       = path_indices
		self.step_index = 0
		self.active     = True
		self.elapsed    = 0.0
		self._move_to(boxes, self.step_index)
		print("Agent: starting walk (%d nodes)." % len(self.path))

	def reset(self, hide=True):
		'''Stop the agent and hide the marker.'''
		self.active     = False
		self.step_index = 0
		self.elapsed    = 0.0
		if hide:
			self.marker.x  = -100
			self.marker.y  = -100
			self.outline.x = -100
			self.outline.y = -100

	def update(self, dt, boxes):
		'''Call every frame; advances the agent when enough time has passed.'''
		if not self.active:
			return
		self.elapsed += dt
		if self.elapsed >= self.STEP_INTERVAL:
			self.elapsed = 0.0
			self.step_index += 1
			if self.step_index >= len(self.path):
				self.active = False
				print("Agent: reached target!")
				return
			self._move_to(boxes, self.step_index)

	def _move_to(self, boxes, index):
		'''Snap the marker to the centre of the box at path[index].'''
		box = boxes[self.path[index]]
		cx, cy = box.center().x, box.center().y
		self.marker.x  = cx
		self.marker.y  = cy
		self.outline.x = cx
		self.outline.y = cy
		print("Agent: step %d -> box %d" % (index, self.path[index]))

# ─────────────────────────────────────────────────────────────────────────────

class Box(object):
	'''A single box for boxworld. '''

	def __init__(self,index, x, y, width, height, type='.'):
		self.x = x
		self.y = y
		self.index = index
		self.width = width
		self.height = height
		for key, value in box_types.items():
			if value['symbol'] == type:
				self.type = key
		#a box must be able to draw:
		# - a box with a grey outline and an (optional) filled colour
		self.box = pyglet.shapes.BorderedRectangle(
			x, y, width, height, border=1,
			color=COLOUR_NAMES[box_types[self.type]["colour"]], 
			border_color=COLOUR_NAMES["LIGHT_GREY"],
			batch=window.get_batch()
		)
		# - a label showing the box index
		self.label = pyglet.text.Label(
			str(index),
			font_name='Times New Roman',
			font_size=12,
			x=x+width//2, y=y+height//2,
			anchor_x='center', anchor_y='center',
			color=COLOUR_NAMES["BLACK"],
			batch=window.get_batch("numbers")
		)
		
		# center marker
		self.center_marker = pyglet.shapes.Circle(
			x+width//2, y+height//2,
			radius=3,
			color=COLOUR_NAMES["BLACK"],
			batch=window.get_batch("centers")
		)
		
		# nav graph node
		self.node = None

	def set_type(self, type):
		#this code gets repeated in a couple of places in theis func, so I made it a function-within-a-function
		#it's usually good practice to make sure things are only ever done in a single location, but sometimes that can make things harder to read
		def update_box(type):
			self.type = type
			self.box.color = COLOUR_NAMES[box_types[self.type]["colour"]]
		if type in box_types:
			update_box(type)
			return
		else:
			for key, value in box_types.items():
				if value['symbol'] == type:
					update_box(key)
					return
		print('not a known tile type "%s"' % type)
	
	def center(self):
		return Point2D(self.x+self.width//2, self.y+self.height//2)

class BoxWorld(object):
	'''A world made up of boxes. '''

	def __init__(self, x_boxes, y_boxes, window_width, window_height):
		self.boxes = [None]*x_boxes*y_boxes
		self.x_boxes= x_boxes 
		self.y_boxes= y_boxes 
		box_width = window_width // x_boxes
		box_height = window_height // y_boxes
		self.wx = (window_width-1) // self.x_boxes
		self.wy = (window_height-1) // self.y_boxes 
		for i in range(len(self.boxes)):
			self.boxes[i] = Box(
				i,
				i%x_boxes*box_width,
				i//x_boxes%y_boxes*box_height,
				box_width,box_height
			)
		# create nav_graph
		self.path = None
		self.graph = None
		
		self.start = self.boxes[1]
		self.start_marker = pyglet.shapes.Arc( #in pyglet a circle is filled, an arc is unfilled
			self.boxes[1].center().x,
			self.boxes[1].center().y,
			15, segments=30,
			color=COLOUR_NAMES["RED"],
			batch=window.get_batch("path"),
			thickness=4
		)
		self.target = self.boxes[2]
		self.target_marker = pyglet.shapes.Arc(
			self.boxes[2].center().x,
			self.boxes[2].center().y,
			15, segments=30,
			color=COLOUR_NAMES["GREEN"],
			batch=window.get_batch("path"),
			thickness=4
		)

		#lists used to store the primitives that render out our various pathfinding data
		self.render_path = []
		self.render_tree = []
		self.render_open_nodes = []
		self.render_graph = []

		self.reset_navgraph()

	def get_box_by_xy(self, ix, iy):
		idx = (self.x_boxes * iy) + ix
		return self.boxes[idx] if idx < len(self.boxes) else None

	def get_box_by_pos(self, x, y):
		idx = int((self.x_boxes * (y // self.wy)) + (x // self.wx))
		return self.boxes[idx] if idx < len(self.boxes) else None

	def _add_edge(self, from_idx, to_idx, distance=1.0):
		b = self.boxes
		if "cost" in box_types[b[from_idx].type] and b[to_idx].type in box_types[b[from_idx].type]["cost"]:
			cost = box_types[b[from_idx].type]["cost"][b[to_idx].type]
			self.graph.add_edge(Edge(from_idx, to_idx, cost*distance))

	def _manhattan(self, idx1, idx2):
		''' Manhattan distance between two nodes in boxworld, assuming the
		minimal edge cost so that we don't overestimate the cost). '''
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return (abs(x1-x2) + abs(y1-y2)) * min_edge_cost

	def _hypot(self, idx1, idx2):
		'''Return the straight line distance between two points on a 2-D
		Cartesian plane. Argh, Pythagoras... trouble maker. '''
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return hypot(x1-x2, y1-y2) * min_edge_cost

	def _max(self, idx1, idx2):
		'''Return the straight line distance between two points on a 2-D
		Cartesian plane. Argh, Pythagoras... trouble maker. '''
		x1, y1 = self.boxes[idx1].pos
		x2, y2 = self.boxes[idx2].pos
		return max(abs(x1-x2),abs(y1-y2)) * min_edge_cost


	def reset_navgraph(self):
		''' Create and store a new nav graph for this box world configuration.
		The graph is build by adding NavNode to the graph for each of the
		boxes in box world. Then edges are created (4-sided).
		'''
		self.path = None # invalid so remove if present
		self.graph = SparseGraph()
		# Set a heuristic cost function for the search to use
		self.graph.cost_h = self._manhattan
		#self.graph.cost_h = self._hypot
		#self.graph.cost_h = self._max

		nx, ny = self.x_boxes, self.y_boxes
		# add all the nodes required
		for i, box in enumerate(self.boxes):
			box.pos = (i % nx, i // nx) #tuple position
			box.node = self.graph.add_node(Node(idx=i))
		# build all the edges required for this world
		for i, box in enumerate(self.boxes):
			# four sided N-S-E-W connections
			if "cost" not in box_types[box.type]:
				continue
			# UP (i + nx)
			if (i+nx) < len(self.boxes):
				self._add_edge(i, i+nx)
			# DOWN (i - nx)
			if (i-nx) >= 0:
				self._add_edge(i, i-nx)
			# RIGHT (i + 1)
			if (i%nx + 1) < nx:
				self._add_edge(i, i+1)
			# LEFT (i - 1)
			if (i%nx - 1) >= 0:
				self._add_edge(i, i-1)
			# # Diagonal connections
			# # UP LEFT(i + nx - 1)
			# j = i + nx
			# if (j-1) < len(self.boxes) and (j%nx - 1) >= 0:
			# 	self._add_edge(i, j-1, 1.4142) # sqrt(1+1)
			# # UP RIGHT (i + nx + 1)
			# j = i + nx
			# if (j+1) < len(self.boxes) and (j%nx + 1) < nx:
			# 	self._add_edge(i, j+1, 1.4142)
			# # DOWN LEFT(i - nx - 1)
			# j = i - nx
			# if (j-1) >= 0 and (j%nx - 1) >= 0:
			# 	print(i, j, j%nx)
			# 	self._add_edge(i, j-1, 1.4142)
			# # DOWN RIGHT (i - nx + 1)
			# j = i - nx
			# if (j+1) >= 0 and (j%nx +1) < nx:
			# 	self._add_edge(i, j+1, 1.4142)
		
		# add the graph to the render_graph
		for line in self.render_graph:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		for start, edge in self.graph.edgelist.items():
			for target in edge.keys():
				self.render_graph.append(
					pyglet.shapes.Line(
						self.boxes[start].center().x, 
						self.boxes[start].center().y,
						self.boxes[target].center().x,
						self.boxes[target].center().y,
						thickness=1.0, 
						color=COLOUR_NAMES['PURPLE'],
						batch=window.get_batch("edges")
					)
				)

	def set_start(self, idx):
		'''Set the start box based on its index idx value. '''
		# remove any existing start node, set new start node
		if self.target == self.boxes[idx]:
			print("Can't have the same start and end boxes!")
			return
		self.start = self.boxes[idx]
		self.start_marker.x = self.start.center().x
		self.start_marker.y = self.start.center().y

	def set_target(self, idx):
		'''Set the target box based on its index idx value. '''
		# remove any existing target node, set new target node
		if self.start == self.boxes[idx]:
			print("Can't have the same start and end boxes!")
			return
		self.target = self.boxes[idx]
		self.target_marker.x = self.target.center().x
		self.target_marker.y = self.target.center().y

	def plan_path(self, search, limit):
		'''Conduct a nav-graph search from the current world start node to the
		current target node, using a search method that matches the string
		specified in `search`.
		'''
		cls = SEARCHES[search]
		self.path = cls(self.graph, self.start.index, self.target.index, limit)
		# print the path details
		print(self.path.report())
		#then add them to the renderer
		#render the final path
		for line in self.render_path:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		p = self.path.path # alias to save us some typing
		if(len(p) > 1):
			for idx in range(len(p)-1):
				self.render_path.append(
					pyglet.shapes.Line(
						self.boxes[p[idx]].center().x, 
						self.boxes[p[idx]].center().y,
						self.boxes[p[idx+1]].center().x,
						self.boxes[p[idx+1]].center().y,
						thickness=3, 
						color=COLOUR_NAMES['BLUE'],
						batch=window.get_batch("path")
					)
				)
		for line in self.render_tree:
			try:
				line.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		#render the search tree
		t = self.path.route # alias to save us some typing
		if(len(t) > 1):
			for start, end in t.items():
				self.render_tree.append(
					pyglet.shapes.Line(
						self.boxes[start].center().x, 
						self.boxes[start].center().y,
						self.boxes[end].center().x,
						self.boxes[end].center().y,
						thickness=2, 
						color=COLOUR_NAMES['PINK'],
						batch=window.get_batch("tree")
					)
				)
		for circle in self.render_open_nodes:
			try:
				circle.delete() #pyglets Line.delete method is slightly broken
			except:
				pass
		#render the nodes that were still on the search stack when the search ended
		o = self.path.open # alias to save us some typing
		if(len(o) > 0):
			for idx in o:
				self.render_open_nodes.append(
					pyglet.shapes.Circle(
						self.boxes[idx].center().x, 
						self.boxes[idx].center().y,
						5, 
						color=COLOUR_NAMES['ORANGE'],
						batch=window.get_batch("tree")
					)
				)


	@classmethod
	def FromFile(cls, filename ):
		'''Support a the construction of a BoxWorld map from a simple text file.
		See the module doc details at the top of this file for format details.
		'''
		# open and read the file
		f = open(filename)
		lines = []
		for line in f.readlines():
			line = line.strip()
			if line and not line.startswith('#'):
				lines.append(line)
		f.close()
		# first line is the number of boxes width, height
		nx, ny = [int(bit) for bit in lines.pop(0).split()]
		# Create a new BoxWorld to store all the new boxes in...
		world = BoxWorld(nx, ny, window.width, window.height)
		# Get and set the Start and Target tiles
		s_idx, t_idx = [int(bit) for bit in lines.pop(0).split()]
		world.set_start(s_idx)
		world.set_target(t_idx)
		# Ready to process each line
		assert len(lines) == ny, "Number of rows doesn't match data."
		# read each line
		idx = 0
		for line in reversed(lines): # in reverse order
			bits = line.split()
			assert len(bits) == nx, "Number of columns doesn't match data."
			for bit in bits:
				bit = bit.strip()
				world.boxes[idx].set_type(bit)
				idx += 1
		world.reset_navgraph()
		return world