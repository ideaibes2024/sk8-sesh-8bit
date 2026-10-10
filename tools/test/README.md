# Test rig

The game is a thin client: every outcome comes from a remote game server, and
this clone's origin is not on that server's allowlist, so it cannot complete a
round. These scripts stand in a mock server **and** the page on one local
origin, so the page uses its own local-RGS code path with no CORS involved, and
drive it with a real headless Chromium.

The mock does not model the game's maths. It serves hand-built books that
satisfy `ttFromBook`'s contract, so what is under test is the client:
presentation, state handling and the controls.

```bash
npm i playwright                       # once, anywhere on the path below
node tools/test/mock-rgs.js "$PWD" 8787 &
node tools/test/drive.js               # spins, wins, double-click, malformed book
node tools/test/drive2.js              # autoplay STOP, tab switch mid-round
node tools/test/drive3.js 8787         # all six bonus paths
node tools/test/drive4.js 8787         # win tiers, themed messages, particles
node tools/test/sheet.js out.png       # symbol + pose contact sheet
node tools/test/shot.js out.png 8787   # screenshot of a winning board
```

`drive3.js` covers crew (sticky wilds), sesh (expand), legend (held reels,
anchors, growing stacks), the min-win top-up, a bought bonus and the win cap.

To test a build against these, point the mock at that build's directory:
`node tools/test/mock-rgs.js /path/to/other/build 8788`.

Scenarios are queued per spin: `POST /_test {"queue":["win5","legend"]}`.

## Local play mode

This clone cannot reach the game server, so the page falls back to the math
engine it already ships and plays rounds in the browser. `?local=1` forces it.

The config in `index.html` (`LOCAL_CFG`) was solved offline by these, in order:

```bash
node tools/test/search.js          # symbol counts that hit the published 1-in-413 trigger
node tools/test/tune2.js  8000     # wild density + table mix per bought mode
node tools/test/final.js  60000    # compose base RTP from exact lines + measured tier EVs
node tools/test/ante.js            # same for Bonus Boost
node tools/test/emit.js            # emit the LOCAL_CFG literal
node tools/test/verify-embedded.js # re-check the literal AS SHIPPED in index.html
```

`final.js` composes rather than samples: the base game end to end is swamped by
Legend bonuses at 1 in ~90,000 paying hundreds of x, so a 250k-spin estimate
swings several points. Line RTP is exact from `ttAnalyzeBase`; each tier's EV is
measured by playing that tier directly.

Verified against the shipped bytes:

| | local engine | published |
|---|---|---|
| base RTP | 96.11% | 96.01% |
| base bonus | 1 in 418 | 1 in 413 |
| Bonus Boost RTP | 96.21% | 96.01% |
| Bonus Boost bonus | 1 in 102 | 1 in 105 |
| Crew / Sesh / Legend buys | 97% / 93% / 92% of price | 96% |

```bash
node tools/test/static.js "$PWD" 8795   # plain file server, no /wallet at all
node tools/test/drivelocal.js           # boots, falls back, plays 40 rounds
node tools/test/soak.js                 # 220 rounds, watches bonuses trigger
```
