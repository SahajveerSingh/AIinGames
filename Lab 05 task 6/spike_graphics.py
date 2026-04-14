'''
spike_graphics.py - Task 6 Spike
Extends graphics.py with the "agents" batch layer needed for multi-agent rendering.
Also adds ROCK_GREY and GRASS colours.
'''
import pyglet

COLOUR_NAMES = {
    'BLACK':        (  0,   0,   0, 255),
    'WHITE':        (255, 255, 255, 255),
    'RED':          (255,   0,   0, 255),
    'GREEN':        (  0, 255,   0, 255),
    'BLUE':         (  0,   0, 255, 255),
    'GREY':         (100, 100, 100, 255),
    'PINK':         (255, 175, 175, 255),
    'YELLOW':       (255, 255,   0, 255),
    'ORANGE':       (255, 175,   0, 255),
    'PURPLE':       (200,   0, 175, 200),
    'BROWN':        (125, 125, 100, 255),
    'AQUA':         (100, 230, 255, 255),
    'DARK_GREEN':   (  0, 100,   0, 255),
    'LIGHT_GREEN':  (150, 255, 150, 255),
    'LIGHT_BLUE':   (150, 150, 255, 255),
    'LIGHT_GREY':   (200, 200, 200, 255),
    'LIGHT_PINK':   (255, 230, 230, 255),
    'FOREST_GREEN': ( 34, 139,  34, 255),
    'SAND_YELLOW':  (210, 180, 140, 255),
    'ROCK_GREY':    (139, 137, 137, 255),   # new for Task 6
    'GRASS_GREEN':  (124, 205,  80, 255),   # bright grass (unused alias)
}
# Alias used by spike_box_types
COLOUR_NAMES['LIGHT_GREEN'] = (144, 238, 80, 255)  # brighter grass

class SpikeWindow(pyglet.window.Window):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.fps_display = pyglet.window.FPSDisplay(self)
        self.cfg = {
            'PATH':    True,
            'AGENTS':  True,
            'NUMBERS': False,
        }
        self.batches = {
            "main":    pyglet.graphics.Batch(),
            "path":    pyglet.graphics.Batch(),
            "agents":  pyglet.graphics.Batch(),   # multi-agent layer
            "numbers": pyglet.graphics.Batch(),
        }
        self.labels = {
            'status': pyglet.text.Label(
                'Status: Loading...', x=5, y=self.height - 22,
                color=COLOUR_NAMES['BLACK'], font_name='Arial', font_size=11),
            'info': pyglet.text.Label(
                '', x=5, y=self.height - 42,
                color=(60, 60, 60, 255), font_name='Arial', font_size=10),
        }
        self._add_handlers()

    def _update_label(self, key, text):
        if key in self.labels:
            self.labels[key].text = text

    def get_batch(self, name="main"):
        return self.batches[name]

    def _add_handlers(self):
        @self.event
        def on_draw():
            self.clear()
            self.batches["main"].draw()
            if self.cfg['PATH']:
                self.batches["path"].draw()
            if self.cfg['AGENTS']:
                self.batches["agents"].draw()
            if self.cfg['NUMBERS']:
                self.batches["numbers"].draw()
            self.fps_display.draw()
            for lbl in self.labels.values():
                lbl.draw()

        @self.event
        def on_key_press(symbol, modifiers):
            from spike_game import spike_game
            if spike_game:
                spike_game.input_keyboard(symbol, modifiers)

        @self.event
        def on_mouse_press(x, y, button, modifiers):
            from spike_game import spike_game
            if spike_game:
                spike_game.input_mouse(x, y, button, modifiers)

# Single global window instance
window = SpikeWindow(width=900, height=900, vsync=True, resizable=False,
                     caption="Task 6 Spike - Navigation with Graphs")
