// HavvamBau Reel 02 – "Erst der Plan. Dann HAVVAMBAU." – komplett in Code.
// Vor dem Drop: Bagger als gelber Bauplan (Linien auf Dunkelblau). Ab dem Drop: texturierter, dreckiger Bagger
// auf einer erkennbaren Baustelle im Sonnenuntergang. Logo-Build am Ende. Timing kommt aus timeline.json.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { mergeGeometries } from 'three/addons/utils/BufferGeometryUtils.js';
import { LineSegments2 } from 'three/addons/lines/LineSegments2.js';
import { LineSegmentsGeometry } from 'three/addons/lines/LineSegmentsGeometry.js';
import { LineMaterial } from 'three/addons/lines/LineMaterial.js';

const W = 1080, H = 1920;
const TL = await (await fetch('./timeline.json')).json();
const B = TL.beats, DROP = TL.drop, DIG = TL.dig_impact, DUMP = TL.dump, ROLL = TL.hat_roll;
const BRAND = 'HAVVAMBAU';

// ───────────────────────── Helfer ─────────────────────────
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, x) => clamp((x - a) / (b - a));
const E = {
  outCubic: t => 1 - Math.pow(1 - t, 3), inCubic: t => t * t * t, inQuad: t => t * t,
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  outBack: t => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
};
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const rnd = (i, k) => hash(i * 1.37 + k * 17.91 + 0.123);
const wobble = (t, s = 0) => Math.sin(t * 13.1 + s) * .5 + Math.sin(t * 23.7 + s * 2.1) * .3 + Math.sin(t * 41.3 + s * 3.7) * .2;
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix3 = (a, b, t) => a.clone().lerp(b, t);
const fx = x => Number(x).toFixed(4);
function vnoise(x, y, P = 1e9) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const h = (a, b) => hash(((a % P) + P) % P * 57.0 + (((b % P) + P) % P) * 131.0);
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v);
}
function fbm(x, y, oct = 5, P = 1e9) { let s = 0, a = .5, f = 1; for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f, P * f); f *= 2; a *= .5; } return s; }
function canvas(w, h, draw) { const c = document.createElement('canvas'); c.width = w; c.height = h; draw(c.getContext('2d'), w, h); return c; }
function tex(c, { srgb = true, repeat = null } = {}) {
  const t = new THREE.CanvasTexture(c); if (srgb) t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  if (repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(...repeat); }
  return t;
}

// ───────────────────────── Renderer & Pipeline ─────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1); renderer.setSize(W, H);
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
renderer.localClippingEnabled = true;
document.body.prepend(renderer.domElement);

const rtScene = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
const rtAcc = [0, 1].map(() => new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, depthBuffer: false }));
const quadCam = new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1);
const QUAD_VS = `varying vec2 vUv; void main(){ vUv = uv; gl_Position = vec4(position.xy, 0., 1.); }`;
const accumMat = new THREE.ShaderMaterial({
  uniforms: { tex: { value: null }, prev: { value: null }, k: { value: 1 }, first: { value: 1 } }, vertexShader: QUAD_VS,
  fragmentShader: `uniform sampler2D tex, prev; uniform float k, first; varying vec2 vUv;
    void main(){ vec3 p = first > .5 ? vec3(0.) : texture2D(prev, vUv).rgb; gl_FragColor = vec4(p + texture2D(tex, vUv).rgb * k, 1.); }`,
  blending: THREE.NoBlending, depthTest: false, depthWrite: false,
});
const postMat = new THREE.ShaderMaterial({
  uniforms: {
    tex: { value: null }, uTime: { value: 0 }, uRes: { value: new THREE.Vector2(W, H) },
    uChroma: { value: 0 }, uVig: { value: 0 }, uGrain: { value: 0 }, uFlash: { value: 0 }, uExposure: { value: 1 },
    uSat: { value: 1 }, uZoom: { value: 0 }, uFade: { value: 0 }, uContrast: { value: 1 }, uWarm: { value: 0 },
    uSun: { value: new THREE.Vector2(.5, .5) }, uSunAmt: { value: 0 },
  },
  vertexShader: QUAD_VS,
  fragmentShader: `
    uniform sampler2D tex; uniform vec2 uRes, uSun; uniform float uTime, uChroma, uVig, uGrain, uFlash, uExposure, uSat, uZoom, uFade, uContrast, uWarm, uSunAmt;
    varying vec2 vUv;
    vec3 aces(vec3 x){ const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.,1.); }
    float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    vec3 samp(vec2 uv){ vec2 d = (uv - 0.5) * uChroma; return vec3(texture2D(tex, uv + d).r, texture2D(tex, uv).g, texture2D(tex, uv - d).b); }
    void main(){
      vec2 uv = vUv; vec3 col;
      if (uZoom > 0.001) { float tot = 0.; col = vec3(0.);
        for (int i = 0; i < 10; i++) { float k = float(i) / 9.; vec2 u2 = 0.5 + (uv - 0.5) * (1.0 - uZoom * k); float w = 1.0 - k * 0.6; col += samp(u2) * w; tot += w; }
        col /= tot; } else col = samp(uv);
      if (uSunAmt > 0.) { // Sonnen-Glare, verdeckt wenn die Sonne hinter etwas steht
        float vis = smoothstep(2.0, 6.0, dot(texture2D(tex, uSun).rgb, vec3(.3,.6,.1)));
        vec2 d = (uv - uSun) * vec2(1., uRes.y / uRes.x);
        float r = length(d);
        col += vec3(1., .72, .42) * (exp(-r * 7.) * .9 + exp(-r * 2.2) * .22) * uSunAmt * vis;
        col += vec3(1., .8, .55) * exp(-abs(d.y) * 160.) * exp(-abs(d.x) * 2.5) * .55 * uSunAmt * vis;
      }
      col *= uExposure;
      col.r *= 1.0 + uWarm * 0.08; col.b *= 1.0 - uWarm * 0.1;
      col = aces(col); col = pow(col, vec3(1.0 / 2.2));
      float l = dot(col, vec3(0.299, 0.587, 0.114)); col = mix(vec3(l), col, uSat);
      col = (col - 0.5) * uContrast + 0.5;
      float v = smoothstep(0.95, 0.25, length((uv - 0.5) * vec2(1.0, 1.15))); col *= mix(1.0, v, uVig);
      col += (hash(uv * uRes + fract(uTime * 7.31) * 100.) - 0.5) * uGrain;
      col = mix(col, vec3(1.0), uFlash); col *= 1.0 - uFade;
      gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
    }`,
  depthTest: false, depthWrite: false,
});
const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), accumMat);
const quadScene = new THREE.Scene(); quadScene.add(quad);

// ───────────────────────── Szene, Licht, Himmel ─────────────────────────
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(35, W / H, 0.05, 1200);
const sunDir = v3(-0.78, 0.30, -0.55).normalize();
const sun = new THREE.DirectionalLight(0xffd2a2, 4.6);
sun.castShadow = true; sun.shadow.mapSize.set(2048, 2048); sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
const hemi = new THREE.HemisphereLight(0x8fb2ff, 0x5a3a22, .75); scene.add(hemi);
function shadowAround(c, size = 14) {
  const sc = sun.shadow.camera; sc.left = -size; sc.right = size; sc.top = size; sc.bottom = -size; sc.near = 1; sc.far = 200; sc.updateProjectionMatrix();
  sun.target.position.copy(c); sun.position.copy(c).addScaledVector(sunDir, 80);
}
const skyMat = new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false, uniforms: { sunDir: { value: sunDir } },
  vertexShader: `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`,
  fragmentShader: `uniform vec3 sunDir; varying vec3 vDir;
    void main(){ vec3 d = normalize(vDir); float h = d.y;
      vec3 zen = vec3(0.07, 0.15, 0.38), hor = vec3(1.5, 0.62, 0.26);
      vec3 col = mix(hor, zen, pow(clamp(h + 0.02, 0., 1.), 0.45));
      float cl = sin(d.x * 9. + d.z * 4.) * sin(d.z * 7. - d.x * 3.) * .5 + .5; // weiche Wolkenbänder
      col = mix(col, col * vec3(1.25, .85, .75), smoothstep(.55, .9, cl) * smoothstep(.02, .15, h) * smoothstep(.45, .2, h) * .6);
      col = mix(col, vec3(0.3, 0.19, 0.12), clamp(-h * 5., 0., 1.));
      float s = max(dot(d, sunDir), 0.);
      col += vec3(1.0, 0.5, 0.2) * pow(s, 5.) * 1.0 + vec3(1.0, 0.75, 0.45) * pow(s, 80.) * 3.0 + vec3(1.0, 0.9, 0.7) * pow(s, 1500.) * 40.;
      gl_FragColor = vec4(col, 1.); }`,
});
const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 32, 16), skyMat); sky.renderOrder = -1; scene.add(sky);
// Umgebung für Spiegelungen (Sonnenuntergang im Lack und in den Scheiben)
const pmrem = new THREE.PMREMGenerator(renderer);
const envScene = new THREE.Scene(); envScene.add(new THREE.Mesh(new THREE.SphereGeometry(100, 48, 24), skyMat));
const ENV = pmrem.fromScene(envScene, 0.01, 0.1, 500).texture;

