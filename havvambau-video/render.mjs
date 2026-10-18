// Renders video.html frame-by-frame with Chromium and encodes with ffmpeg.
//   node render.mjs stills 0.5 2.8 6 ...   -> out/still_<t>.png
//   node render.mjs video [fps] [workers]  -> out/<name>_silent.mp4
// HTML=video_v2.html selects the composition (default video.html).
import { createRequire } from 'node:module';
import { spawn } from 'node:child_process';
import { mkdirSync, writeFileSync, rmSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';

const require = createRequire(import.meta.url);
let pw;
try { pw = require('playwright'); } catch { pw = require('/opt/node-tools/node_modules/playwright'); }

const dir = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(dir, 'out');
mkdirSync(out, { recursive: true });
const html = process.env.HTML || 'video.html';
const url = pathToFileURL(path.join(dir, html)).href;
const name = html === 'video.html' ? 'havvambau_reel' : `havvambau_reel_${path.basename(html, '.html').replace('video_', '')}`;

async function openPage(browser) {
  const page = await browser.newPage({ viewport: { width: 1080, height: 1920 }, deviceScaleFactor: 1 });
  await page.goto(url);
  await page.evaluate(() => window.ready);
  return page;
}

const [mode = 'stills', ...args] = process.argv.slice(2);
const browser = await pw.chromium.launch({ args: ['--allow-file-access-from-files', '--disable-gpu-vsync'] });

if (mode === 'stills') {
  const page = await openPage(browser);
  for (const t of args.map(Number)) {
    await page.evaluate(t => window.renderFrame(t), t);
    await page.screenshot({ path: path.join(out, `still_${t.toFixed(2)}.png`), clip: { x: 0, y: 0, width: 1080, height: 1920 } });
  }
} else if (mode === 'video') {
  const fps = Number(args[0] || 60);
  const workers = Number(args[1] || 4);
  const page0 = await openPage(browser);
  const duration = await page0.evaluate(() => window.DURATION);
  await page0.close();
  const total = Math.round(duration * fps);
  const per = Math.ceil(total / workers);
  const segDir = path.join(out, 'seg');
  rmSync(segDir, { recursive: true, force: true });
  mkdirSync(segDir, { recursive: true });
  const t0 = Date.now();
  let done = 0;

  const jobs = Array.from({ length: workers }, async (_, w) => {
    const from = w * per, to = Math.min(total, from + per);
    const page = await openPage(browser);
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(fps), '-c:v', 'png', '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '10', '-pix_fmt', 'yuv444p', path.join(segDir, `seg${w}.mp4`)],
      { stdio: ['pipe', 'inherit', 'inherit'] });
    for (let f = from; f < to; f++) {
      await page.evaluate(t => window.renderFrame(t), f / fps);
      const buf = await page.screenshot({ type: 'png', clip: { x: 0, y: 0, width: 1080, height: 1920 } });
      if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
      if (++done % 120 === 0) console.log(`${done}/${total} frames  ${((Date.now() - t0) / 1000).toFixed(0)}s`);
    }
    ff.stdin.end();
    await new Promise(r => ff.on('close', r));
    await page.close();
  });
  await Promise.all(jobs);

  writeFileSync(path.join(segDir, 'list.txt'), Array.from({ length: workers }, (_, w) => `file 'seg${w}.mp4'`).join('\n'));
  await new Promise((res, rej) => {
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'concat', '-safe', '0', '-i', path.join(segDir, 'list.txt'),
      '-c:v', 'libx264', '-preset', 'slow', '-crf', '16', '-pix_fmt', 'yuv420p', '-profile:v', 'high', '-movflags', '+faststart',
      '-r', String(fps), path.join(out, `${name}_silent.mp4`)], { stdio: 'inherit' });
    ff.on('close', c => (c === 0 ? res() : rej(new Error('ffmpeg concat failed'))));
  });
  console.log(`done: ${total} frames in ${((Date.now() - t0) / 1000).toFixed(0)}s`);
}
await browser.close();
