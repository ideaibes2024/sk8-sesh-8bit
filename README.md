# SK8 SESH — 8-bit scene rework

A copy of [SK8 SESH](https://ozbsachs.github.io/sk8-sesh/) with the skatepark
background rebuilt as real pixel art. The original repo is untouched.

## What changed

Only the background. The two inline SVG data-URIs in `index.html` were replaced
with generated pixel-art scenes:

- `scene-day.svg` — the park in daylight
- `scene-night.svg` — the same park at dusk, used during the bonus round

Both are drawn on a 320×180 pixel grid scaled 5× to 1600×900, with
`shape-rendering="crispEdges"` so they stay blocky at any size.

The park has a quarter pipe, a pool-coping bowl, a 5-stair set with handrail,
a funbox, a flat rail, a graffiti block wall, chain-link fencing, floodlight
towers and assorted props — plus 14 skaters, male and female, most of them
mid-trick (airs, grinds, a kickflip, a manual, a bowl carve, a filmer, and a
crew watching from the ledge).

## Regenerating the art

    python3 tools/gen_scene.py          # writes both SVGs
    python3 tools/gen_scene.py --png    # also writes previews into tools/

Edit poses, palettes or skater positions in `tools/gen_scene.py` and re-run.