// ───────────────────────── Grime-Shader (Schmutz, Kratzer, Staub, Relief) ─────────────────────────
const GRIME_GLSL = `
varying vec3 vWPos; varying vec3 vLPos;
float gh31(vec3 p){ p = fract(p * 0.3183099 + .1); p *= 17.0; return fract(p.x * p.y * p.z * (p.x + p.y + p.z)); }
float gn3(vec3 x){ vec3 i = floor(x); vec3 f = fract(x); f = f * f * (3. - 2. * f);
  return mix(mix(mix(gh31(i), gh31(i + vec3(1,0,0)), f.x), mix(gh31(i + vec3(0,1,0)), gh31(i + vec3(1,1,0)), f.x), f.y),
             mix(mix(gh31(i + vec3(0,0,1)), gh31(i + vec3(1,0,1)), f.x), mix(gh31(i + vec3(0,1,1)), gh31(i + vec3(1,1,1)), f.x), f.y), f.z); }
float gfbm(vec3 p){ float s = 0., a = .5; for (int i = 0; i < 4; i++) { s += a * gn3(p); p = p * 2.03 + vec3(1.7, 9.2, 3.1); a *= .5; } return s; }
vec3 gBump(vec3 sp, vec3 sn, float h, float k){
  vec3 dx = dFdx(sp), dy = dFdy(sp); vec3 r1 = cross(dy, sn), r2 = cross(sn, dx); float det = dot(dx, r1);
  vec2 dh = vec2(dFdx(h), dFdy(h)) * k; vec3 g = sign(det) * (dh.x * r1 + dh.y * r2);
  return normalize(abs(det) * sn - g); }
`;
function grime(mat, o = {}) {
  const G = { mud: 1, dust: 1, wear: 1, vary: .18, bump: .025, mudLine: 1.0, scale: 1, seed: 0, ...o };
  mat.onBeforeCompile = (sh) => {
    sh.vertexShader = sh.vertexShader
      .replace('#include <common>', '#include <common>\nvarying vec3 vWPos; varying vec3 vLPos;')
      .replace('#include <project_vertex>', `#include <project_vertex>
        vLPos = transformed; vec4 gw = vec4(transformed, 1.0);
        #ifdef USE_INSTANCING
          gw = instanceMatrix * gw;
        #endif
        vWPos = (modelMatrix * gw).xyz;`);
    sh.fragmentShader = sh.fragmentShader
      .replace('#include <common>', '#include <common>\n' + GRIME_GLSL)
      .replace('#include <normal_fragment_maps>', `#include <normal_fragment_maps>
        vec3 gp = vLPos * ${fx(G.scale)} + vec3(${fx(G.seed)});
        float gN1 = gfbm(gp * 1.7), gN2 = gfbm(gp * 7.0 + 4.0);
        float gMud = smoothstep(${fx(G.mudLine + .3)}, ${fx(G.mudLine - .5)}, vWPos.y + (gN1 - .5) * 1.2) * ${fx(G.mud)};
        float gScr = smoothstep(.71, .78, gfbm(gp * vec3(34., 3.5, 34.))) * ${fx(G.wear)};
        vec3 gWN = normalize((vec4(normal, 0.) * viewMatrix).xyz);
        float gDust = smoothstep(.5, .95, gWN.y) * ${fx(G.dust)} * (.4 + .6 * gN1);
        diffuseColor.rgb *= 1.0 - ${fx(G.vary)} + 2.0 * ${fx(G.vary)} * gN1;
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.40, .38, .35), gScr * .55);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.55, .44, .32), gDust * .5);
        diffuseColor.rgb = mix(diffuseColor.rgb, vec3(.15, .095, .055) * (.55 + .9 * gN2), clamp(gMud * 1.25, 0., .93));
        roughnessFactor = mix(roughnessFactor, .97, clamp(max(gMud, gDust * .8), 0., 1.));
        roughnessFactor = mix(roughnessFactor, .4, gScr * .4);
        normal = gBump(-vViewPosition, normal, gMud * gN2 * 2.0 + gN2 * .25 + gScr * .3, ${fx(G.bump)});`);
  };
  mat.customProgramCacheKey = () => 'grime' + JSON.stringify(G);
  return mat;
}

// ───────────────────────── Texturen ─────────────────────────
await document.fonts.load('120px Anton'); await document.fonts.load('600 60px Inter');
const dirtCanvas = canvas(512, 512, (g, N) => {
  const img = g.createImageData(N, N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const n = fbm(x / 64, y / 64, 4, 8), m = vnoise(x / 5, y / 5, N / 5 | 0);
    const v = .62 + .75 * (n - .5) + .22 * (m - .5), i = (y * N + x) * 4;
    img.data[i] = 128 * v; img.data[i + 1] = 94 * v; img.data[i + 2] = 64 * v; img.data[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  for (let k = 0; k < 1100; k++) { const x = rnd(k, 1) * N, y = rnd(k, 2) * N, r = .6 + rnd(k, 3) * 2.0, l = 45 + rnd(k, 4) * 70;
    g.fillStyle = `rgba(${l + 22},${l + 10},${l - 6},0.6)`; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill(); }
});
const dirtTex = tex(dirtCanvas, { repeat: [64, 64] });
const dirtBump = tex(dirtCanvas, { srgb: false, repeat: [64, 64] });
const stripes = (c1, c2, w = 512, h = 64, s = 48) => canvas(w, h, (g) => { g.fillStyle = c1; g.fillRect(0, 0, w, h); g.fillStyle = c2;
  for (let x = -h; x < w + h; x += s * 2) { g.beginPath(); g.moveTo(x, h); g.lineTo(x + s, h); g.lineTo(x + s + h, 0); g.lineTo(x + h, 0); g.fill(); } });
const chevronTex = tex(stripes('#f2b200', '#111'));
const brandCanvas = (text, fg, bg, w = 1024, h = 160, font = 'Anton', size = .78) => canvas(w, h, (g) => {
  if (bg) { g.fillStyle = bg; g.fillRect(0, 0, w, h); }
  g.fillStyle = fg; g.font = `${h * size}px ${font}`; g.textAlign = 'center'; g.textBaseline = 'middle'; g.letterSpacing = '8px'; g.fillText(text, w / 2, h / 2 + 4);
});
const brandTex = tex(brandCanvas(BRAND, '#111', null));
const bannerTex = tex(canvas(1024, 300, (g, w, h) => {
  g.fillStyle = '#F5B800'; g.fillRect(0, 0, w, h); g.fillStyle = '#111'; g.fillRect(0, h - 40, w, 40);
  g.font = '150px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.letterSpacing = '10px'; g.fillText(BRAND, w / 2, 105);
  g.font = '600 46px Inter'; g.letterSpacing = '1px'; g.fillText('Erdarbeiten · Fundamente · Pflaster', w / 2, 210);
}));
const grilleTex = tex(canvas(256, 128, (g, w, h) => { g.fillStyle = '#2a2a2a'; g.fillRect(0, 0, w, h); g.fillStyle = '#0b0b0b'; for (let x = 8; x < w; x += 16) g.fillRect(x, 6, 8, h - 12); }));
const meshTex = tex(canvas(256, 256, (g, w) => { g.strokeStyle = '#d8d8d8'; g.lineWidth = 3; for (let i = 0; i <= w; i += 32) { g.beginPath(); g.moveTo(i, 0); g.lineTo(i, w); g.stroke(); g.beginPath(); g.moveTo(0, i); g.lineTo(w, i); g.stroke(); } }), { repeat: [1, 1] });
const paverTex = tex(canvas(256, 256, (g, w) => { g.fillStyle = '#262626'; g.fillRect(0, 0, w, w);
  for (let y = 0; y < 8; y++) for (let x = 0; x < 4; x++) { const l = 95 + rnd(x + y * 9, 3) * 40; g.fillStyle = `rgb(${l},${l},${l - 4})`; g.fillRect(x * 64 + (y % 2) * 32 - 32 + 3, y * 32 + 3, 58, 26); } }));
const imprintTex = tex(canvas(64, 64, (g, w) => { g.fillStyle = 'rgba(40,26,16,0.0)'; g.fillRect(0, 0, w, w);
  const gr = g.createLinearGradient(0, 0, w, 0); gr.addColorStop(0, 'rgba(45,30,18,0)'); gr.addColorStop(.12, 'rgba(45,30,18,.55)'); gr.addColorStop(.88, 'rgba(45,30,18,.55)'); gr.addColorStop(1, 'rgba(45,30,18,0)');
  g.fillStyle = gr; g.fillRect(0, 0, w, w); g.fillStyle = 'rgba(25,15,8,.6)'; g.fillRect(4, 26, w - 8, 12); }), { repeat: [1, 160] });
const blobTex = tex(canvas(256, 256, (g, w) => { const gr = g.createRadialGradient(w / 2, w / 2, 0, w / 2, w / 2, w / 2); gr.addColorStop(0, 'rgba(0,0,0,.85)'); gr.addColorStop(.55, 'rgba(0,0,0,.45)'); gr.addColorStop(1, 'rgba(0,0,0,0)'); g.fillStyle = gr; g.fillRect(0, 0, w, w); }));

// ───────────────────────── Materialien ─────────────────────────
const MAT = {
  yellow: grime(new THREE.MeshPhysicalMaterial({ color: 0xf0b000, roughness: .42, metalness: .05, clearcoat: .55, clearcoatRoughness: .3 }), { mudLine: .8, mud: .8, seed: 1 }),
  yellowArm: grime(new THREE.MeshPhysicalMaterial({ color: 0xeaa800, roughness: .45, metalness: .05, clearcoat: .45, clearcoatRoughness: .35 }), { mudLine: 1.6, mud: 1.3, seed: 2 }),
  bucket: grime(new THREE.MeshPhysicalMaterial({ color: 0xe0a000, roughness: .55, metalness: .1, clearcoat: .2 }), { mudLine: 99, mud: .75, wear: 2.2, seed: 3, bump: .035 }),
  black: grime(new THREE.MeshStandardMaterial({ color: 0x1c1c1c, roughness: .6, metalness: .3 }), { seed: 4 }),
  steel: grime(new THREE.MeshStandardMaterial({ color: 0x4a4744, roughness: .5, metalness: .75 }), { mudLine: .9, mud: 1.2, wear: 1.5, seed: 5, bump: .04 }),
  chrome: new THREE.MeshStandardMaterial({ color: 0xe8e8e8, roughness: .08, metalness: 1 }),
  rubber: grime(new THREE.MeshStandardMaterial({ color: 0x161616, roughness: .85, metalness: .1 }), { mudLine: .9, seed: 6 }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0x05090e, roughness: .04, metalness: .6, clearcoat: 1, envMapIntensity: 1.2 }),
  lamp: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff0c8, emissiveIntensity: 6 }),
  beacon: new THREE.MeshStandardMaterial({ color: 0xff7a00, emissive: 0xff6a00, emissiveIntensity: 3, roughness: .3 }),
  dirt: grime(new THREE.MeshStandardMaterial({ color: 0x6b4b30, roughness: 1 }), { mud: 0, dust: .3, wear: 0, vary: .3, bump: .06, scale: 2.5, seed: 7 }),
  concrete: grime(new THREE.MeshStandardMaterial({ color: 0xa8a39b, roughness: .92 }), { mud: .5, mudLine: .5, wear: 0, vary: .22, bump: .02, scale: .8, seed: 8 }),
  wood: grime(new THREE.MeshStandardMaterial({ color: 0x9a7246, roughness: .8 }), { mud: .4, mudLine: .3, wear: 0, seed: 9 }),
  rebar: new THREE.MeshStandardMaterial({ color: 0x6b3a22, roughness: .6, metalness: .6 }),
  cone: new THREE.MeshStandardMaterial({ color: 0xff5a10, roughness: .5 }),
  white: new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: .5 }),
  pipe: grime(new THREE.MeshStandardMaterial({ color: 0xc8581a, roughness: .45 }), { mud: .5, mudLine: .4, wear: .3, seed: 10 }),
  galv: new THREE.MeshStandardMaterial({ color: 0xb8bcc0, roughness: .35, metalness: .9 }),
  ground: grime(new THREE.MeshStandardMaterial({ map: dirtTex, bumpMap: dirtBump, bumpScale: 2.2, roughness: .96 }), { mud: 0, dust: 0, wear: 0, vary: .25, bump: .015, scale: .35, seed: 11 }),
  brand: new THREE.MeshStandardMaterial({ map: brandTex, alphaTest: .5, roughness: .45, polygonOffset: true, polygonOffsetFactor: -2 }),
  chevron: grime(new THREE.MeshStandardMaterial({ map: chevronTex, roughness: .5, polygonOffset: true, polygonOffsetFactor: -2 }), { mudLine: .9, seed: 12 }),
  banner: new THREE.MeshStandardMaterial({ map: bannerTex, roughness: .7, side: THREE.DoubleSide }),
  grille: new THREE.MeshStandardMaterial({ map: grilleTex, roughness: .6, metalness: .4, polygonOffset: true, polygonOffsetFactor: -2 }),
  fenceMesh: new THREE.MeshStandardMaterial({ map: meshTex, alphaTest: .4, side: THREE.DoubleSide, metalness: .8, roughness: .4, color: 0xcccccc }),
  pavers: grime(new THREE.MeshStandardMaterial({ map: paverTex, roughness: .85 }), { mud: 0, wear: 0, vary: .1, seed: 13 }),
  imprint: new THREE.MeshStandardMaterial({ map: imprintTex, transparent: true, depthWrite: false, roughness: 1, polygonOffset: true, polygonOffsetFactor: -1 }),
  blob: new THREE.MeshBasicMaterial({ map: blobTex, transparent: true, depthWrite: false, color: 0x000000, opacity: .7 }),
};
// Bauplan-Look
const scanPlane = new THREE.Plane(v3(0, -1, 0), 1000);
const BP = {
  fill: new THREE.MeshBasicMaterial({ color: 0x0b1e33, polygonOffset: true, polygonOffsetFactor: 1, polygonOffsetUnits: 1, clippingPlanes: [scanPlane] }),
  dim: new THREE.MeshBasicMaterial({ color: 0x7a5d10, clippingPlanes: [scanPlane] }),
  ground: new THREE.MeshBasicMaterial({ color: 0x0a1a2c }),
  hide: null,
};
const LINE = new LineMaterial({ color: 0xffc21a, linewidth: 2.3, worldUnits: false, clippingPlanes: [scanPlane] });
LINE.clipping = true;
const reg = [], lines = [], colorOnly = [], bpOnly = [];
function mk(geo, mat, { bp = BP.fill, edge = true, shadow = true, angle = 30 } = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = m.receiveShadow = shadow;
  m.userData.color = mat; m.userData.bp = bp; reg.push(m);
  if (edge && bp) { const l = new LineSegments2(new LineSegmentsGeometry().fromEdgesGeometry(new THREE.EdgesGeometry(geo, angle)), LINE); m.add(l); lines.push(l); }
  return m;
}
function inst(geo, mat, n, bp = BP.dim) { const m = new THREE.InstancedMesh(geo, mat, n); m.castShadow = m.receiveShadow = true; m.userData.color = mat; m.userData.bp = bp; reg.push(m); return m; }
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const rbox = (w, h, d, r = .08) => new RoundedBoxGeometry(w, h, d, 3, r);
const cylX = (r, len, seg = 24) => new THREE.CylinderGeometry(r, r, len, seg).rotateZ(Math.PI / 2);
function extrudeProfile(pts, depth, bevel = .03) {
  const s = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2, curveSegments: 12 });
  g.translate(0, 0, -depth / 2); g.rotateY(-Math.PI / 2); g.computeVertexNormals(); return g;
}
const plane = (w, h, mat, opts = {}) => { const m = new THREE.Mesh(new THREE.PlaneGeometry(w, h), mat); m.userData.colorOnly = true; colorOnly.push(m); m.receiveShadow = !!opts.shadow; return m; };
const dummy = new THREE.Object3D();

