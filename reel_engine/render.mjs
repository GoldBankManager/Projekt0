#!/usr/bin/env node
// Rendert eine Code-Komposition (HTML-Seite mit window.renderFrame(t)) Frame für Frame zu MP4.
//
//   node reel_engine/render.mjs reels/havvambau_01 [--fps 30] [--from 0] [--to 9.8] [--workers 2]
//   node reel_engine/render.mjs reels/havvambau_01 --stills 0.3,2.2,5.8   → PNG-Standbilder zum Prüfen
//
// Die Seite muss window.ready = true setzen und window.renderFrame(t) bereitstellen.
// Tonspur wird separat erzeugt (sfx.py) und mit mux.sh angelegt.
import { chromium } from 'playwright';
import { spawn } from 'child_process';
import http from 'http';
import fs from 'fs';
import path from 'path';

const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');
const args = process.argv.slice(2);
const reelDir = args[0];
if (!reelDir) { console.error('Usage: render.mjs <reel-dir> [--fps 30] [--from s] [--to s] [--workers n] [--stills a,b,c]'); process.exit(1); }
const opt = (k, d) => { const i = args.indexOf('--' + k); return i >= 0 ? args[i + 1] : d; };
const timeline = JSON.parse(fs.readFileSync(path.join(ROOT, reelDir, 'timeline.json'), 'utf8'));
const fps = +opt('fps', timeline.fps || 30);
const from = +opt('from', 0);
const to = +opt('to', timeline.duration);
const workers = +opt('workers', 2);
const stills = opt('stills', null);
const W = 1080, H = 1920;
const outDir = path.join(ROOT, reelDir, 'out');
fs.mkdirSync(outDir, { recursive: true });

const TYPES = { '.js': 'text/javascript', '.mjs': 'text/javascript', '.html': 'text/html', '.json': 'application/json',
  '.woff2': 'font/woff2', '.woff': 'font/woff', '.css': 'text/css', '.png': 'image/png', '.jpg': 'image/jpeg', '.svg': 'image/svg+xml' };
const server = http.createServer((req, res) => {
  const p = path.join(ROOT, decodeURIComponent(req.url.split('?')[0]));
  if (!p.startsWith(ROOT) || !fs.existsSync(p) || fs.statSync(p).isDirectory()) { res.writeHead(404); return res.end(); }
  res.writeHead(200, { 'Content-Type': TYPES[path.extname(p)] || 'application/octet-stream' });
  fs.createReadStream(p).pipe(res);
});
await new Promise(r => server.listen(0, r));
const url = `http://localhost:${server.address().port}/${reelDir}/index.html`;

async function openPage() {
  const browser = await chromium.launch({
    executablePath: fs.existsSync('/opt/pw-browsers/chromium') ? '/opt/pw-browsers/chromium' : undefined,
    args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'],
  });
  const page = await browser.newPage({ viewport: { width: W, height: H } });
  page.on('pageerror', e => console.error('PAGE ERROR', e.message));
  page.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') console.error('PAGE', m.text()); });
  await page.goto(url);
  await page.waitForFunction(() => window.ready === true, null, { timeout: 120000 });
  return { browser, page };
}

const debug = opt('debug', null);
if (debug) { // JSON-Datei mit [{name, pos, target, fov, pose, mode, ...}]
  const { browser, page } = await openPage();
  for (const v of JSON.parse(fs.readFileSync(debug, 'utf8'))) {
    const info = await page.evaluate(o => window.debugRender(o), v);
    const f = path.join(outDir, `dbg_${v.name}.png`);
    await page.screenshot({ path: f }); console.log(f, JSON.stringify(info));
  }
  await browser.close(); server.close(); process.exit(0);
}

if (stills) {
  const { browser, page } = await openPage();
  for (const s of stills.split(',').map(Number)) {
    await page.evaluate(t => window.renderFrame(t), s);
    const f = path.join(outDir, `still_${s.toFixed(3)}.png`);
    await page.screenshot({ path: f });
    console.log(f);
  }
  await browser.close(); server.close(); process.exit(0);
}

const first = Math.round(from * fps), last = Math.round(to * fps); // [first, last)
// Jeder Frame wird als JPEG gespeichert → ein abgebrochener Render setzt beim nächsten Start dort fort.
const framesDir = path.join(outDir, 'frames');
fs.mkdirSync(framesDir, { recursive: true });
const fname = f => path.join(framesDir, `f${String(f).padStart(5, '0')}.jpg`);
const todo = [];
for (let f = first; f < last; f++) if (!fs.existsSync(fname(f))) todo.push(f);
console.log(`${last - first} Frames, ${todo.length} zu rendern, ${workers} Worker`);
const t0 = Date.now();
let done = 0;
await Promise.all(Array.from({ length: workers }, async (_, w) => {
  const mine = todo.filter((_, i) => i % workers === w); // verschränkt → gleichmäßige Last
  if (!mine.length) return;
  const { browser, page } = await openPage();
  for (const f of mine) {
    await page.evaluate(t => window.renderFrame(t), f / fps);
    const buf = await page.screenshot({ type: 'jpeg', quality: 95, timeout: 0 });
    fs.writeFileSync(fname(f) + '.tmp', buf); fs.renameSync(fname(f) + '.tmp', fname(f));
    done++;
    if (done % 10 === 0) {
      const el = (Date.now() - t0) / 1000;
      process.stdout.write(`\r${done}/${todo.length} Frames  ${el.toFixed(0)}s  ETA ${(el / done * (todo.length - done)).toFixed(0)}s   `);
    }
  }
  await browser.close();
}));
server.close();

const video = path.join(outDir, 'video_only.mp4');
await new Promise((res, rej) => spawn('ffmpeg', ['-y', '-v', 'error', '-framerate', String(fps), '-start_number', String(first),
  '-i', path.join(framesDir, 'f%05d.jpg'), '-frames:v', String(last - first),
  '-c:v', 'libx264', '-preset', 'slow', '-crf', '18', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', video],
  { stdio: 'inherit' }).on('close', c => c ? rej(new Error('ffmpeg ' + c)) : res()));
console.log(`\n✓ ${video}  (${((Date.now() - t0) / 1000).toFixed(0)}s)`);
