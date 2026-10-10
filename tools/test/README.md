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
node tools/test/sheet.js out.png       # symbol + pose contact sheet
node tools/test/shot.js out.png 8787   # screenshot of a winning board
```

`drive3.js` covers crew (sticky wilds), sesh (expand), legend (held reels,
anchors, growing stacks), the min-win top-up, a bought bonus and the win cap.

To test a build against these, point the mock at that build's directory:
`node tools/test/mock-rgs.js /path/to/other/build 8788`.

Scenarios are queued per spin: `POST /_test {"queue":["win5","legend"]}`.