// ───────────────────────── Bagger ─────────────────────────
const exc = new THREE.Group(); scene.add(exc);
const TRACK_L = 4.4, TRACK_R = .46, TRACK_X = 1.12;
const hx = TRACK_L / 2 - TRACK_R, PERIM = 4 * hx + 2 * Math.PI * TRACK_R;
function stadium(L, r) { const s = new THREE.Shape(), a = L / 2 - r; s.moveTo(-a, -r); s.lineTo(a, -r); s.absarc(a, 0, r, -Math.PI / 2, Math.PI / 2, false); s.lineTo(-a, r); s.absarc(-a, 0, r, Math.PI / 2, Math.PI * 1.5, false); return s; }
function trackPoint(s) {
  s = ((s % PERIM) + PERIM) % PERIM; const arc = Math.PI * TRACK_R, st = 2 * hx;
  if (s < st) return [-hx + s, -TRACK_R, -Math.PI / 2];
  s -= st; if (s < arc) { const a = -Math.PI / 2 + s / TRACK_R; return [hx + Math.cos(a) * TRACK_R, Math.sin(a) * TRACK_R, a]; }
  s -= arc; if (s < st) return [hx - s, TRACK_R, Math.PI / 2];
  s -= st; const a = Math.PI / 2 + s / TRACK_R; return [-hx + Math.cos(a) * TRACK_R, Math.sin(a) * TRACK_R, a];
}
const SHOES = 50;
const shoeGeo = mergeGeometries([box(.7, .05, .2), box(.7, .05, .045).translate(0, .045, -.04)]);
const tracks = [];
for (const side of [-1, 1]) {
  const g = new THREE.Group(); g.position.set(side * TRACK_X, TRACK_R + .06, 0); exc.add(g);
  const sg = new THREE.ExtrudeGeometry(stadium(TRACK_L - .1, TRACK_R - .06), { depth: .5, bevelEnabled: true, bevelThickness: .03, bevelSize: .03, bevelSegments: 2, curveSegments: 16 });
  sg.translate(0, 0, -.25); sg.rotateY(-Math.PI / 2);
  g.add(mk(sg, MAT.black));
  const shoes = inst(shoeGeo, MAT.steel, SHOES); g.add(shoes);
  for (const z of [-hx, hx]) {
    const w = mk(cylX(TRACK_R - .1, .56), MAT.steel); w.position.set(0, 0, z); g.add(w);
    const hub = mk(cylX(.17, .6), MAT.yellow); hub.position.set(0, 0, z); g.add(hub);
  }
  for (let i = 0; i < 5; i++) { const r = mk(cylX(.12, .58), MAT.steel, { edge: false }); r.position.set(0, -TRACK_R + .17, -hx + .45 + i * (2 * hx - .9) / 4); g.add(r); }
  const step = mk(box(.08, .05, .4), MAT.steel, { edge: false }); step.position.set(side * .3, .35, .6); g.add(step);
  tracks.push(shoes);
}
function setTread(off) {
  for (const shoes of tracks) {
    for (let i = 0; i < SHOES; i++) {
      const [z, y, a] = trackPoint(i * PERIM / SHOES + off);
      dummy.position.set(0, y + Math.sin(a) * .03, z + Math.cos(a) * .03);
      dummy.rotation.set(Math.atan2(Math.cos(a), Math.sin(a)), 0, 0); dummy.scale.set(1, 1, 1);
      dummy.updateMatrix(); shoes.setMatrixAt(i, dummy.matrix);
    }
    shoes.instanceMatrix.needsUpdate = true;
  }
}
const frame = mk(box(1.3, .42, 3.0), MAT.black); frame.position.set(0, .58, 0); exc.add(frame);
const ring = mk(new THREE.CylinderGeometry(.95, .95, .16, 32), MAT.black); ring.position.set(0, .9, 0); exc.add(ring);
const blob = new THREE.Mesh(new THREE.PlaneGeometry(4.2, 6.2).rotateX(-Math.PI / 2), MAT.blob); blob.position.y = .03; blob.renderOrder = 1; exc.add(blob); colorOnly.push(blob);

