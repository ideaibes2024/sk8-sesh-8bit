// Bonus books built against ttFromBook's contract (index.html ~2743-2810).
// The maths is not meant to be realistic -- these exist to drive the real
// presentation path: trigger, free spins, expands, sticky/held reels,
// Legend stacks, the min-win top-up and the bought-bonus entry.
const SYM = ['L1', 'L2', 'L3', 'L4', 'L5', 'H1', 'H2', 'H3', 'H4', 'W', 'S1', 'S2'];
const cell = (r, row) => r * 4 + row;

// grid helpers -------------------------------------------------------------
const base = () => Array.from({ length: 20 }, (_, c) => [0, 1, 2, 3, 4, 5, 6, 7][(c * 3 + (c >> 2)) % 8]);
function board(g, mults) {
  return [0, 1, 2, 3, 4].map(r => [0, 1, 2, 3].map(row => {
    const c = cell(r, row), o = { name: SYM[g[c]] };
    if (g[c] === 9) o.multiplier = (mults && mults[c]) || 2;
    return o;
  }));
}
// a board carrying `n` wilds on distinct reels, each with a multiplier
function withWilds(n, mult) {
  const g = base(), m = new Array(20).fill(0);
  for (let r = 0; r < n; r++) { const c = cell(r, 1); g[c] = 9; m[c] = mult || 2; }
  return { g, m };
}
// a line win of `k` H4 along payline 0
function lineWin(k, x100) {
  return [{ kind: k, symbol: 'H4', win: x100, meta: { lineIndex: 0, winWithoutMult: x100, multiplier: 1 } }];
}
function winBoard(k) {
  const g = base();
  for (let r = 0; r < k; r++) g[cell(r, 0)] = 8;
  for (let r = k; r < 5; r++) g[cell(r, 0)] = 0;
  return { g, m: new Array(20).fill(0) };
}

// one free spin: reveal -> (expand) -> winInfo -> setWin
function freeSpin(ev, opts) {
  const o = opts || {}, b = o.b || winBoard(0);
  const rev = { type: 'reveal', gameType: 'freegame', board: board(b.g, b.m) };
  if (o.held) rev.heldReels = o.held;
  if (o.sticky) rev.sticky = o.sticky;
  ev.push(rev);
  if (o.expand) ev.push({ type: 'expand', reels: o.expand });
  ev.push({ type: 'winInfo', wins: o.wins || [] });
  ev.push({ type: 'setWin', amount: o.win || 0 });
}

// --- triggered bonuses ----------------------------------------------------
function trigger(key, n, opts) {
  const o = opts || {};
  const ev = [];
  const tb = o.bought ? null : withWilds(3, 4);
  if (tb) {
    ev.push({ type: 'reveal', gameType: 'basegame', board: board(tb.g, tb.m) });
    ev.push({ type: 'winInfo', wins: [] });
    ev.push({ type: 'setWin', amount: 0 });
  }
  const trg = { type: 'freeSpinTrigger', bonus: key, totalFs: n };
  if (o.plain) trg.wilds = 'plain';
  ev.push(trg);
  return ev;
}

function crew(n) {                    // tier 0: wilds stay sticky between spins
  const ev = trigger('crew', n);
  freeSpin(ev, { b: winBoard(3), wins: lineWin(3, 60), win: 60 });
  freeSpin(ev, { b: withWilds(2, 3), win: 0 });
  freeSpin(ev, { b: winBoard(4), wins: lineWin(4, 300), win: 300 });
  ev.push({ type: 'freeSpinEnd', amount: 360 });
  ev.push({ type: 'finalWin', amount: 360 });
  return ev;
}

function sesh(n) {                    // tier 1, with a hit big enough for the count-up
  const ev = trigger('sesh', n);
  freeSpin(ev, { b: winBoard(3), wins: lineWin(3, 40), win: 40 });
  freeSpin(ev, {
    b: winBoard(5), wins: lineWin(5, 900), win: 900,
    expand: [{ reel: 2, multiplier: 5, from: [{ reel: 2, row: 1, multiplier: 5 }] }]
  });
  ev.push({ type: 'freeSpinEnd', amount: 940 });
  ev.push({ type: 'finalWin', amount: 940 });
  return ev;
}

function legend(n) {                  // tier 2: held reels and growing stacks
  const ev = trigger('legend', n);
  freeSpin(ev, {
    b: withWilds(1, 3), win: 0,
    expand: [{ reel: 1, multiplier: 3, from: [{ reel: 1, row: 1, multiplier: 3 }], anchor: { reel: 1, row: 1, multiplier: 3 } }]
  });
  freeSpin(ev, {
    b: winBoard(3), wins: lineWin(3, 120), win: 120,
    held: [{ reel: 1, multiplier: 3 }],
    expand: [{ reel: 3, multiplier: 4, from: [{ reel: 3, row: 2, multiplier: 4 }], anchor: { reel: 3, row: 2, multiplier: 4 } }]
  });
  freeSpin(ev, {
    b: winBoard(4), wins: lineWin(4, 400), win: 400,
    held: [{ reel: 1, multiplier: 3 }, { reel: 3, multiplier: 4 }]
  });
  ev.push({ type: 'freeSpinEnd', amount: 520 });
  ev.push({ type: 'finalWin', amount: 520 });
  return ev;
}

function minwin() {                   // the 10%-of-price top-up path
  const ev = trigger('crew', 2);
  freeSpin(ev, { win: 0 });
  freeSpin(ev, { win: 0 });
  ev.push({ type: 'minWin', amount: 1250 });
  ev.push({ type: 'freeSpinEnd', amount: 1250 });
  ev.push({ type: 'finalWin', amount: 1250 });
  return ev;
}

function bought() {                   // a bonus BUY: no base reveal before the trigger
  const ev = trigger('sesh', 2, { bought: true });
  freeSpin(ev, { b: winBoard(3), wins: lineWin(3, 80), win: 80 });
  freeSpin(ev, { b: winBoard(5), wins: lineWin(5, 1200), win: 1200 });
  ev.push({ type: 'freeSpinEnd', amount: 1280 });
  ev.push({ type: 'finalWin', amount: 1280 });
  return ev;
}

function capped() {                   // the win-cap path
  const ev = trigger('legend', 1);
  freeSpin(ev, { b: winBoard(5), wins: lineWin(5, 100000), win: 100000 });
  ev.push({ type: 'wincap' });
  ev.push({ type: 'freeSpinEnd', amount: 100000 });
  ev.push({ type: 'finalWin', amount: 100000 });
  return ev;
}

module.exports = {
  crew: () => crew(3), sesh: () => sesh(2), legend: () => legend(3),
  minwin, bought, capped,
};
