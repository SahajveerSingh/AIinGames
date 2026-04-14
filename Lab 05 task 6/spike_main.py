'''
spike_main.py - Task 6 Spike Entry Point
COS30002 AI for Games

Run with:
    python spike_main.py
    python spike_main.py spike_map.txt
'''
import sys
import os

import pyglet
pyglet.options['win32_gdi_font'] = True   # Windows DirectWrite crash fix

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

import spike_graphics   # creates the global window
import spike_game

if __name__ == '__main__':
    filename = sys.argv[1] if len(sys.argv) > 1 else 'spike_map.txt'
    if not os.path.isabs(filename):
        filename = os.path.join(SCRIPT_DIR, filename)

    spike_game.spike_game = spike_game.SpikeGame(filename)

    def update(dt):
        if spike_game.spike_game:
            spike_game.spike_game.update(dt)

    pyglet.clock.schedule_interval(update, 1 / 60.0)
    pyglet.app.run()