const house = new THREE.Group(); house.position.y = .98; exc.add(house);
const deck = mk(rbox(2.6, .3, 3.0, .06), MAT.black); deck.position.set(0, .15, -.15); house.add(deck);
const body = mk(rbox(2.56, .95, 2.05, .12), MAT.yellow); body.position.set(-.08, .76, -.62); house.add(body);
const cw = mk(rbox(2.6, 1.0, .62, .26), MAT.yellow); cw.position.set(0, .66, -1.66); house.add(cw);
const hood = mk(rbox(1.5, .14, 1.3, .05), MAT.black); hood.position.set(-.45, 1.28, -.75); house.add(hood);
const exhaust = mk(new THREE.CylinderGeometry(.06, .07, .6, 12), MAT.black); exhaust.position.set(-.95, 1.6, -.4); house.add(exhaust);
const grille = plane(1.3, .55, MAT.grille); grille.position.set(-1.372, .82, -.75); grille.rotation.y = -Math.PI / 2; house.add(grille);
const chev = plane(2.3, .26, MAT.chevron); chev.position.set(0, .34, -1.975); chev.rotation.y = Math.PI; house.add(chev);
const cwBrand = plane(1.9, .3, MAT.brand); cwBrand.position.set(0, .82, -1.975); cwBrand.rotation.y = Math.PI; house.add(cwBrand);
for (const z of [-1.4, -.2]) { const p = mk(new THREE.CylinderGeometry(.02, .02, .4, 8), MAT.black, { edge: false }); p.position.set(-1.22, 1.45, z); house.add(p); }
const rail = mk(new THREE.CylinderGeometry(.02, .02, 1.3, 8).rotateX(Math.PI / 2), MAT.black, { edge: false }); rail.position.set(-1.22, 1.65, -.8); house.add(rail);
// Kabine
const cab = new THREE.Group(); cab.position.set(.78, .3, .42); house.add(cab);
const cabBody = mk(rbox(.96, 1.62, 1.38, .1), MAT.yellow); cabBody.position.set(0, .81, 0); cab.add(cabBody);
const glassF = mk(box(.82, 1.18, .02), MAT.glass, { edge: false }); glassF.position.set(0, .92, .695); cab.add(glassF);
const glassS = mk(box(.02, 1.18, 1.16), MAT.glass, { edge: false }); glassS.position.set(.485, .92, .02); cab.add(glassS);
const glassS2 = mk(box(.02, 1.0, .9), MAT.glass, { edge: false }); glassS2.position.set(-.485, .98, .12); cab.add(glassS2);
const roof = mk(rbox(1.0, .08, 1.42, .03), MAT.black); roof.position.set(0, 1.64, 0); cab.add(roof);
for (const x of [-.3, .3]) { const l = mk(box(.16, .1, .08), MAT.lamp, { edge: false, shadow: false }); l.position.set(x, 1.72, .62); cab.add(l); }
const beacon = mk(new THREE.CylinderGeometry(.07, .08, .14, 16), MAT.beacon, { edge: false }); beacon.position.set(.3, 1.75, -.45); cab.add(beacon);
const mirrorArm = mk(new THREE.CylinderGeometry(.015, .015, .5, 6).rotateZ(.9), MAT.black, { edge: false }); mirrorArm.position.set(.62, 1.35, .62); cab.add(mirrorArm);
const mirror = mk(box(.04, .26, .16), MAT.black, { edge: false }); mirror.position.set(.82, 1.48, .62); cab.add(mirror);
// Ausleger / Stiel / Löffel
const boomPivot = new THREE.Group(); boomPivot.position.set(-.2, .62, .98); house.add(boomPivot);
const BOOM_TOP = [[-.35, .32], [2.75, 1.78], [5.3, .95]];
boomPivot.add(mk(extrudeProfile([[-.25, -.28], [2.55, 1.08], [5.25, .42], [5.3, .95], [2.75, 1.78], [-.35, .32]], .52), MAT.yellowArm));
for (const x of [-.12, .12]) { // Hydraulikschläuche auf dem Ausleger
  const pts = [v3(x, .55, .25), v3(x, 1.25, 1.35), v3(x, 1.86, 2.75), v3(x, 1.38, 4.0), v3(x, 1.06, 5.0), v3(x, .95, 5.45)];
  boomPivot.add(mk(new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 40, .035, 6), MAT.rubber, { edge: false }));
}
const boomLamp = mk(box(.14, .1, .1), MAT.lamp, { edge: false, shadow: false }); boomLamp.position.set(0, 1.4, 1.3); boomPivot.add(boomLamp);
const stickPivot = new THREE.Group(); stickPivot.position.set(0, .7, 5.2); boomPivot.add(stickPivot);
stickPivot.add(mk(extrudeProfile([[-.6, .32], [-.25, .52], [2.75, .2], [2.8, -.13], [-.1, -.3], [-.6, -.02]], .4), MAT.yellowArm));
const bucketPivot = new THREE.Group(); bucketPivot.position.set(0, 0, 2.68); stickPivot.add(bucketPivot);
const BUCKET_OUT = [[0, .12], [.35, .3], [.85, .2], [1.22, -.15], [1.36, -.62], [1.24, -1.04]];
const BUCKET_IN = [[1.12, -.98], [1.2, -.6], [1.06, -.24], [.76, -.04], [.35, .03], [.05, -.06]];
bucketPivot.add(mk(extrudeProfile([...BUCKET_OUT, ...BUCKET_IN], 1.1, .02), MAT.bucket));
for (const x of [-.56, .56]) { const s = mk(extrudeProfile([...BUCKET_OUT, [.95, -.7], [.3, -.15]], .05, .01), MAT.bucket, { edge: false }); s.position.x = x; bucketPivot.add(s); }
const toothGeo = new THREE.ConeGeometry(.055, .24, 6); toothGeo.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(v3(0, 1, 0), v3(0, -1, -.25).normalize()));
for (let i = 0; i < 5; i++) { const t = mk(toothGeo, MAT.steel, { edge: false }); t.position.set(-.44 + i * .22, -1.12, 1.22); bucketPivot.add(t); }
const bucketTip = new THREE.Object3D(); bucketTip.position.set(0, -1.2, 1.2); bucketPivot.add(bucketTip);
const bucketMouth = new THREE.Object3D(); bucketMouth.position.set(0, -.6, .9); bucketPivot.add(bucketMouth);
const loadGeo = new THREE.SphereGeometry(.55, 24, 16);
{ const p = loadGeo.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const n = .8 + .4 * fbm(x * 3 + 5, z * 3 + y * 2, 3); p.setXYZ(i, x * n, y * n * .7, z * n); } loadGeo.computeVertexNormals(); }
const load = mk(loadGeo, MAT.dirt, { edge: false }); load.position.set(0, -.42, .78); bucketPivot.add(load);
for (const grp of [boomPivot, stickPivot, bucketPivot]) { const pin = mk(cylX(.09, .75), MAT.chrome, { edge: false }); grp.add(pin); }
for (const s of [-1, 1]) { const p = plane(2.3, .36, MAT.brand); p.position.set(s * .3, 1.08, 3.9); p.rotation.set(0, s * Math.PI / 2, 0); p.rotateZ(s * .27); boomPivot.add(p); }
const brandSpot = new THREE.Object3D(); brandSpot.position.set(-.3, 1.08, 3.9); boomPivot.add(brandSpot);

const ANCH = { boomA: [house, v3(-.2, .22, 1.55)], boomB: [boomPivot, v3(0, .58, 2.1)], stickA: [boomPivot, v3(0, 1.95, 2.6)], stickB: [stickPivot, v3(0, .45, -.55)], bktA: [stickPivot, v3(0, .38, .35)], bktB: [bucketPivot, v3(0, .38, -.05)] };
for (const k in ANCH) { const o = new THREE.Object3D(); o.position.copy(ANCH[k][1]); ANCH[k][0].add(o); ANCH[k] = o; }
function makeCyl(rb, rr) { const barrel = mk(new THREE.CylinderGeometry(rb, rb, 1, 16), MAT.yellowArm, { edge: false }); const rod = mk(new THREE.CylinderGeometry(rr, rr, 1, 12), MAT.chrome, { edge: false }); exc.add(barrel, rod); return { barrel, rod }; }
const CYL = [{ c: makeCyl(.12, .065), a: 'boomA', b: 'boomB', dx: .33 }, { c: makeCyl(.12, .065), a: 'boomA', b: 'boomB', dx: -.33 }, { c: makeCyl(.11, .06), a: 'stickA', b: 'stickB', dx: 0 }, { c: makeCyl(.09, .05), a: 'bktA', b: 'bktB', dx: 0 }];
const _a = v3(0, 0, 0), _b = v3(0, 0, 0), _up = v3(0, 1, 0), _q = new THREE.Quaternion(), _sw = v3(0, 0, 0);
function updateCylinders() {
  exc.updateMatrixWorld(true);
  for (const { c, a, b, dx } of CYL) {
    exc.worldToLocal(ANCH[a].getWorldPosition(_a)); exc.worldToLocal(ANCH[b].getWorldPosition(_b));
    _sw.set(dx, 0, 0).applyAxisAngle(_up, house.rotation.y); _a.add(_sw); _b.add(_sw);
    const d = _b.clone().sub(_a), L = d.length(); d.normalize(); _q.setFromUnitVectors(_up, d);
    c.barrel.scale.set(1, L * .6, 1); c.barrel.position.copy(_a).addScaledVector(d, L * .3); c.barrel.quaternion.copy(_q);
    c.rod.scale.set(1, L * .5, 1); c.rod.position.copy(_b).addScaledVector(d, -L * .25); c.rod.quaternion.copy(_q);
  }
}
const POSE = {
  rest: { boom: .25, stick: 2.05, bucket: 1.7 }, up: { boom: .62, stick: 1.25, bucket: .55 }, hit: { boom: .14, stick: 1.24, bucket: .95 },
  curl: { boom: .2, stick: 1.95, bucket: 2.15 }, high: { boom: .78, stick: 1.55, bucket: 2.1 }, raise: { boom: .98, stick: 1.2, bucket: 1.4 },
  slam: { boom: .18, stick: 1.1, bucket: .85 }, dump: { boom: .72, stick: 1.2, bucket: -.15 },
};
const state = { x: 0, z: 0, yaw: 0, swing: 0, tread: 0, load: false, ...POSE.rest };
const pose = p => Object.assign(state, p);
const blend = (a, b, t) => ({ boom: lerp(a.boom, b.boom, t), stick: lerp(a.stick, b.stick, t), bucket: lerp(a.bucket, b.bucket, t) });
function applyPose() {
  exc.position.set(state.x, 0, state.z); exc.rotation.y = state.yaw; house.rotation.y = state.swing;
  boomPivot.rotation.x = -state.boom; stickPivot.rotation.x = state.stick; bucketPivot.rotation.x = state.bucket;
  load.visible = state.load; setTread(state.tread); updateCylinders();
}
const W_POS = o => { exc.updateMatrixWorld(true); return o.getWorldPosition(v3(0, 0, 0)); };
const CAB = () => W_POS(cab).add(v3(0, 1.0, 0));

// ───────────────────────── Baustelle ─────────────────────────
const terrGeo = new THREE.PlaneGeometry(320, 320, 180, 180).rotateX(-Math.PI / 2);
{ const p = terrGeo.attributes.position;
  for (let i = 0; i < p.count; i++) { const x = p.getX(i), z = p.getZ(i), r = Math.hypot(x, z);
    const amp = THREE.MathUtils.smoothstep(r, 26, 55) * 5 + THREE.MathUtils.smoothstep(r, 80, 160) * 24;
    p.setY(i, (fbm(x / 30 + 3, z / 30 + 7, 4) - .42) * amp + (fbm(x / 3, z / 3, 2) - .5) * .1); }
  terrGeo.computeVertexNormals(); }
