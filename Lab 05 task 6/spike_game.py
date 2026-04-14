'''
spike_game.py - Task 6 Spike
Game controller: handles keyboard/mouse, wires world + agents + window together.

Controls:
  SPACE  - restart all agents on their current paths
  G      - shuffle all agent targets (dynamic environment)
  D      - randomly change 5 terrain tiles and replan (dynamic environment)
  P      - toggle path lines on/off
  A      - toggle agent visibility
  L      - toggle tile index numbers
'''
spike_game = None

import pyglet
from spike_world import SpikeWorld
from spike_graphics import window

class SpikeGame:
    def __init__(self, map_file):
        self.world = SpikeWorld.FromFile(map_file)
        self.world.spawn_agents()
        window._update_label('status',
            'Task 6 Spike | SPACE=restart  G=new targets  D=change terrain  P/A/L=toggles')
        window._update_label('info',
            'Yellow/Red/Pink = SpeedAgent  |  Blue/Orange/Green = CautiousAgent')
        print("SpikeGame ready. %d agents active." % len(self.world.manager.agents))

    def update(self, dt):
        self.world.update(dt)

    def input_keyboard(self, symbol, modifiers):
        key = pyglet.window.key

        if symbol == key.SPACE:
            # Restart all agents
            self.world.manager.start_all()
            window._update_label('status', 'All agents restarted!')

        elif symbol == key.G:
            # Step 7: dynamic - shuffle agent targets
            self.world.manager.shuffle_targets()
            window._update_label('status', 'Targets shuffled - agents replanned!')

        elif symbol == key.D:
            # Step 7: dynamic - change random terrain tiles
            self.world.toggle_random_terrain()
            window._update_label('status', 'Terrain changed - graph rebuilt - agents replanned!')

        elif symbol == key.P:
            window.cfg['PATH'] = not window.cfg['PATH']

        elif symbol == key.A:
            window.cfg['AGENTS'] = not window.cfg['AGENTS']

        elif symbol == key.L:
            window.cfg['NUMBERS'] = not window.cfg['NUMBERS']

    def input_mouse(self, x, y, button, modifiers):
        # Click a tile to see its type printed in the console
        box = self.world.get_box_by_pos(x, y)
        if box:
            from spike_world import spike_box_types
            info = spike_box_types.get(box.type, {})
            print("Clicked tile %d: type=%s  colour=%s" % (
                box.index, box.type, info.get('colour', '?')))
