// plain static file server: NO /wallet API at all, like GitHub Pages
const http=require('http'),fs=require('fs'),path=require('path');
const ROOT=process.argv[2],PORT=+process.argv[3];
const M={'.html':'text/html','.svg':'image/svg+xml','.png':'image/png','.woff2':'font/woff2','.js':'text/javascript'};
http.createServer((q,r)=>{const u=new URL(q.url,'http://x');
 let f=path.join(ROOT,u.pathname==='/'?'index.html':u.pathname.slice(1));
 fs.readFile(f,(e,d)=>{if(e){r.writeHead(404);return r.end('nf');}
 r.writeHead(200,{'Content-Type':M[path.extname(f)]||'application/octet-stream'});r.end(d);});
}).listen(PORT,()=>console.log('static on '+PORT));