const ground = mk(terrGeo, MAT.ground, { bp: BP.ground, edge: false }); ground.castShadow = false; scene.add(ground);
const grid = new THREE.GridHelper(160, 160, 0x3f86c4, 0x1d4469); grid.position.y = .02; scene.add(grid); bpOnly.push(grid);
for (const x of [-TRACK_X, TRACK_X]) { const s = plane(.66, 34, MAT.imprint); s.rotation.x = -Math.PI / 2; s.position.set(x, .025, 15); scene.add(s); }
function mound(x, z, r, h, seed) {
  const g = new THREE.SphereGeometry(1, 48, 24, 0, Math.PI * 2, 0, Math.PI / 2); const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const a = p.getX(i), b = p.getY(i), c = p.getZ(i); const n = .75 + .5 * fbm(a * 2 + seed, c * 2 + seed, 3); p.setXYZ(i, a * r * n, b * h * n, c * r * n); }
  g.computeVertexNormals(); const m = mk(g, MAT.dirt, { edge: false }); m.position.set(x, -.05, z); scene.add(m); return m;
}
mound(-7, -11, 2.8, 1.7, 1); mound(10.5, -12, 3.4, 2.1, 2); mound(13, 11, 2.4, 1.3, 3); mound(-12, 13, 3.5, 2.2, 4);
// Fundament mit Schalung + Bewehrung
const found = new THREE.Group(); found.position.set(-9, 0, 4); scene.add(found);
{ const slab = mk(box(7, .32, 5.2), MAT.concrete); slab.position.y = .16; found.add(slab);
  for (const [w, d, x, z] of [[7.4, .08, 0, 2.66], [7.4, .08, 0, -2.66], [.08, 5.4, 3.66, 0], [.08, 5.4, -3.66, 0]]) { const b = mk(box(w, .42, d), MAT.wood); b.position.set(x, .21, z); found.add(b); }
  const bars = inst(new THREE.CylinderGeometry(.018, .018, 1, 6), MAT.rebar, 42); let k = 0;
  for (let i = 0; i < 24; i++) { dummy.position.set(-3.3 + i * 6.6 / 23, .4, 0); dummy.rotation.set(Math.PI / 2, 0, 0); dummy.scale.set(1, 5, 1); dummy.updateMatrix(); bars.setMatrixAt(k++, dummy.matrix); }
  for (let i = 0; i < 18; i++) { dummy.position.set(0, .43, -2.4 + i * 4.8 / 17); dummy.rotation.set(0, 0, Math.PI / 2); dummy.scale.set(1, 6.8, 1); dummy.updateMatrix(); bars.setMatrixAt(k++, dummy.matrix); }
  found.add(bars); }
// Rohbau mit Gerüst
const rohbau = new THREE.Group(); rohbau.position.set(-16, 0, -15); rohbau.rotation.y = .25; scene.add(rohbau);
{ const C = MAT.concrete, T = .3, HF = 2.8;
  const addB = (w, h, d, x, y, z) => { const b = mk(box(w, h, d), C); b.position.set(x, y, z); rohbau.add(b); };
  addB(10.6, .25, 8.6, 0, .12, 0); addB(10.6, .25, 8.6, 0, .25 + HF + .12, 0);
  for (const fl of [0, 1]) { const y0 = .25 + fl * (HF + .25), yc = y0 + HF / 2;
    // Front (z=+4.15) mit Fenster/Tür-Öffnungen
    addB(1.5, HF, T, -4.55, yc, 4.15); addB(2.2, HF, T, -.9, yc, 4.15); addB(2.0, HF, T, 3.0, yc, 4.15); addB(.9, HF, T, 4.85, yc, 4.15);
    addB(2.0, .9, T, -2.8, y0 + .45, 4.15); addB(2.0, .6, T, -2.8, y0 + HF - .3, 4.15); addB(1.5, .6, T, 1.25, y0 + HF - .3, 4.15); addB(1.5, .9, T, 1.25, y0 + .45, 4.15);
    addB(10.6, HF, T, 0, yc, -4.15); addB(T, HF, 8.6, -5.15, yc, 0); addB(T, HF, 8.6, 5.15, yc, 0); }
  const tubes = inst(new THREE.CylinderGeometry(.025, .025, 1, 6), MAT.galv, 120); let k = 0;
  const tube = (a, b) => { const d = b.clone().sub(a); dummy.position.copy(a).addScaledVector(d, .5); dummy.quaternion.setFromUnitVectors(_up, d.clone().normalize()); dummy.scale.set(1, d.length(), 1); dummy.updateMatrix(); tubes.setMatrixAt(k++, dummy.matrix); };
  for (const z of [4.9, 5.9]) { for (let x = -5; x <= 5.01; x += 2.5) tube(v3(x, 0, z), v3(x, 6.8, z)); for (const y of [.2, 2.2, 4.2, 6.2]) tube(v3(-5, y, z), v3(5, y, z)); }
  for (let x = -5; x <= 5.01; x += 2.5) for (const y of [2.2, 4.2, 6.2]) tube(v3(x, y, 4.9), v3(x, y, 5.9));
  for (let x = -5; x < 5; x += 2.5) tube(v3(x, .2, 5.9), v3(x + 2.5, 2.2, 5.9));
  tubes.count = k; rohbau.add(tubes);
  for (const y of [2.25, 4.25]) { const p = mk(box(10, .05, .95), MAT.wood, { edge: false }); p.position.set(0, y, 5.4); rohbau.add(p); } }
// Bauzaun mit Bannern
const fence = new THREE.Group(); fence.position.set(0, 0, -21); scene.add(fence);
{ const n = 14, pw = 3.45, x0 = -n * pw / 2; const frames = inst(new THREE.CylinderGeometry(.022, .022, 1, 6), MAT.galv, n * 4); let k = 0;
  const tube = (a, b) => { const d = b.clone().sub(a); dummy.position.copy(a).addScaledVector(d, .5); dummy.quaternion.setFromUnitVectors(_up, d.clone().normalize()); dummy.scale.set(1, d.length(), 1); dummy.updateMatrix(); frames.setMatrixAt(k++, dummy.matrix); };
  for (let i = 0; i < n; i++) { const xa = x0 + i * pw, xb = xa + pw - .05;
    tube(v3(xa, .15, 0), v3(xa, 2.1, 0)); tube(v3(xb, .15, 0), v3(xb, 2.1, 0)); tube(v3(xa, 2.1, 0), v3(xb, 2.1, 0)); tube(v3(xa, .15, 0), v3(xb, .15, 0));
    const m = plane(pw - .05, 1.95, MAT.fenceMesh); m.position.set((xa + xb) / 2, 1.12, 0); fence.add(m);
    const foot = mk(box(.7, .15, .25), MAT.concrete, { edge: false }); foot.position.set(xa, .075, 0); fence.add(foot);
    if (i % 3 === 1) { const b = plane(pw - .2, .95, MAT.banner); b.position.set((xa + xb) / 2, 1.3, .03); fence.add(b); } }
  fence.add(frames); }
// KG-Rohre, Pflaster-Paletten, Pylonen
{ const g = new THREE.Group(); g.position.set(8, 0, -8); g.rotation.y = .5; scene.add(g);
  const pg = new THREE.CylinderGeometry(.16, .16, 5, 20, 1, true).rotateZ(Math.PI / 2); let i = 0;
  for (const [row, cnt] of [[0, 4], [1, 3], [2, 2]]) for (let c = 0; c < cnt; c++) { const p = mk(pg, MAT.pipe, { edge: false }); p.position.set(0, .16 + row * .28, (c - (cnt - 1) / 2) * .33); g.add(p); i++; } }
for (const [x, z, r] of [[10.5, 1.5, .1], [10.8, 3.1, -.2], [12.2, 2.2, .4]]) {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = r; scene.add(g);
  const pal = mk(box(1.2, .14, 1.0), MAT.wood, { edge: false }); pal.position.y = .07; g.add(pal);
  const st = mk(box(1.15, .7, .95), MAT.pavers); st.position.y = .5; g.add(st);
}
for (const [x, z] of [[-6.5, 7], [-4, 9.5], [10, -3], [-12.5, -2.5]]) {
  const c = mk(new THREE.ConeGeometry(.2, .7, 20), MAT.cone); c.position.set(x, .35, z); scene.add(c);
  const s = mk(new THREE.CylinderGeometry(.115, .145, .12, 20), MAT.white, { edge: false }); s.position.set(x, .42, z); scene.add(s);
}

// Uhr (Top-Down beim Hi-Hat-Roll)
const clockTex = tex(canvas(2048, 2048, (g, N) => { const m = N / 2;
  const grd = g.createRadialGradient(m, m, 0, m, m, m); grd.addColorStop(0, '#ff6a00'); grd.addColorStop(.35, '#7a2500'); grd.addColorStop(.62, '#1a0800'); grd.addColorStop(1, '#000');
  g.fillStyle = grd; g.fillRect(0, 0, N, N); g.strokeStyle = '#ffc400'; g.lineWidth = 34; g.beginPath(); g.arc(m, m, N * .4, 0, 7); g.stroke(); g.lineWidth = 10; g.beginPath(); g.arc(m, m, N * .3, 0, 7); g.stroke();
  for (let i = 0; i < 60; i++) { const a = i / 60 * Math.PI * 2, r1 = N * .37, r2 = i % 5 ? N * .355 : N * .33; g.lineWidth = i % 5 ? 6 : 16; g.beginPath(); g.moveTo(m + Math.sin(a) * r1, m - Math.cos(a) * r1); g.lineTo(m + Math.sin(a) * r2, m - Math.cos(a) * r2); g.stroke(); }
  g.fillStyle = '#ffc400'; g.font = '150px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle';
  ['XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'].forEach((s, i) => { const a = i / 12 * Math.PI * 2; g.fillText(s, m + Math.sin(a) * N * .45, m - Math.cos(a) * N * .45); }); }));
const clock = new THREE.Group(); scene.add(clock); clock.visible = false;
const clockDisc = new THREE.Mesh(new THREE.CircleGeometry(9, 96).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: clockTex, color: new THREE.Color(2.2, 2.2, 2.2) }));
clockDisc.position.y = .04; clock.add(clockDisc);
const hand = new THREE.Mesh(box(.18, .02, 6.2).translate(0, 0, 2.6), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 3, .3) })); hand.position.y = .07; clock.add(hand);
// Scan-Ebene für den Bauplan-Aufbau
const scanMesh = new THREE.Mesh(new THREE.RingGeometry(3.2, 3.32, 64).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ color: new THREE.Color(2.5, 2, .4), transparent: true, opacity: .9, side: THREE.DoubleSide }));
scanMesh.visible = false; scene.add(scanMesh);

