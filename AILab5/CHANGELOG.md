# Changelog

## [2026-03-25 - 23:20]
- **Fixed:** Reverted string enum casts in `game.py` algorithm switches back to their default underlying integer representations to resolve `KeyError: 'DFS'` runtime crashes.

## [2026-03-25 - 23:16]
- **Fixed:** Corrected an indentation and syntax error in `graphics.py` where a dictionary declaration was missing its variable assignment.

## [2026-03-25 - 23:11]
- **Fixed (Graphics):** Added the missing configuration logic for toggleable 'Centers' (`C`) mode in `graphics.py` and `BoxWorld.__init__`.
- **Fixed (Input):** Resolved float evaluation crash when acquiring cell index via mouse coordinates.
- **Fixed (Logic):** Resolved missing attribute errors for keyboard-controlled searches by renaming variables to `self.search_limit` and resolving strict string parameters for algorithm enumeration.

## [2026-03-25 - 23:06]
- **Documentation:** Merged legacy `readme.txt` into standard `README.md` format, updated descriptions, preserved original authorship (Clinton Woodward) and cited updated maintainer (Enrique Ketterer).

## [2026-03-25 - 23:00]
- **Fixed:** Refactored `box_world.py` to use `thickness` instead of `width` for `pyglet.shapes.Line` invocations, ensuring compatibility with Pyglet 2.0+.
