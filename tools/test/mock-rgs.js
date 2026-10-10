// Mock RGS for testing SK8 SESH's client. Serves the repo AND the /wallet API
// from one origin, so the page's own local-rgs path is used and there is no CORS.
const http = require('http'), fs = require('fs'), path = require('path');
const ROOT = process.argv[2], PORT = +process.argv[3] || 8787;
const API = 1e6;
let balance = 1000 * API;
const MIME = {'.html':'text/html','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2','.js':'text/javascript','.json':'application/json'};

const SYM = ['L1','L2','L3','L4','L5','H1','H2','H3','H4','W','S1','S2'];
// scenario queue the test driver fills via POST /_test
let queue = [];

function board(grid, mults){            // grid: 20 ints, column-major (reel*4+row)
  return [0,1,2,3,4].map(r => [0,1,2,3].map(row => {
    const c = r*4+row, s = {name: SYM[grid[c]]};
    if (grid[c] === 9) s.multiplier = (mults && mults[c]) || 2;
    return s;
  }));
}
const LOSS = Array.from({length:20},(_,c)=>[0,1,2,3,4,5,6,7][(c*3+Math.floor(c/4))%8]);

function bookLose(){
  const g = LOSS.slice();
  return [{type:'reveal', gameType:'basegame', board: board(g)},
          {type:'winInfo', wins: []}, {type:'setWin', amount: 0}, {type:'finalWin', amount: 0}];
}
// a line win: symbol H4 (index 8) across the first k reels on payline 0 (top row)
function bookWin(k, payX100){
  const g = LOSS.slice();
  for (let r=0;r<k;r++) g[r*4+0] = 8;
  for (let r=k;r<5;r++) g[r*4+0] = 0;        // break the run
  return [{type:'reveal', gameType:'basegame', board: board(g)},
          {type:'winInfo', wins: [{kind:k, symbol:'H4', win:payX100, meta:{lineIndex:0, winWithoutMult:payX100, multiplier:1}}]},
          {type:'setWin', amount: payX100}, {type:'finalWin', amount: payX100}];
}
// deliberately malformed: freeSpinTrigger with an unknown bonus key -> tier -1
function bookBadBonus(){
  const g = LOSS.slice();
  return [{type:'reveal', gameType:'basegame', board: board(g)},
          {type:'freeSpinTrigger', bonus:'not-a-real-bonus', totalFs: 10},
          {type:'finalWin', amount: 0}];
}
const BONUS = require('/tmp/claude-0/sk8test/bonus-books.js');
const SCEN = Object.assign({lose: bookLose, win3: () => bookWin(3, 50), win5: () => bookWin(5, 1500), bad: bookBadBonus}, BONUS);

function send(res, code, obj){ const b = JSON.stringify(obj); res.writeHead(code, {'Content-Type':'application/json','Content-Length':Buffer.byteLength(b)}); res.end(b); }
function body(req){ return new Promise(r => { let d=''; req.on('data',c=>d+=c); req.on('end',()=>{ try{r(JSON.parse(d||'{}'))}catch(e){r({})} }); }); }

http.createServer(async (req, res) => {
  const u = new URL(req.url, 'http://x');
  if (u.pathname === '/_test'){ const b = await body(req); queue = b.queue || []; return send(res,200,{ok:true,queued:queue.length}); }
  if (u.pathname === '/game') return send(res, 200, {});
  if (u.pathname === '/wallet/authenticate')
    return send(res, 200, {balance:{amount:balance, currency:'USD'}, player:{name:'Tester'},
      config:{minBet:1e5, maxBet:1e8, stepBet:1e5, defaultBetLevel:1e6, betLevels:[1e5,5e5,1e6,2e6,5e6], jurisdiction:{}, deposits:[100e6,500e6]},
      round:{active:false}});
  if (u.pathname === '/wallet/balance') return send(res, 200, {balance:{amount:balance}});
  if (u.pathname === '/wallet/end-round') return send(res, 200, {balance:{amount:balance}});
  if (u.pathname === '/wallet/play'){
    const b = await body(req);
    balance -= b.amount;
    const key = queue.shift() || 'lose';
    const ev = (SCEN[key] || bookLose)();
    const fin = ev[ev.length-1];
    const won = Math.round((fin.amount||0)/100 * b.amount);
    balance += won;
    return send(res, 200, {balance:{amount:balance}, round:{active:true, state:ev, amount:b.amount}});
  }
  // static
  let f = path.join(ROOT, u.pathname === '/' ? 'index.html' : u.pathname.slice(1));
  fs.readFile(f, (e,d) => { if (e){ res.writeHead(404); return res.end('nf'); }
    res.writeHead(200, {'Content-Type': MIME[path.extname(f)] || 'application/octet-stream'}); res.end(d); });
}).listen(PORT, () => console.log('mock rgs on ' + PORT));
