'''  BoxWorldWindow to test/demo graph (path) search.

Created for COS30002 AI for Games, Lab,
by Clinton Woodward <cwoodward@swin.edu.au>, James Bonner <jbonner@swin.edu.au>

For class use only. Do not publically share or post this code without
permission.

'''

import sys
import os

# Fix for Windows DirectWrite crash (ffi_prep_cif_var failed).
# Forces Pyglet to use the older GDI font renderer instead of DirectWrite.
import pyglet
pyglet.options['win32_gdi_font'] = True

# Resolve paths relative to this script's directory so the program works
# regardless of which directory you launch it from.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# importing graphics for side-effects - it creates the window module object.
import graphics
import game

if __name__ == '__main__':
	if len(sys.argv) > 1:
		filename = sys.argv[1]
	else:
		filename = "map1.txt"

	# If the path isn't absolute, resolve it relative to the script's folder
	if not os.path.isabs(filename):
		filename = os.path.join(SCRIPT_DIR, filename)

	game.game = game.Game(filename)

	# ── AGENT TICK (Feature 3) ────────────────────────────────────────
	# Schedule the agent update at 60 fps so its animation runs smoothly.
	def update(dt):
		if game.game and game.game.agent:
			game.game.agent.update(dt, game.game.world.boxes)

	pyglet.clock.schedule_interval(update, 1/60.0)

	pyglet.app.run()