// ───────────────────────── Partikel ─────────────────────────
const MAXD = 900, MAXC = 320;
const dustGeo = new THREE.BufferGeometry();
dustGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAXD * 3), 3));
dustGeo.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array(MAXD), 1));
dustGeo.setAttribute('aAlpha', new THREE.BufferAttribute(new Float32Array(MAXD), 1));
const dustMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false, uniforms: { uScale: { value: 1000 }, uColor: { value: new THREE.Color(.75, .52, .34) } },
  vertexShader: `attribute float aSize; attribute float aAlpha; uniform float uScale; varying float vA;
    void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = min(aSize * uScale / -mv.z, 700.); vA = aAlpha * smoothstep(1.5, 5., -mv.z); }`,
  fragmentShader: `uniform vec3 uColor; varying float vA;
    void main(){ float r = length(gl_PointCoord - .5) * 2.; float a = smoothstep(1., 0., r); gl_FragColor = vec4(uColor * (0.8 + 0.4 * (1. - r)), a * a * vA); }`,
});
const dust = new THREE.Points(dustGeo, dustMat); dust.frustumCulled = false; scene.add(dust);
const chunks = inst(new THREE.DodecahedronGeometry(.055, 0), MAT.dirt, MAXC); chunks.frustumCulled = false; scene.add(chunks);
const EMIT = [];
function updateParticles(st) {
  const P = dustGeo.attributes.position.array, S = dustGeo.attributes.aSize.array, A = dustGeo.attributes.aAlpha.array; let d = 0, c = 0;
  for (const [ei, e] of EMIT.entries()) {
    const age0 = st - e.t0; if (age0 < 0 || age0 > e.life) continue; const o = e.o;
    for (let i = 0; i < e.dust && d < MAXD; i++) {
      const sd = ei * 1000 + i, a = age0 - (e.kind === 'pour' ? rnd(sd, 9) * .5 : rnd(sd, 9) * .05); if (a < 0) continue;
      const ang = rnd(sd, 1) * Math.PI * 2, el = rnd(sd, 2) * .9 + .08, sp = e.power * (1.5 + rnd(sd, 3) * 6), k = 2.2, f = (1 - Math.exp(-k * a)) / k;
      let x = o.x + Math.cos(ang) * Math.cos(el) * sp * f, z = o.z + Math.sin(ang) * Math.cos(el) * sp * f, y = o.y + Math.sin(el) * sp * f + a * .35;
      if (e.kind === 'pour') { x = o.x + (rnd(sd, 4) - .5) * .9 + (rnd(sd, 5) - .5) * a; z = o.z + (rnd(sd, 6) - .5) * .5; y = Math.max(.1, o.y - 4.9 * a * a) + a * .4; }
      P[d * 3] = x; P[d * 3 + 1] = Math.max(y, .05); P[d * 3 + 2] = z;
      S[d] = (.35 + rnd(sd, 7) * .9) * (1 + a * (e.kind === 'pour' ? 1.2 : 2.2)) * e.size;
      A[d] = Math.pow(1 - a / e.life, 2.2) * (.2 + rnd(sd, 8) * .3) * clamp(a * 30); d++;
    }
    for (let i = 0; i < e.chunks && c < MAXC; i++) {
      const sd = ei * 2000 + i + 7, a = age0 - (e.kind === 'pour' ? rnd(sd, 9) * .45 : 0); if (a < 0) continue;
      const ang = rnd(sd, 1) * Math.PI * 2, el = e.kind === 'pour' ? 0 : .5 + rnd(sd, 2) * .9, sp = e.kind === 'pour' ? .6 * rnd(sd, 3) : e.power * (2 + rnd(sd, 3) * 4.5);
      const x = o.x + Math.cos(ang) * Math.cos(el) * sp * a + (e.kind === 'pour' ? (rnd(sd, 4) - .5) * .9 : 0), z = o.z + Math.sin(ang) * Math.cos(el) * sp * a;
      const y = Math.max(.04, o.y + Math.sin(el) * sp * a - 4.9 * a * a);
      dummy.position.set(x, y, z); dummy.rotation.set(a * 9 * rnd(sd, 5), a * 7, 0); const s = (.5 + rnd(sd, 6) * 1.2) * e.size; dummy.scale.set(s, s, s); dummy.updateMatrix(); chunks.setMatrixAt(c++, dummy.matrix);
    }
  }
  for (let i = d; i < MAXD; i++) A[i] = 0;
  dustGeo.setDrawRange(0, d); dustGeo.attributes.position.needsUpdate = dustGeo.attributes.aSize.needsUpdate = dustGeo.attributes.aAlpha.needsUpdate = true;
  chunks.count = c; chunks.instanceMatrix.needsUpdate = true;
}
const SLOW1 = .32, SLOW2 = .75;
const sim = t => t < DROP ? t : t < B[15] ? DROP + (t - DROP) * SLOW1 : DROP + (B[15] - DROP) * SLOW1 + (t - B[15]) * SLOW2;
function probe(o, p) { const keep = { ...state }; pose({ x: 0, z: 0, swing: 0, ...p }); applyPose(); const v = W_POS(o); Object.assign(state, keep); applyPose(); return v; }
EMIT.push({ t0: DIG, life: 1.8, dust: 90, chunks: 45, power: 1.0, size: 1, o: probe(bucketTip, POSE.hit).setY(.15) });
EMIT.push({ t0: DROP, life: 3.2, dust: 380, chunks: 160, power: 1.9, size: 1.3, o: probe(bucketTip, POSE.slam).setY(.2) });
EMIT.push({ t0: sim(DUMP + .05), life: 3, dust: 140, chunks: 70, power: .6, size: .9, kind: 'pour', o: probe(bucketMouth, { ...POSE.dump, swing: .5 }) });

// ───────────────────────── Modus: Bauplan / Farbe ─────────────────────────
const BP_BG = new THREE.Color(0x081626), FOG_COLOR = new THREE.Fog(0xd9a06c, 35, 280), FOG_BP = new THREE.Fog(0x081626, 22, 95);
let curMode = null;
function setMode(mode) {
  if (mode === curMode) return; curMode = mode; const bp = mode === 'bp';
  for (const m of reg) { m.material = bp ? (m.userData.bp || BP.fill) : m.userData.color; m.visible = !(bp && m.userData.bp === null); }
  for (const l of lines) l.visible = bp; for (const o of colorOnly) o.visible = !bp; for (const o of bpOnly) o.visible = bp;
  sky.visible = !bp; scene.background = bp ? BP_BG : null; scene.fog = bp ? FOG_BP : FOG_COLOR;
  scene.environment = bp ? null : ENV; scene.environmentIntensity = .75; sun.castShadow = !bp;
  dustMat.uniforms.uColor.value.set(bp ? 1.1 : .75, bp ? .85 : .52, bp ? .2 : .34);
}

// ───────────────────────── Overlay ─────────────────────────
const ov = document.getElementById('ov');
let ovHTML = '';
const add = (html, cls, style) => { ovHTML += `<div class="${cls}" style="${style}">${html}</div>`; };
function typed(text, p, y, size = 92) { const n = Math.round(clamp(p) * text.length); add(`${text.slice(0, n)}<span class="cursor"></span>`, 'type', `top:${y}px;font-size:${size}px`); }
function slam(text, t, t0, y, size, cls = 'slam', dur = .13) {
  if (t < t0) return; const p = E.outExpo(inv(t0, t0 + dur, t));
  add(text, cls, `top:${y}px;font-size:${size}px;transform:scale(${1 + 1.4 * (1 - p)});filter:blur(${18 * (1 - p)}px);opacity:${clamp((t - t0) / .03)}`);
}
const tag = (t, txt = 'HAVVAMBAU&nbsp;&nbsp;/&nbsp;&nbsp;BAUPLAN') => add('● ' + txt, 'tag', `left:56px;top:150px;opacity:${.6 + .4 * (Math.floor(t * 4) % 2)}`);
const proj = p => { const v = p.clone().project(cam); return { x: (v.x * .5 + .5) * W, y: (1 - (v.y * .5 + .5)) * H }; };
function dimLine(a, b, label, off = 0) { // Maßlinie zwischen zwei Bildschirmpunkten
  let A = proj(a), Bp = proj(b); if (Bp.x < A.x) [A, Bp] = [Bp, A];
  const dx = Bp.x - A.x, dy = Bp.y - A.y, L = Math.hypot(dx, dy), ang = Math.atan2(dy, dx) * 180 / Math.PI;
  ovHTML += `<div style="position:absolute;left:${A.x}px;top:${A.y + off}px;width:${L}px;height:0;border-top:3px solid #7fd0ff;transform-origin:0 0;transform:rotate(${ang}deg)">
    <div style="position:absolute;left:-2px;top:-14px;width:3px;height:26px;background:#7fd0ff"></div><div style="position:absolute;right:-2px;top:-14px;width:3px;height:26px;background:#7fd0ff"></div>
    <div style="position:absolute;left:0;right:0;top:-58px;text-align:center;font:600 34px 'DejaVu Sans Mono',monospace;color:#bfe6ff;letter-spacing:2px">${label}</div></div>`;
}

// ───────────────────────── Post ─────────────────────────
const P = {};
function resetPost(mode) { Object.assign(P, { chroma: .0016, vig: .5, grain: .04, flash: 0, exposure: 1, sat: 1, zoom: 0, fade: 0, contrast: mode === 'bp' ? 1.1 : 1.06, warm: 0, sun: mode === 'color' }); }
const punch = (t, t0, amt = .14, d = .12) => t >= t0 ? amt * (1 - E.outCubic(inv(t0, t0 + d, t))) : 0;
const flashAt = (t, t0, amt = 1, d = .15) => t >= t0 ? amt * Math.pow(1 - inv(t0, t0 + d, t), 2) : 0;

// ───────────────────────── Kamera ─────────────────────────
function look(pos, target, fov = 35, roll = 0) { cam.position.copy(pos); cam.lookAt(target); cam.fov = fov; if (roll) cam.rotateZ(roll); }
function shake(t, amp, seed = 0) { if (amp <= 0) return; cam.rotateX(wobble(t * 2.3, seed) * amp); cam.rotateY(wobble(t * 2.1, seed + 9) * amp); cam.rotateZ(wobble(t * 1.7, seed + 4) * amp * .6); }
const whip = (t, t0, ang, d = .16) => t >= t0 ? ang * (1 - E.outCubic(inv(t0, t0 + d, t))) : 0;

// ───────────────────────── Shots ─────────────────────────
// scene(t,u): Kamera + Pose (pro Subframe). ui(t,u): Overlay + Post (einmal pro Frame, nach dem Rendern → Kamera bekannt).
const S = []; const shot = o => S.push(o);
// 1 – Hook: Bauplan zeichnet sich von unten nach oben auf
shot({ a: 0, b: B[0], mode: 'bp', mb: 1,
  scene(t, u) { pose({ ...POSE.up, swing: 0, load: false }); applyPose();
    const h = lerp(-.1, 6.4, E.outCubic(inv(.0, .6, t))); scanPlane.constant = h; scanMesh.visible = h < 6.3; scanMesh.position.set(0, h, 1.8); scanMesh.scale.setScalar(1.5);
    const a = lerp(.66, .54, u); look(v3(Math.sin(a) * 19, 3.6, Math.cos(a) * 19 + 1.8), v3(0, 2.1, 1.6), 44); },
  ui(t) { typed('Erst der Plan.', inv(.06, .5, t), 300); P.fade = 1 - inv(0, .08, t); tag(t); } });
// 2 – Seitenansicht wie eine technische Zeichnung, mit Maßlinien
shot({ a: B[0], b: B[1], mode: 'bp', mb: 1,
  scene(t, u) { pose({ ...POSE.up, swing: 0 }); applyPose(); look(v3(27, 2.6, lerp(2.6, 2.2, u)), v3(0, 2.5, 2.2), 44); },
  ui(t) { const tip = W_POS(bucketTip); dimLine(v3(0, .02, -2.3), v3(0, .02, tip.z), 'REICHWEITE 9,4 M', 60); dimLine(v3(0, 0, -3.0), v3(0, 4.4, -3.0), 'H 4,4 M');
    P.zoom = punch(t, B[0]); P.flash = flashAt(t, B[0], .3, .07); tag(t); } });
// 3 – Front, "Jedes Detail."
shot({ a: B[1], b: B[2], mode: 'bp', mb: 1,
  scene(t, u) { pose({ ...POSE.up, swing: 0 }); applyPose(); look(v3(lerp(1.6, 1.1, u), 1.8, lerp(16, 14.5, u)), v3(0, 2.4, 1.5), 38); },
  ui(t) { typed('Jedes Detail.', inv(B[1] + .02, B[1] + .22, t), 300); P.zoom = punch(t, B[1]); tag(t); } });
// 4 – von oben, Oberwagen dreht
shot({ a: B[2], b: B[3], mode: 'bp', mb: 2,
  scene(t, u) { pose({ ...POSE.up, swing: lerp(-.4, .25, E.inOutSine(u)) }); applyPose(); const a = lerp(.9, 1.25, u); look(v3(Math.sin(a) * 9, 12, Math.cos(a) * 9 + 1), v3(0, 1, 1.8), 48); },
  ui(t) { P.zoom = punch(t, B[2]); tag(t); } });
// 5 – Whip-Pan, Graben
shot({ a: B[3], b: B[5], mode: 'bp', mb: t => t < B[3] + .16 ? 5 : 1, shutter: 1 / 30,
  scene(t) { const p = t < DIG ? blend(POSE.up, POSE.hit, E.inCubic(inv(B[3], DIG, t))) : blend(POSE.hit, POSE.curl, E.inOutCubic(inv(DIG + .03, B[5], t)));
    pose({ ...p, swing: 0, load: t > DIG + .12 }); applyPose(); look(v3(9, 3.2, 15), v3(0, 1.5, 3.4), 46); cam.rotateY(whip(t, B[3], .9));
    if (t > DIG) shake(t, .025 * Math.exp(-(t - DIG) * 9), 3); },
  ui(t) { P.flash = flashAt(t, DIG, .3, .1); P.zoom = punch(t, DIG, .12); tag(t); } });
// 6 – Löffel steigt
shot({ a: B[5], b: B[6], mode: 'bp', mb: 1,
  scene(t, u) { pose({ ...blend(POSE.curl, POSE.high, E.inOutSine(u)), swing: 0, load: true }); applyPose(); look(v3(6.5, .9, 13.5), W_POS(bucketMouth).add(v3(0, -1.2, -1.5)), 44); },
  ui(t) { P.zoom = punch(t, B[5]); tag(t); } });
// 7 – Split: oben Plan, unten echt
shot({ a: B[6], b: B[8], mode: 'split', mb: 1,
  scene(t) { const u = inv(B[6], B[8], t); pose({ ...POSE.high, swing: lerp(0, 1.4, E.inOutSine(u)), load: true }); applyPose();
    if (t < B[7]) look(v3(-9.5, 3.2, 10.5), v3(0, 2.6, 1.5), 36); else look(v3(4, .8, -11), v3(0, 2.6, 0), 36); },
  ui(t) { add('Plan', 'label', 'top:110px'); add('Echt', 'label', 'top:1070px'); P.zoom = punch(t, B[6]) + punch(t, B[7]); P.flash = flashAt(t, B[6], .3, .07); P.sun = false; } });
// 8 – Rush auf den Bagger, bei 3.95 Stillstand
const RUSH_END = 3.95;
function rushScene(t) { pose({ ...POSE.high, swing: .25, load: true }); applyPose(); const p = E.outExpo(inv(B[8], RUSH_END, t));
  look(mix3(v3(22, 9, 32), v3(10, 2, 14), p), mix3(v3(0, 2, 0), v3(0, 2.6, 1.5), p), lerp(50, 44, p)); }
shot({ a: B[8], b: TL.break, mode: 'bp', mb: t => t < B[8] + .2 ? 5 : 1, shutter: 1 / 30, scene: rushScene, ui(t) { P.zoom = .25 * (1 - inv(B[8], B[8] + .25, t)); tag(t); } });
// 9 – Break: Freeze
shot({ a: TL.break, b: ROLL[0], mode: 'bp', mb: 1, scene: () => rushScene(RUSH_END),
  ui(t) { P.sat = .35; P.exposure = .7; P.vig = 1; P.contrast = 1.25; P.grain = .08; P.flash = flashAt(t, TL.break, .4, .05); } });
// 10 – Hi-Hat-Roll: Draufsicht auf der Uhr
const tickIdx = t => ROLL.filter(x => x <= t).length;
const tickEase = (t, step) => { const i = tickIdx(t); if (!i) return 0; return (i - 1 + E.outExpo(inv(ROLL[i - 1], ROLL[i - 1] + .05, t))) * step; };
shot({ a: ROLL[0], b: B[12], mode: 'bp', mb: 1,
  scene(t) { pose({ ...POSE.rest, swing: tickEase(t, Math.PI / 6), load: false }); applyPose(); clock.visible = true; hand.rotation.y = -tickEase(t, Math.PI / 6);
    cam.up.set(0, 0, -1); look(v3(0, lerp(17, 11.5, tickEase(t, 1 / ROLL.length)), .001), v3(0, 0, 0), 40, tickEase(t, .06)); },
  ui(t) { const i = tickIdx(t); P.flash = i ? flashAt(t, ROLL[i - 1], .15, .06) : 0; P.zoom = i ? punch(t, ROLL[i - 1], .06, .06) : 0; P.vig = .8; } });
// 11 – Spannung: Low-Angle, "Dann…", dunkel → schwarz vor dem Drop
shot({ a: B[12], b: DROP, mode: 'bp', mb: 1,
  scene(t, u) { pose({ ...blend(POSE.high, POSE.raise, E.inOutSine(u)), swing: 0, load: false }); applyPose();
    look(v3(lerp(1.6, .8, u), lerp(.45, .75, u), lerp(13, 10, E.inQuad(u))), v3(0, lerp(2.4, 3.2, u), 1), lerp(42, 36, u)); shake(t, .012 * E.inQuad(u), 5);
    LINE.opacity = 1; },
  ui(t, u) { typed('Dann …', inv(B[12] + .05, B[12] + .3, t), 300, 110); P.exposure = lerp(1, .6, u); P.zoom = .12 * E.inQuad(u) + punch(t, B[12]); P.fade = inv(5.63, 5.7, t); P.chroma = .0016 + .005 * u; } });
// 12 – DROP: echt, Einschlag, Staubexplosion in Zeitlupe
shot({ a: DROP, b: B[15], mode: 'color', mb: 3, shutter: 1 / 40,
  scene(t, u) { pose({ ...POSE.slam, swing: 0, load: false }); applyPose(); look(v3(lerp(7.6, 7.1, u), .6, lerp(16.8, 15.8, u)), v3(-.3, 1.7, 3.4), 48); shake(t, .045 * Math.exp(-(t - DROP) * 6), 11); },
  ui(t) { P.flash = flashAt(t, DROP, 1, .16); P.chroma = .0016 + punch(t, DROP, .014, .3); P.zoom = punch(t, DROP, .25, .2); P.warm = .5; slam(BRAND, t, DROP, 300, 196); } });
// 13 – schneller Orbit
shot({ a: B[15], b: B[16], mode: 'color', mb: t => t < B[15] + .15 ? 5 : 2, shutter: 1 / 30,
  scene(t, u) { pose({ ...blend(POSE.slam, POSE.up, E.inOutSine(u) * .5), swing: 0 }); applyPose(); const a = lerp(-.5, 1.9, E.outCubic(u)); look(v3(Math.sin(a) * 14, 2.4, Math.cos(a) * 14 + 1.5), v3(0, 2.0, 1.5), 46); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[15]); } });
// 14 – Schriftzug-Makro am Ausleger
shot({ a: B[16], b: B[17], mode: 'color', mb: 2,
  scene(t, u) { pose({ ...POSE.up, swing: 0 }); applyPose(); const b = W_POS(brandSpot);
    look(b.clone().add(v3(-2.8, lerp(-.5, .1, u), lerp(1.6, -.6, E.inOutSine(u)))), b.clone().add(v3(0, 0, lerp(.5, -.3, u))), 30); shake(t, .003, 2); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[16]); P.flash = flashAt(t, B[16], .2, .06); } });
// 15 – Silhouette gegen die Sonne
shot({ a: B[17], b: B[18], mode: 'color', mb: 2,
  scene(t, u) { pose({ ...blend(POSE.slam, POSE.raise, E.inOutSine(u)), swing: 0, load: true }); applyPose(); look(v3(12.5, .5, 9.5), v3(0, 2.8, 0), 44); },
  ui(t) { P.warm = .7; P.zoom = punch(t, B[17]); P.exposure = 1.05; } });
// 16 – Auskippen
shot({ a: B[18], b: B[19], mode: 'color', mb: 2,
  scene(t) { const op = E.outCubic(inv(B[18], B[18] + .2, t)); pose({ ...blend(POSE.high, POSE.dump, op), swing: .5, load: op < .55 }); applyPose();
    const m = W_POS(bucketMouth); look(m.clone().add(v3(-7.5, 2.6, 8.5)), m.clone().add(v3(0, -1.6, 0)), 42); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[18]); } });
// 17 – Whip-Pan + Kran-Rückfahrt über die Baustelle
shot({ a: B[19], b: B[21], mode: 'color', noDust: true, mb: t => t < B[19] + .16 ? 5 : 2, shutter: 1 / 30,
  scene(t, u) { pose({ ...POSE.raise, swing: .3, load: false }); applyPose(); const p = E.inOutCubic(u); shadowAround(v3(-4, 0, -2), 26);
    look(mix3(v3(3.5, 2.2, 9.5), v3(11, 9, 18), p), mix3(v3(0, 1.8, 0), v3(-4, 1, -3), p), lerp(34, 42, p)); cam.rotateY(whip(t, B[19], -1.0)); },
  ui(t) { P.warm = .5; slam('WIR SCHAFFEN', t, B[19] + .05, 250, 140, 'slam white'); slam('DIE GRUNDLAGE.', t, B[20], 410, 150); P.zoom = punch(t, B[20], .1); } });
// 18 – Logo-Build
shot({ a: B[21], b: 99, mode: 'logo', mb: 1, scene() {}, ui: logoUI });
function logoUI(t) {
  const T0 = B[21], wipe = E.outCubic(inv(T0, T0 + .14, t)) * 1400;
  const zoom = 1 + .04 * inv(T0, TL.duration, t) + punch(t, TL.end_hits[1], .04, .2) + punch(t, TL.end_hits[2], .03, .2);
  let h = `<div style="position:absolute;inset:0;background:#fff;clip-path:circle(${wipe}px at 50% 50%)"></div><div style="position:absolute;inset:0;transform:scale(${zoom});transform-origin:50% 44%">`;
  const drop = (t0, y0) => { const p = E.outBack(inv(t0, t0 + .16, t)); return [y0 * (1 - p), clamp((t - t0) * 25)]; };
  const [y1, o1] = drop(T0 + .03, -500), [y2, o2] = drop(T0 + .11, -500), pb = E.outBack(inv(T0 + .2, T0 + .34, t)), cx = 540, cy = 760;
  h += `<div style="position:absolute;left:${cx - 120}px;top:${cy - 130 + y1}px;width:72px;height:260px;background:#F5B800;border-radius:10px;opacity:${o1}"></div>`;
  h += `<div style="position:absolute;left:${cx + 48}px;top:${cy - 130 + y2}px;width:72px;height:260px;background:#F5B800;border-radius:10px;opacity:${o2}"></div>`;
  h += `<div style="position:absolute;left:${cx - 120}px;top:${cy - 26}px;width:240px;height:52px;background:#111;border-radius:8px;transform:scaleX(${pb});transform-origin:0 50%"></div>`;
  h += `<div style="position:absolute;left:${cx - 160}px;top:${cy + 150}px;width:320px;height:14px;background:#111;border-radius:7px;transform:scaleX(${E.outCubic(inv(T0 + .28, T0 + .42, t))})"></div>`;
  const w0 = TL.end_hits[0]; let letters = '';
  [...BRAND].forEach((ch, i) => { const p = E.outCubic(inv(w0 + i * .022, w0 + i * .022 + .14, t)); letters += `<span style="display:inline-block;transform:translateY(${(1 - p) * 110}%)">${ch}</span>`; });
  h += `<div class="logo-word" style="left:0;right:0;text-align:center;top:1010px;overflow:hidden;height:190px;line-height:190px">${letters}</div>`;
  const s1 = TL.end_hits[1], p1 = E.outCubic(inv(s1, s1 + .2, t)), s2 = TL.end_hits[2], p2 = E.outCubic(inv(s2, s2 + .2, t));
  h += `<div class="logo-sub" style="left:0;right:0;text-align:center;top:${1230 + 30 * (1 - p1)}px;opacity:${p1}">Erdarbeiten · Fundamente · Pflaster</div>`;
  h += `<div class="logo-small" style="left:0;right:0;text-align:center;top:${1320 + 30 * (1 - p2)}px;opacity:${p2}"><span class="hl">Augsburg &amp; Umgebung</span>&nbsp;&nbsp;havvambau.de</div></div>`;
  ovHTML += h; P.grain = 0; P.vig = 0; P.chroma = 0;
}

// ───────────────────────── Frame rendern ─────────────────────────
const FPS = TL.fps;
function renderView(mode, x, y, w, h) {
  setMode(mode); cam.aspect = w / h; cam.updateProjectionMatrix(); sky.position.copy(cam.position);
  dust.visible = mode !== 'bp' && !curShot?.noDust; chunks.visible = mode !== 'bp';
  dustMat.uniforms.uScale.value = h / (2 * Math.tan(THREE.MathUtils.degToRad(cam.fov / 2)));
  LINE.resolution.set(w, h);
  rtScene.viewport.set(x, y, w, h); rtScene.scissor.set(x, y, w, h); rtScene.scissorTest = true;
  renderer.setRenderTarget(rtScene); renderer.render(scene, cam);
}
function renderScene(sh, t) {
  cam.up.set(0, 1, 0); clock.visible = false; scanMesh.visible = false; scanPlane.constant = 1000; shadowAround(v3(0, 0, 1.5), 13);
  sh.scene(t, inv(sh.a, sh.b, t)); updateParticles(sim(t));
  if (sh.mode === 'split') {
    const c = { p: cam.position.clone(), q: cam.quaternion.clone() };
    renderView('bp', 0, H / 2, W, H / 2); cam.position.copy(c.p); cam.quaternion.copy(c.q); renderView('color', 0, 0, W, H / 2);
  } else renderView(sh.mode, 0, 0, W, H);
  cam.aspect = W / H; cam.updateProjectionMatrix();
}
function sunUniform() {
  const s = cam.position.clone().addScaledVector(sunDir, 500); const inFront = s.clone().sub(cam.position).dot(cam.getWorldDirection(v3(0, 0, 0))) > 0;
  const p = s.project(cam); postMat.uniforms.uSun.value.set(p.x * .5 + .5, p.y * .5 + .5);
  return inFront && Math.abs(p.x) < 1.3 && Math.abs(p.y) < 1.3 ? 1 : 0;
}
let curShot = null;
window.renderFrame = (t) => {
  const sh = curShot = S.find(s => t >= s.a && t < s.b) || S[S.length - 1];
  resetPost(sh.mode); ovHTML = '';
  if (sh.mode === 'logo') {
    sh.ui(t, 0); renderer.setRenderTarget(null); renderer.setClearColor(0x000000); renderer.clear();
  } else {
    const n = window.FORCE_MB ?? (typeof sh.mb === 'function' ? sh.mb(t) : sh.mb);
    const shutter = sh.shutter ?? .5 / FPS; let src = rtScene.texture;
    if (n > 1) {
      for (let k = 0; k < n; k++) {
        renderScene(sh, clamp(t + ((k + .5) / n - .5) * shutter, sh.a, sh.b - 1e-4));
        const dst = rtAcc[k % 2], prv = rtAcc[(k + 1) % 2];
        quad.material = accumMat; accumMat.uniforms.tex.value = rtScene.texture; accumMat.uniforms.prev.value = prv.texture; accumMat.uniforms.k.value = 1 / n; accumMat.uniforms.first.value = k === 0 ? 1 : 0;
        renderer.setRenderTarget(dst); renderer.render(quadScene, quadCam); src = dst.texture;
      }
      if (n % 2 === 0) { /* letzte Subframe-Position für Overlays */ }
    } else renderScene(sh, t);
    sh.ui(t, inv(sh.a, sh.b, t));
    const U = postMat.uniforms;
    U.tex.value = src; U.uTime.value = t; U.uChroma.value = P.chroma; U.uVig.value = P.vig; U.uGrain.value = P.grain; U.uFlash.value = clamp(P.flash);
    U.uExposure.value = P.exposure; U.uSat.value = P.sat; U.uZoom.value = P.zoom; U.uFade.value = clamp(P.fade); U.uContrast.value = P.contrast; U.uWarm.value = P.warm;
    U.uSunAmt.value = P.sun ? sunUniform() : 0;
    quad.material = postMat; renderer.setRenderTarget(null); renderer.render(quadScene, quadCam);
  }
  ov.innerHTML = ovHTML; renderer.getContext().finish();
  return sh.a;
};
window.debugRender = (o) => {
  resetPost(o.mode || 'color'); cam.up.set(0, 1, 0); clock.visible = false; scanPlane.constant = 1000; shadowAround(v3(0, 0, 1.5), o.shadow || 13);
  pose({ x: 0, z: 0, tread: 0, swing: o.swing || 0, load: !!o.load, ...(typeof o.pose === 'string' ? POSE[o.pose] : (o.pose || POSE.rest)) }); applyPose();
  updateParticles(o.t ?? -10); look(v3(...o.pos), v3(...o.target), o.fov || 35); renderView(o.mode || 'color', 0, 0, W, H); cam.aspect = W / H; cam.updateProjectionMatrix();
  const U = postMat.uniforms; U.tex.value = rtScene.texture; U.uExposure.value = 1; U.uSat.value = 1; U.uZoom.value = 0; U.uFade.value = 0; U.uFlash.value = 0; U.uContrast.value = 1.06; U.uVig.value = .4; U.uChroma.value = 0; U.uGrain.value = 0; U.uWarm.value = .5;
  U.uSunAmt.value = (o.mode || 'color') === 'color' ? sunUniform() : 0;
  quad.material = postMat; renderer.setRenderTarget(null); renderer.render(quadScene, quadCam); ov.innerHTML = ''; renderer.getContext().finish();
  return { tip: W_POS(bucketTip).toArray().map(v => +v.toFixed(2)) };
};
await document.fonts.ready;
window.ready = true;
