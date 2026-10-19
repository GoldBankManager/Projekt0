// HavvamBau Reel 01 – "Previs → Render": prozeduraler 3D-Bagger, komplett in Code.
// Bis zum Drop graue 3D-Szene (Blender-Previs-Look), ab dem Drop fertiger gelber Bagger im Sonnenuntergang,
// am Ende Logo-Build im Motion-Design-Stil. Alle Schnitte liegen auf der Beat-Map in timeline.json.
import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/addons/geometries/RoundedBoxGeometry.js';
import { RoomEnvironment } from 'three/addons/environments/RoomEnvironment.js';

const W = 1080, H = 1920;
const TL = await (await fetch('./timeline.json')).json();
const B = TL.beats, DROP = TL.drop, DIG = TL.dig_impact, DUMP = TL.dump, ROLL = TL.hat_roll;
const BRAND = 'HAVVAMBAU';

// ───────────────────────── Helfer ─────────────────────────
const clamp = (x, a = 0, b = 1) => Math.min(b, Math.max(a, x));
const lerp = (a, b, t) => a + (b - a) * t;
const inv = (a, b, x) => clamp((x - a) / (b - a));
const E = {
  outCubic: t => 1 - Math.pow(1 - t, 3),
  inCubic: t => t * t * t,
  inQuad: t => t * t,
  inOutCubic: t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2,
  outExpo: t => t >= 1 ? 1 : 1 - Math.pow(2, -10 * t),
  inExpo: t => t <= 0 ? 0 : Math.pow(2, 10 * t - 10),
  outBack: t => { const c1 = 1.9, c3 = c1 + 1; return 1 + c3 * Math.pow(t - 1, 3) + c1 * Math.pow(t - 1, 2); },
  inOutSine: t => -(Math.cos(Math.PI * t) - 1) / 2,
};
const hash = n => { const s = Math.sin(n * 127.1 + 311.7) * 43758.5453; return s - Math.floor(s); };
const rnd = (i, k) => hash(i * 1.37 + k * 17.91 + 0.123);
const wobble = (t, s = 0) => Math.sin(t * 13.1 + s) * .5 + Math.sin(t * 23.7 + s * 2.1) * .3 + Math.sin(t * 41.3 + s * 3.7) * .2;
const v3 = (x, y, z) => new THREE.Vector3(x, y, z);
const mix3 = (a, b, t) => a.clone().lerp(b, t);

function vnoise(x, y, P = 1e9) {
  const xi = Math.floor(x), yi = Math.floor(y), xf = x - xi, yf = y - yi;
  const h = (a, b) => hash(((a % P) + P) % P * 57.0 + (((b % P) + P) % P) * 131.0);
  const u = xf * xf * (3 - 2 * xf), v = yf * yf * (3 - 2 * yf);
  return lerp(lerp(h(xi, yi), h(xi + 1, yi), u), lerp(h(xi, yi + 1), h(xi + 1, yi + 1), u), v);
}
function fbm(x, y, oct = 5, P = 1e9) {
  let s = 0, a = .5, f = 1;
  for (let i = 0; i < oct; i++) { s += a * vnoise(x * f, y * f, P * f); f *= 2; a *= .5; }
  return s;
}

// ───────────────────────── Renderer & Pipeline ─────────────────────────
const renderer = new THREE.WebGLRenderer({ antialias: false, preserveDrawingBuffer: true });
renderer.setPixelRatio(1);
renderer.setSize(W, H);
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
renderer.toneMapping = THREE.NoToneMapping;
document.body.prepend(renderer.domElement);

const rtScene = new THREE.WebGLRenderTarget(W, H, { type: THREE.HalfFloatType, samples: 4 });
// Motion-Blur-Akkumulation per Ping-Pong (ohne Float-Blending, das SwiftShader nicht sauber kann)
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
  },
  vertexShader: QUAD_VS,
  fragmentShader: `
    uniform sampler2D tex; uniform vec2 uRes; uniform float uTime, uChroma, uVig, uGrain, uFlash, uExposure, uSat, uZoom, uFade, uContrast, uWarm;
    varying vec2 vUv;
    vec3 aces(vec3 x){ const float a=2.51,b=0.03,c=2.43,d=0.59,e=0.14; return clamp((x*(a*x+b))/(x*(c*x+d)+e),0.,1.); }
    float hash(vec2 p){ return fract(sin(dot(p, vec2(12.9898,78.233))) * 43758.5453); }
    vec3 samp(vec2 uv){
      vec2 d = (uv - 0.5) * uChroma;
      return vec3(texture2D(tex, uv + d).r, texture2D(tex, uv).g, texture2D(tex, uv - d).b);
    }
    void main(){
      vec2 uv = vUv; vec3 col;
      if (uZoom > 0.001) {
        float tot = 0.; col = vec3(0.);
        for (int i = 0; i < 10; i++) { float k = float(i) / 9.; vec2 u2 = 0.5 + (uv - 0.5) * (1.0 - uZoom * k); float w = 1.0 - k * 0.6; col += samp(u2) * w; tot += w; }
        col /= tot;
      } else col = samp(uv);
      col *= uExposure;
      col.r *= 1.0 + uWarm * 0.08; col.b *= 1.0 - uWarm * 0.1;
      col = aces(col);
      col = pow(col, vec3(1.0 / 2.2));
      float l = dot(col, vec3(0.299, 0.587, 0.114));
      col = mix(vec3(l), col, uSat);
      col = (col - 0.5) * uContrast + 0.5;
      float v = smoothstep(0.95, 0.25, length((uv - 0.5) * vec2(1.0, 1.15)));
      col *= mix(1.0, v, uVig);
      col += (hash(uv * uRes + fract(uTime * 7.31) * 100.) - 0.5) * uGrain;
      col = mix(col, vec3(1.0), uFlash);
      col *= 1.0 - uFade;
      gl_FragColor = vec4(clamp(col, 0., 1.), 1.);
    }`,
  depthTest: false, depthWrite: false,
});
const quad = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), accumMat);
const quadScene = new THREE.Scene(); quadScene.add(quad);

// ───────────────────────── Szene, Licht, Himmel ─────────────────────────
const scene = new THREE.Scene();
const cam = new THREE.PerspectiveCamera(35, W / H, 0.05, 1200);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

const sunDir = v3(-0.78, 0.36, -0.52).normalize();
const sun = new THREE.DirectionalLight(0xffffff, 3);
sun.castShadow = true;
sun.shadow.mapSize.set(2048, 2048);
sun.shadow.bias = -0.0004; sun.shadow.normalBias = 0.03;
scene.add(sun, sun.target);
const hemi = new THREE.HemisphereLight(0xbfd6ff, 0x5a4330, 1);
scene.add(hemi);
function shadowAround(c, size = 14) {
  const sc = sun.shadow.camera;
  sc.left = -size; sc.right = size; sc.top = size; sc.bottom = -size; sc.near = 1; sc.far = 160; sc.updateProjectionMatrix();
  sun.target.position.copy(c); sun.position.copy(c).addScaledVector(sunDir, 70);
}

const sky = new THREE.Mesh(new THREE.SphereGeometry(800, 32, 16), new THREE.ShaderMaterial({
  side: THREE.BackSide, depthWrite: false, fog: false,
  uniforms: { sunDir: { value: sunDir } },
  vertexShader: `varying vec3 vDir; void main(){ vDir = position; gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.); }`,
  fragmentShader: `uniform vec3 sunDir; varying vec3 vDir;
    void main(){ vec3 d = normalize(vDir); float h = d.y;
      vec3 zen = vec3(0.09, 0.18, 0.42), hor = vec3(1.45, 0.66, 0.30);
      vec3 col = mix(hor, zen, pow(clamp(h + 0.02, 0., 1.), 0.5));
      col = mix(col, vec3(0.32, 0.2, 0.13), clamp(-h * 5., 0., 1.));
      float s = max(dot(d, sunDir), 0.);
      col += vec3(1.0, 0.55, 0.25) * pow(s, 6.) * 0.9 + vec3(1.0, 0.8, 0.5) * pow(s, 90.) * 3.0 + vec3(1.0, 0.9, 0.7) * pow(s, 900.) * 30.;
      gl_FragColor = vec4(col, 1.); }`,
}));
sky.renderOrder = -1;
scene.add(sky);

// Boden-Textur (kachelbar)
function dirtTexture() {
  const N = 512, c = document.createElement('canvas'); c.width = c.height = N;
  const g = c.getContext('2d'), img = g.createImageData(N, N);
  for (let y = 0; y < N; y++) for (let x = 0; x < N; x++) {
    const n = fbm(x / 64, y / 64, 4, 8), m = vnoise(x / 5, y / 5, N / 5 | 0);
    const v = 0.62 + 0.75 * (n - 0.5) + 0.22 * (m - 0.5);
    const i = (y * N + x) * 4;
    img.data[i] = 128 * v; img.data[i + 1] = 94 * v; img.data[i + 2] = 64 * v; img.data[i + 3] = 255;
  }
  g.putImageData(img, 0, 0);
  for (let k = 0; k < 900; k++) { // Steinchen
    const x = rnd(k, 1) * N, y = rnd(k, 2) * N, r = 0.6 + rnd(k, 3) * 2.2, l = 60 + rnd(k, 4) * 90;
    g.fillStyle = `rgba(${l + 20},${l + 8},${l - 6},0.8)`; g.beginPath(); g.arc(x, y, r, 0, 7); g.fill();
  }
  const t = new THREE.CanvasTexture(c);
  t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(60, 60); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// ───────────────────────── Materialien (Farbe + Clay) ─────────────────────────
const MAT = {
  yellow: new THREE.MeshPhysicalMaterial({ color: 0xf2b200, roughness: .36, metalness: .1, clearcoat: .7, clearcoatRoughness: .2 }),
  black: new THREE.MeshStandardMaterial({ color: 0x1b1b1b, roughness: .55, metalness: .3 }),
  steel: new THREE.MeshStandardMaterial({ color: 0x4a4a48, roughness: .45, metalness: .8 }),
  chrome: new THREE.MeshStandardMaterial({ color: 0xe8e8e8, roughness: .07, metalness: 1 }),
  rubber: new THREE.MeshStandardMaterial({ color: 0x161616, roughness: .85, metalness: .2 }),
  glass: new THREE.MeshPhysicalMaterial({ color: 0x0a141c, roughness: .04, metalness: .3, clearcoat: 1 }),
  lamp: new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff0c8, emissiveIntensity: 6 }),
  dirt: new THREE.MeshStandardMaterial({ color: 0x5b412b, roughness: 1 }),
  concrete: new THREE.MeshStandardMaterial({ color: 0xa19d96, roughness: .9 }),
  wood: new THREE.MeshStandardMaterial({ color: 0x9a7246, roughness: .8 }),
  rebar: new THREE.MeshStandardMaterial({ color: 0x6b3a22, roughness: .6, metalness: .6 }),
  cone: new THREE.MeshStandardMaterial({ color: 0xff5a10, roughness: .5 }),
  white: new THREE.MeshStandardMaterial({ color: 0xf0f0f0, roughness: .5 }),
};
const CLAY = {
  light: new THREE.MeshStandardMaterial({ color: 0xb2b2b2, roughness: .85 }),
  mid: new THREE.MeshStandardMaterial({ color: 0x9a9a9a, roughness: .9 }),
  dark: new THREE.MeshStandardMaterial({ color: 0x585858, roughness: .9 }),
  ground: new THREE.MeshStandardMaterial({ color: 0x7c7c7c, roughness: 1 }),
};
const EDGE = new THREE.LineBasicMaterial({ color: 0x2c2c2c });
const reg = [], edges = [];
function mk(geo, mat, clay = CLAY.light, { edge = true, shadow = true } = {}) {
  const m = new THREE.Mesh(geo, mat);
  m.castShadow = m.receiveShadow = shadow;
  m.userData.color = mat; m.userData.clay = clay;
  reg.push(m);
  if (edge) { const l = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 30), EDGE); m.add(l); edges.push(l); }
  return m;
}
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const rbox = (w, h, d, r = .08) => new RoundedBoxGeometry(w, h, d, 3, r);
const cylX = (r, len, seg = 24) => new THREE.CylinderGeometry(r, r, len, seg).rotateZ(Math.PI / 2);

// Profil (x = vorwärts, y = hoch) entlang X extrudieren → Profil-x wird Welt-z
function extrudeProfile(pts, depth, bevel = .03) {
  const s = new THREE.Shape(pts.map(p => new THREE.Vector2(p[0], p[1])));
  const g = new THREE.ExtrudeGeometry(s, { depth, bevelEnabled: bevel > 0, bevelThickness: bevel, bevelSize: bevel, bevelSegments: 2, curveSegments: 12 });
  g.translate(0, 0, -depth / 2); g.rotateY(-Math.PI / 2); g.computeVertexNormals();
  return g;
}

// Schriftzug als Textur
async function brandTexture(text, color = '#111', bg = null, w = 1024, h = 160) {
  await document.fonts.load('120px Anton');
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  const g = c.getContext('2d');
  if (bg) { g.fillStyle = bg; g.fillRect(0, 0, w, h); }
  g.fillStyle = color; g.font = `${h * 0.78}px Anton`; g.textAlign = 'center'; g.textBaseline = 'middle';
  g.letterSpacing = '8px';
  g.fillText(text, w / 2, h / 2 + 4);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; t.anisotropy = 8;
  return t;
}

// ───────────────────────── Bagger ─────────────────────────
const exc = new THREE.Group(); scene.add(exc);

// Laufwerk
const TRACK_L = 4.4, TRACK_R = .46, TRACK_X = 1.12;
const hx = TRACK_L / 2 - TRACK_R, PERIM = 4 * hx + 2 * Math.PI * TRACK_R;
function stadium(L, r) {
  const s = new THREE.Shape(), a = L / 2 - r;
  s.moveTo(-a, -r); s.lineTo(a, -r); s.absarc(a, 0, r, -Math.PI / 2, Math.PI / 2, false);
  s.lineTo(-a, r); s.absarc(-a, 0, r, Math.PI / 2, Math.PI * 1.5, false);
  return s;
}
function trackPoint(s) { // Umfangsposition → (z, y, Normalen-Winkel)
  s = ((s % PERIM) + PERIM) % PERIM;
  const arc = Math.PI * TRACK_R, st = 2 * hx;
  if (s < st) return [-hx + s, -TRACK_R, -Math.PI / 2];
  s -= st; if (s < arc) { const a = -Math.PI / 2 + s / TRACK_R; return [hx + Math.cos(a) * TRACK_R, Math.sin(a) * TRACK_R, a]; }
  s -= arc; if (s < st) return [hx - s, TRACK_R, Math.PI / 2];
  s -= st; const a = Math.PI / 2 + s / TRACK_R; return [-hx + Math.cos(a) * TRACK_R, Math.sin(a) * TRACK_R, a];
}
const SHOES = 54;
const shoeGeo = box(.68, .07, .2);
const tracks = [];
for (const side of [-1, 1]) {
  const g = new THREE.Group(); g.position.set(side * TRACK_X, TRACK_R + .04, 0); exc.add(g);
  const sg = new THREE.ExtrudeGeometry(stadium(TRACK_L - .1, TRACK_R - .05), { depth: .5, bevelEnabled: true, bevelThickness: .03, bevelSize: .03, bevelSegments: 2, curveSegments: 16 });
  sg.translate(0, 0, -.25); sg.rotateY(-Math.PI / 2);
  g.add(mk(sg, MAT.rubber, CLAY.dark));
  const shoes = new THREE.InstancedMesh(shoeGeo, MAT.steel, SHOES);
  shoes.castShadow = shoes.receiveShadow = true; shoes.userData.color = MAT.steel; shoes.userData.clay = CLAY.mid; reg.push(shoes);
  g.add(shoes);
  for (const z of [-hx, hx]) { // Turas & Leitrad
    const w = mk(cylX(TRACK_R - .1, .56), MAT.steel, CLAY.mid); w.position.set(0, 0, z); g.add(w);
    const hub = mk(cylX(.16, .6), MAT.yellow, CLAY.light); hub.position.set(0, 0, z); g.add(hub);
  }
  for (let i = 0; i < 4; i++) { const r = mk(cylX(.13, .58), MAT.steel, CLAY.mid, { edge: false }); r.position.set(0, -TRACK_R + .17, -hx + .5 + i * (2 * hx - 1) / 3); g.add(r); }
  tracks.push(shoes);
}
const dummy = new THREE.Object3D();
function setTread(off) {
  for (const shoes of tracks) {
    for (let i = 0; i < SHOES; i++) {
      const [z, y, a] = trackPoint(i * PERIM / SHOES + off);
      dummy.position.set(0, y + Math.sin(a) * .035, z + Math.cos(a) * .035);
      dummy.rotation.set(Math.atan2(Math.cos(a), Math.sin(a)), 0, 0);
      dummy.updateMatrix(); shoes.setMatrixAt(i, dummy.matrix);
    }
    shoes.instanceMatrix.needsUpdate = true;
  }
}
setTread(0);
const frame = mk(box(1.3, .42, 3.0), MAT.black, CLAY.dark); frame.position.set(0, .55, 0); exc.add(frame);
const ring = mk(new THREE.CylinderGeometry(.95, .95, .16, 32), MAT.black, CLAY.dark); ring.position.set(0, .88, 0); exc.add(ring);

// Oberwagen
const house = new THREE.Group(); house.position.y = .96; exc.add(house);
const deck = mk(rbox(2.6, .3, 3.0, .06), MAT.black, CLAY.dark); deck.position.set(0, .15, -.15); house.add(deck);
const body = mk(rbox(2.56, .95, 2.05, .12), MAT.yellow); body.position.set(-.08, .76, -.62); house.add(body);
const cw = mk(rbox(2.6, 1.0, .62, .26), MAT.yellow); cw.position.set(0, .66, -1.66); house.add(cw);
const cwStripe = mk(box(2.62, .12, .5), MAT.black, CLAY.dark, { edge: false }); cwStripe.position.set(0, .3, -1.68); house.add(cwStripe);
const hood = mk(rbox(1.5, .14, 1.3, .05), MAT.black, CLAY.mid); hood.position.set(-.45, 1.28, -.75); house.add(hood);
const exhaust = mk(new THREE.CylinderGeometry(.06, .06, .55, 12), MAT.black, CLAY.dark); exhaust.position.set(-.95, 1.55, -.4); house.add(exhaust);
const rail = mk(box(.04, .04, 1.6), MAT.black, CLAY.dark, { edge: false }); rail.position.set(-1.2, 1.5, -.7); house.add(rail);
// Kabine
const cab = new THREE.Group(); cab.position.set(.78, .3, .42); house.add(cab);
const cabBody = mk(rbox(.96, 1.62, 1.38, .1), MAT.yellow); cabBody.position.set(0, .81, 0); cab.add(cabBody);
const glassF = mk(box(.82, 1.18, .02), MAT.glass, CLAY.dark, { edge: false }); glassF.position.set(0, .92, .695); cab.add(glassF);
const glassS = mk(box(.02, 1.18, 1.16), MAT.glass, CLAY.dark, { edge: false }); glassS.position.set(.485, .92, .02); cab.add(glassS);
const glassS2 = mk(box(.02, 1.0, .9), MAT.glass, CLAY.dark, { edge: false }); glassS2.position.set(-.485, .98, .12); cab.add(glassS2);
const roof = mk(rbox(1.0, .08, 1.42, .03), MAT.black, CLAY.dark); roof.position.set(0, 1.64, 0); cab.add(roof);
for (const x of [-.3, .3]) { const l = mk(box(.16, .1, .08), MAT.lamp, CLAY.light, { edge: false, shadow: false }); l.position.set(x, 1.72, .62); cab.add(l); }

// Ausleger / Stiel / Löffel
const boomPivot = new THREE.Group(); boomPivot.position.set(-.2, .62, .98); house.add(boomPivot);
const boom = mk(extrudeProfile([[-.25, -.28], [2.55, 1.08], [5.25, .42], [5.3, .95], [2.75, 1.78], [-.35, .32]], .52), MAT.yellow);
boomPivot.add(boom);
const stickPivot = new THREE.Group(); stickPivot.position.set(0, .7, 5.2); boomPivot.add(stickPivot);
const stick = mk(extrudeProfile([[-.6, .32], [-.25, .52], [2.75, .2], [2.8, -.13], [-.1, -.3], [-.6, -.02]], .4), MAT.yellow);
stickPivot.add(stick);
const bucketPivot = new THREE.Group(); bucketPivot.position.set(0, 0, 2.68); stickPivot.add(bucketPivot);
const BUCKET_OUT = [[0, .12], [.35, .3], [.85, .2], [1.22, -.15], [1.36, -.62], [1.24, -1.04]];
const BUCKET_IN = [[1.12, -.98], [1.2, -.6], [1.06, -.24], [.76, -.04], [.35, .03], [.05, -.06]];
const bucket = mk(extrudeProfile([...BUCKET_OUT, ...BUCKET_IN], 1.1, .02), MAT.yellow);
bucketPivot.add(bucket);
for (const x of [-.56, .56]) { // Seitenbleche
  const side = mk(extrudeProfile([...BUCKET_OUT, [.95, -.7], [.3, -.15]], .05, .01), MAT.yellow, CLAY.light, { edge: false });
  side.position.x = x; bucketPivot.add(side);
}
const toothGeo = new THREE.ConeGeometry(.055, .24, 6);
toothGeo.applyQuaternion(new THREE.Quaternion().setFromUnitVectors(v3(0, 1, 0), v3(0, -1, -.25).normalize()));
for (let i = 0; i < 5; i++) { const tth = mk(toothGeo, MAT.steel, CLAY.mid, { edge: false }); tth.position.set(-.44 + i * .22, -1.12, 1.22); bucketPivot.add(tth); }
const bucketTip = new THREE.Object3D(); bucketTip.position.set(0, -1.2, 1.2); bucketPivot.add(bucketTip);
const bucketMouth = new THREE.Object3D(); bucketMouth.position.set(0, -.6, .9); bucketPivot.add(bucketMouth);
// Ladung im Löffel
const loadGeo = new THREE.SphereGeometry(.55, 20, 14);
{ const p = loadGeo.attributes.position; for (let i = 0; i < p.count; i++) { const x = p.getX(i), y = p.getY(i), z = p.getZ(i); const n = .8 + .4 * fbm(x * 3 + 5, z * 3 + y * 2, 3); p.setXYZ(i, x * n, y * n * .7, z * n); } loadGeo.computeVertexNormals(); }
const load = mk(loadGeo, MAT.dirt, CLAY.mid, { edge: false }); load.position.set(0, -.42, .78); load.scale.set(1.0, 1, .95); bucketPivot.add(load);
// Bolzen
for (const [grp, z, y] of [[boomPivot, 0, 0], [stickPivot, 0, 0], [bucketPivot, 0, 0]]) {
  const pin = mk(cylX(.09, .75), MAT.chrome, CLAY.mid, { edge: false }); pin.position.set(0, y, z); grp.add(pin);
}
// Schriftzug auf dem Ausleger + Gegengewicht
const brandTex = await brandTexture(BRAND, '#111');
const brandMat = new THREE.MeshStandardMaterial({ map: brandTex, alphaTest: .5, roughness: .4, polygonOffset: true, polygonOffsetFactor: -2 });
for (const s of [-1, 1]) {
  const p = new THREE.Mesh(new THREE.PlaneGeometry(2.3, .36), brandMat);
  p.position.set(s * .3, 1.08, 3.9); p.rotation.set(0, s * Math.PI / 2, 0); p.rotateZ(s * .27);
  boomPivot.add(p); p.userData.brand = true;
}
const cwBrand = new THREE.Mesh(new THREE.PlaneGeometry(1.9, .3), brandMat);
const brandSpot = new THREE.Object3D(); brandSpot.position.set(-.3, 1.08, 3.9); boomPivot.add(brandSpot);
cwBrand.position.set(0, .82, -1.98); cwBrand.rotation.y = Math.PI; house.add(cwBrand); cwBrand.userData.brand = true;

// Hydraulikzylinder
const ANCH = {
  boomA: [house, v3(-.2, .22, 1.55)], boomB: [boomPivot, v3(0, .58, 2.1)],
  stickA: [boomPivot, v3(0, 1.95, 2.6)], stickB: [stickPivot, v3(0, .45, -.55)],
  bktA: [stickPivot, v3(0, .38, .35)], bktB: [bucketPivot, v3(0, .38, -.05)],
};
for (const k in ANCH) { const o = new THREE.Object3D(); o.position.copy(ANCH[k][1]); ANCH[k][0].add(o); ANCH[k] = o; }
function makeCyl(rb, rr) {
  const barrel = mk(new THREE.CylinderGeometry(rb, rb, 1, 16), MAT.yellow, CLAY.light, { edge: false });
  const rod = mk(new THREE.CylinderGeometry(rr, rr, 1, 12), MAT.chrome, CLAY.mid, { edge: false });
  exc.add(barrel, rod); return { barrel, rod };
}
const CYL = [
  { c: makeCyl(.12, .065), a: 'boomA', b: 'boomB', dx: .33 }, { c: makeCyl(.12, .065), a: 'boomA', b: 'boomB', dx: -.33 },
  { c: makeCyl(.11, .06), a: 'stickA', b: 'stickB', dx: 0 }, { c: makeCyl(.09, .05), a: 'bktA', b: 'bktB', dx: 0 },
];
const _a = v3(0, 0, 0), _b = v3(0, 0, 0), _up = v3(0, 1, 0), _q = new THREE.Quaternion(), _sw = v3(0, 0, 0);
function updateCylinders() {
  exc.updateMatrixWorld(true);
  for (const { c, a, b, dx } of CYL) {
    exc.worldToLocal(ANCH[a].getWorldPosition(_a)); exc.worldToLocal(ANCH[b].getWorldPosition(_b));
    _sw.set(dx, 0, 0).applyAxisAngle(_up, house.rotation.y); _a.add(_sw); _b.add(_sw);
    const d = _b.clone().sub(_a), L = d.length(); d.normalize(); _q.setFromUnitVectors(_up, d);
    const bl = L * .6, rl = L * .5;
    c.barrel.scale.set(1, bl, 1); c.barrel.position.copy(_a).addScaledVector(d, bl / 2); c.barrel.quaternion.copy(_q);
    c.rod.scale.set(1, rl, 1); c.rod.position.copy(_b).addScaledVector(d, -rl / 2); c.rod.quaternion.copy(_q);
  }
}

// Posen
const POSE = {
  rest:  { boom: .25, stick: 2.05, bucket: 1.7 },
  up:    { boom: .62, stick: 1.25, bucket: .55 },
  hit:   { boom: .14, stick: 1.24, bucket: .95 },
  curl:  { boom: .2, stick: 1.95, bucket: 2.15 },
  high:  { boom: .78, stick: 1.55, bucket: 2.1 },
  raise: { boom: .98, stick: 1.2, bucket: 1.4 },
  slam:  { boom: .18, stick: 1.1, bucket: .85 },
  dump:  { boom: .72, stick: 1.2, bucket: -.15 },
};
const state = { x: 0, z: 0, yaw: 0, swing: 0, tread: 0, load: false, boom: .25, stick: 2.05, bucket: 1.7 };
function pose(p) { Object.assign(state, p); }
function blend(a, b, t) { return { boom: lerp(a.boom, b.boom, t), stick: lerp(a.stick, b.stick, t), bucket: lerp(a.bucket, b.bucket, t) }; }
function applyPose() {
  exc.position.set(state.x, 0, state.z); exc.rotation.y = state.yaw;
  house.rotation.y = state.swing;
  boomPivot.rotation.x = -state.boom; stickPivot.rotation.x = state.stick; bucketPivot.rotation.x = state.bucket;
  load.visible = state.load;
  setTread(state.tread);
  updateCylinders();
}
const W_POS = o => { exc.updateMatrixWorld(true); return o.getWorldPosition(v3(0, 0, 0)); };

// ───────────────────────── Baustelle ─────────────────────────
const dirtTex = dirtTexture();
MAT.ground = new THREE.MeshStandardMaterial({ map: dirtTex, roughness: .96, color: 0xffffff });
const terrGeo = new THREE.PlaneGeometry(320, 320, 170, 170).rotateX(-Math.PI / 2);
{
  const p = terrGeo.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), z = p.getZ(i), r = Math.hypot(x, z);
    const amp = THREE.MathUtils.smoothstep(r, 16, 45) * 5 + THREE.MathUtils.smoothstep(r, 70, 150) * 22;
    p.setY(i, (fbm(x / 30 + 3, z / 30 + 7, 4) - .42) * amp + (fbm(x / 3, z / 3, 2) - .5) * .12);
  }
  terrGeo.computeVertexNormals();
}
const ground = mk(terrGeo, MAT.ground, CLAY.ground, { edge: false }); ground.castShadow = false; scene.add(ground);
const grid = new THREE.GridHelper(120, 120, 0x5c5c5c, 0x777777); grid.position.y = .015; scene.add(grid);

function mound(x, z, r, h, seed) {
  const g = new THREE.SphereGeometry(1, 40, 20, 0, Math.PI * 2, 0, Math.PI / 2);
  const p = g.attributes.position;
  for (let i = 0; i < p.count; i++) { const a = p.getX(i), b = p.getY(i), c = p.getZ(i); const n = .75 + .5 * fbm(a * 2 + seed, c * 2 + seed, 3); p.setXYZ(i, a * r * n, b * h * n, c * r * n); }
  g.computeVertexNormals();
  const m = mk(g, MAT.dirt, CLAY.mid, { edge: false }); m.position.set(x, -.05, z); scene.add(m); return m;
}
mound(-5.5, -4, 2.6, 1.6, 1); mound(6.5, -3, 3.2, 2.0, 2); mound(12, 11, 2.2, 1.2, 3); mound(-11, 12, 3.5, 2.2, 4);

// Fundament mit Schalung + Bewehrung
const found = new THREE.Group(); found.position.set(-9, 0, 4); scene.add(found);
{
  const slab = mk(box(7, .32, 5.2), MAT.concrete, CLAY.light); slab.position.y = .16; found.add(slab);
  for (const [w, d, x, z] of [[7.4, .08, 0, 2.66], [7.4, .08, 0, -2.66], [.08, 5.4, 3.66, 0], [.08, 5.4, -3.66, 0]]) {
    const b = mk(box(w, .42, d), MAT.wood, CLAY.mid); b.position.set(x, .21, z); found.add(b);
  }
  const rg = new THREE.CylinderGeometry(.018, .018, 1, 6);
  const n = 24 + 18, bars = new THREE.InstancedMesh(rg, MAT.rebar, n); bars.castShadow = true; bars.userData.color = MAT.rebar; bars.userData.clay = CLAY.dark; reg.push(bars);
  let k = 0;
  for (let i = 0; i < 24; i++) { dummy.position.set(-3.3 + i * 6.6 / 23, .4, 0); dummy.rotation.set(Math.PI / 2, 0, 0); dummy.scale.set(1, 5, 1); dummy.updateMatrix(); bars.setMatrixAt(k++, dummy.matrix); }
  for (let i = 0; i < 18; i++) { dummy.position.set(0, .43, -2.4 + i * 4.8 / 17); dummy.rotation.set(0, 0, Math.PI / 2); dummy.scale.set(1, 6.8, 1); dummy.updateMatrix(); bars.setMatrixAt(k++, dummy.matrix); }
  found.add(bars);
}
for (const [x, z] of [[9, 6], [-4, 9.5], [10, -2], [-12.5, -2.5]]) {
  const c = mk(new THREE.ConeGeometry(.2, .7, 20), MAT.cone, CLAY.light); c.position.set(x, .35, z); scene.add(c);
  const s = mk(new THREE.CylinderGeometry(.115, .145, .12, 20), MAT.white, CLAY.light, { edge: false }); s.position.set(x, .42, z); scene.add(s);
}

// Uhr (Top-Down-Sequenz beim Hi-Hat-Roll)
async function clockTexture() {
  await document.fonts.load('120px Anton');
  const N = 2048, c = document.createElement('canvas'); c.width = c.height = N; const g = c.getContext('2d'), m = N / 2;
  const grd = g.createRadialGradient(m, m, 0, m, m, m);
  grd.addColorStop(0, '#ff6a00'); grd.addColorStop(.35, '#7a2500'); grd.addColorStop(.62, '#1a0800'); grd.addColorStop(1, '#000');
  g.fillStyle = grd; g.fillRect(0, 0, N, N);
  g.strokeStyle = '#ffc400'; g.lineWidth = 34; g.beginPath(); g.arc(m, m, N * .4, 0, 7); g.stroke();
  g.lineWidth = 10; g.beginPath(); g.arc(m, m, N * .3, 0, 7); g.stroke();
  for (let i = 0; i < 60; i++) {
    const a = i / 60 * Math.PI * 2, r1 = N * .37, r2 = i % 5 ? N * .355 : N * .33;
    g.lineWidth = i % 5 ? 6 : 16; g.beginPath(); g.moveTo(m + Math.sin(a) * r1, m - Math.cos(a) * r1); g.lineTo(m + Math.sin(a) * r2, m - Math.cos(a) * r2); g.stroke();
  }
  g.fillStyle = '#ffc400'; g.font = '150px Anton'; g.textAlign = 'center'; g.textBaseline = 'middle';
  const R = ['XII', 'I', 'II', 'III', 'IV', 'V', 'VI', 'VII', 'VIII', 'IX', 'X', 'XI'];
  for (let i = 0; i < 12; i++) { const a = i / 12 * Math.PI * 2; g.fillText(R[i], m + Math.sin(a) * N * .45, m - Math.cos(a) * N * .45); }
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
}
const clock = new THREE.Group(); scene.add(clock); clock.visible = false;
const clockDisc = new THREE.Mesh(new THREE.CircleGeometry(9, 96).rotateX(-Math.PI / 2), new THREE.MeshBasicMaterial({ map: await clockTexture(), color: new THREE.Color(2.2, 2.2, 2.2) }));
clockDisc.position.y = .03; clock.add(clockDisc);
const hand = new THREE.Mesh(box(.18, .02, 6.2), new THREE.MeshBasicMaterial({ color: new THREE.Color(4, 3, .3) }));
hand.geometry.translate(0, 0, 2.6); hand.position.y = .06; clock.add(hand);

// ───────────────────────── Partikel (deterministisch) ─────────────────────────
const MAXD = 900, MAXC = 320;
const dustGeo = new THREE.BufferGeometry();
dustGeo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(MAXD * 3), 3));
dustGeo.setAttribute('aSize', new THREE.BufferAttribute(new Float32Array(MAXD), 1));
dustGeo.setAttribute('aAlpha', new THREE.BufferAttribute(new Float32Array(MAXD), 1));
const dustMat = new THREE.ShaderMaterial({
  transparent: true, depthWrite: false,
  uniforms: { uScale: { value: 1000 }, uColor: { value: new THREE.Color(.62, .45, .3) } },
  vertexShader: `attribute float aSize; attribute float aAlpha; uniform float uScale; varying float vA;
    void main(){ vec4 mv = modelViewMatrix * vec4(position, 1.); gl_Position = projectionMatrix * mv; gl_PointSize = min(aSize * uScale / -mv.z, 700.); vA = aAlpha * smoothstep(1.5, 5., -mv.z); }`,
  fragmentShader: `uniform vec3 uColor; varying float vA;
    void main(){ float r = length(gl_PointCoord - .5) * 2.; float a = smoothstep(1., 0., r); gl_FragColor = vec4(uColor * (0.8 + 0.4 * (1. - r)), a * a * vA); }`,
});
const dust = new THREE.Points(dustGeo, dustMat); dust.frustumCulled = false; scene.add(dust);
const chunks = new THREE.InstancedMesh(new THREE.DodecahedronGeometry(.055, 0), MAT.dirt, MAXC);
chunks.castShadow = true; chunks.frustumCulled = false; chunks.userData.color = MAT.dirt; chunks.userData.clay = CLAY.mid; reg.push(chunks); scene.add(chunks);

const EMIT = []; // {t0, origin(), dust, chunks, power, kind}
function updateParticles(st) {
  const P = dustGeo.attributes.position.array, S = dustGeo.attributes.aSize.array, A = dustGeo.attributes.aAlpha.array;
  let d = 0, c = 0;
  for (const [ei, e] of EMIT.entries()) {
    const age0 = st - e.t0; if (age0 < 0 || age0 > e.life) continue;
    const o = e.o || (e.o = e.origin());
    for (let i = 0; i < e.dust && d < MAXD; i++) {
      const sd = ei * 1000 + i, a = age0 - (e.kind === 'pour' ? rnd(sd, 9) * .5 : rnd(sd, 9) * .05); if (a < 0) continue;
      const ang = rnd(sd, 1) * Math.PI * 2, el = e.kind === 'pour' ? -1.2 : rnd(sd, 2) * .9 + .08;
      const sp = e.power * (1.5 + rnd(sd, 3) * 6), k = 2.2, f = (1 - Math.exp(-k * a)) / k;
      let x = o.x + Math.cos(ang) * Math.cos(el) * sp * f, z = o.z + Math.sin(ang) * Math.cos(el) * sp * f;
      let y = o.y + Math.sin(el) * sp * f + a * .35;
      if (e.kind === 'pour') { x = o.x + (rnd(sd, 4) - .5) * .9 + (rnd(sd, 5) - .5) * a; z = o.z + (rnd(sd, 6) - .5) * .5; y = Math.max(.1, o.y - 4.9 * a * a) + a * .4; }
      P[d * 3] = x; P[d * 3 + 1] = Math.max(y, .05); P[d * 3 + 2] = z;
      S[d] = (.35 + rnd(sd, 7) * .9) * (1 + a * (e.kind === 'pour' ? 1.2 : 2.2)) * e.size;
      A[d] = Math.pow(1 - a / e.life, 2.2) * (.2 + rnd(sd, 8) * .3) * clamp(a * 30);
      d++;
    }
    for (let i = 0; i < e.chunks && c < MAXC; i++) {
      const sd = ei * 2000 + i + 7, a = age0 - (e.kind === 'pour' ? rnd(sd, 9) * .45 : 0); if (a < 0) continue;
      const ang = rnd(sd, 1) * Math.PI * 2, el = e.kind === 'pour' ? 0 : .5 + rnd(sd, 2) * .9, sp = e.kind === 'pour' ? .6 * rnd(sd, 3) : e.power * (2 + rnd(sd, 3) * 4.5);
      let x = o.x + Math.cos(ang) * Math.cos(el) * sp * a + (e.kind === 'pour' ? (rnd(sd, 4) - .5) * .9 : 0);
      let z = o.z + Math.sin(ang) * Math.cos(el) * sp * a;
      let y = o.y + Math.sin(el) * sp * a - 4.9 * a * a;
      const landed = y < .04; if (landed) y = .04;
      dummy.position.set(x, y, z); dummy.rotation.set(a * 9 * rnd(sd, 5), a * 7, 0);
      const s = (.5 + rnd(sd, 6) * 1.2) * e.size; dummy.scale.set(s, s, s); dummy.updateMatrix(); chunks.setMatrixAt(c++, dummy.matrix);
    }
  }
  for (let i = d; i < MAXD; i++) A[i] = 0;
  dustGeo.setDrawRange(0, d);
  dustGeo.attributes.position.needsUpdate = dustGeo.attributes.aSize.needsUpdate = dustGeo.attributes.aAlpha.needsUpdate = true;
  chunks.count = c; chunks.instanceMatrix.needsUpdate = true;
}
// Zeitlupe nach dem Drop: Simulationszeit für Partikel
const SLOW1 = .32, SLOW2 = .75;
const sim = t => t < DROP ? t : t < B[15] ? DROP + (t - DROP) * SLOW1 : DROP + (B[15] - DROP) * SLOW1 + (t - B[15]) * SLOW2;
function tipAt(p) { const keep = { ...state }; pose(p); applyPose(); const v = W_POS(bucketTip); Object.assign(state, keep); applyPose(); return v; }
function mouthAt(p) { const keep = { ...state }; pose(p); applyPose(); const v = W_POS(bucketMouth); Object.assign(state, keep); applyPose(); return v; }
EMIT.push({ t0: DIG, life: 1.8, dust: 90, chunks: 45, power: 1.0, size: 1, origin: () => tipAt({ ...POSE.hit, swing: 0, x: 0, z: 0 }).setY(.15) });
EMIT.push({ t0: DROP, life: 3.2, dust: 380, chunks: 160, power: 1.9, size: 1.3, origin: () => tipAt({ ...POSE.slam, swing: 0, x: 0, z: 0 }).setY(.2) });
EMIT.push({ t0: sim(DUMP + .05), life: 3, dust: 140, chunks: 70, power: .6, size: .9, kind: 'pour', origin: () => mouthAt({ ...POSE.dump, swing: .5, x: 0, z: 0 }) });

for (const e of EMIT) e.o = e.origin(); // Ursprünge vorab berechnen

// ───────────────────────── Modus: Clay / Farbe ─────────────────────────
const FOG_COLOR = new THREE.Fog(0xd9a06c, 30, 260), FOG_CLAY = new THREE.Fog(0x767676, 30, 150);
const CLAY_BG = new THREE.Color(0x767676);
let curMode = null;
function setMode(mode) {
  if (mode === curMode) return; curMode = mode;
  const clay = mode === 'clay';
  for (const m of reg) m.material = clay ? m.userData.clay : m.userData.color;
  for (const l of edges) l.visible = clay;
  grid.visible = clay; sky.visible = !clay;
  scene.background = clay ? CLAY_BG : null; scene.fog = clay ? FOG_CLAY : FOG_COLOR;
  scene.traverse(o => { if (o.userData.brand) o.visible = !clay; });
  sun.color.set(clay ? 0xffffff : 0xffc38a); sun.intensity = clay ? 2.5 : 4.2;
  hemi.color.set(clay ? 0xffffff : 0x9cb8ff); hemi.groundColor.set(clay ? 0x777777 : 0x6a4428); hemi.intensity = clay ? .55 : .9;
  scene.environmentIntensity = clay ? .25 : .55;
  dustMat.uniforms.uColor.value.set(clay ? .55 : .75, clay ? .55 : .52, clay ? .55 : .34);
}

// ───────────────────────── Overlay (DOM) ─────────────────────────
const ov = document.getElementById('ov');
let ovHTML = '';
const add = (html, cls, style) => { ovHTML += `<div class="${cls}" style="${style}">${html}</div>`; };
function typed(text, p, y, size = 88) {
  const n = Math.round(clamp(p) * text.length);
  add(`${text.slice(0, n)}<span class="cursor"></span>`, 'type', `top:${y}px;font-size:${size}px`);
}
function slam(text, t, t0, y, size, cls = 'slam', dur = .13) {
  if (t < t0) return;
  const p = E.outExpo(inv(t0, t0 + dur, t));
  const s = 1 + 1.4 * (1 - p), blur = 18 * (1 - p), op = clamp((t - t0) / .03);
  add(text, cls, `top:${y}px;font-size:${size}px;transform:scale(${s});filter:blur(${blur}px);opacity:${op}`);
}
const tag = t => add('● HAVVAMBAU&nbsp;&nbsp;/&nbsp;&nbsp;3D-SZENE', 'tag', `left:56px;top:${150}px;opacity:${.55 + .45 * (Math.floor(t * 4) % 2)}`);

// ───────────────────────── Post-Parameter ─────────────────────────
const P = {};
function resetPost(mode) { Object.assign(P, { chroma: .0018, vig: .55, grain: .045, flash: 0, exposure: mode === 'clay' ? .92 : 1, sat: 1, zoom: 0, fade: 0, contrast: mode === 'clay' ? 1.16 : 1.05, warm: 0, shake: [0, 0] }); }
const punch = (t, t0, amt = .22, d = .14) => t >= t0 ? amt * (1 - E.outCubic(inv(t0, t0 + d, t))) : 0;
const flashAt = (t, t0, amt = 1, d = .15) => t >= t0 ? amt * Math.pow(1 - inv(t0, t0 + d, t), 2) : 0;

// ───────────────────────── Kamera ─────────────────────────
function look(pos, target, fov = 35, roll = 0) {
  cam.position.copy(pos); cam.lookAt(target); cam.fov = fov;
  if (roll) cam.rotateZ(roll);
}
function shake(t, amp, seed = 0) {
  if (amp <= 0) return;
  cam.rotateX(wobble(t * 2.3, seed) * amp); cam.rotateY(wobble(t * 2.1, seed + 9) * amp); cam.rotateZ(wobble(t * 1.7, seed + 4) * amp * .6);
}
const whip = (t, t0, ang, d = .16) => t >= t0 ? ang * (1 - E.outCubic(inv(t0, t0 + d, t))) : 0;

// ───────────────────────── Shots ─────────────────────────
// Jeder Shot: a/b = Start/Ende (s), mode = clay | color | split | logo, mb = Motion-Blur-Subframes,
// scene(t,u) = Kamera + Pose (wird pro Subframe aufgerufen), ui(t,u) = Overlay + Post (einmal pro Frame).
const CAB = () => W_POS(cab).add(v3(0, 1.0, 0));
const S = [];
const shot = o => S.push(o);

// 1 – Hook: Makro auf die Zähne, Text tippt
shot({ a: 0, b: B[0], mode: 'clay', mb: 1,
  scene(t, u) { pose({ ...POSE.hit, swing: 0, load: false, tread: 0 }); applyPose(); const T = W_POS(bucketTip);
    look(T.clone().add(v3(lerp(1.5, .7, E.outCubic(u)), .3, 1.15)), T.clone().add(v3(-.1, .15, 0)), 30); },
  ui(t, u) { typed('Ihr Projekt.', inv(.06, .5, t), 640); P.exposure = .78; P.fade = 1 - inv(0, .09, t); P.vig = .9; } });
// 2 – Fahrt auf die Kamera zu (Bodenperspektive)
shot({ a: B[0], b: B[1], mode: 'clay', mb: 2,
  scene(t, u) { const z = lerp(-2.2, -1.2, u); pose({ ...POSE.rest, z, tread: z * 1.0, swing: 0 }); applyPose();
    look(v3(lerp(3.4, 3.1, u), .32, 9.2), v3(0, 1.5, 0), 31); shake(t, .003); },
  ui(t) { P.zoom = punch(t, B[0], .3); P.flash = flashAt(t, B[0], .35, .08); tag(t); } });
// 3 – Seitliche Fahrt, "Unser Handwerk."
shot({ a: B[1], b: B[2], mode: 'clay', mb: 2,
  scene(t, u) { pose({ ...POSE.rest, z: 0, tread: 0, swing: 0 }); applyPose();
    look(v3(9.5, 1.5, lerp(4.5, -.5, u)), v3(0, 1.7, lerp(2, -.6, u)), 30); },
  ui(t) { typed('Unser Handwerk.', inv(B[1] + .02, B[1] + .2, t), 640); P.zoom = punch(t, B[1], .18); tag(t); } });
// 4 – Kabine, Oberwagen dreht
shot({ a: B[2], b: B[3], mode: 'clay', mb: 2,
  scene(t, u) { pose({ ...POSE.rest, swing: lerp(-.35, .2, E.inOutSine(u)) }); applyPose(); const c = CAB();
    const a = lerp(.45, 1.15, u); look(c.clone().add(v3(Math.sin(a) * 6.2, .9, Math.cos(a) * 6.2)), c.clone().add(v3(-.4, -.2, 0)), 32); },
  ui(t) { P.zoom = punch(t, B[2], .25); tag(t); } });
// 5 – Whip-Pan, Graben: Löffel schlägt bei DIG ein
shot({ a: B[3], b: B[5], mode: 'clay', mb: t => t < B[3] + .16 ? 5 : 2, shutter: 1 / 30,
  scene(t) {
    let p; if (t < DIG) p = blend(POSE.up, POSE.hit, E.inCubic(inv(B[3], DIG, t)));
    else p = blend(POSE.hit, POSE.curl, E.inOutCubic(inv(DIG + .03, B[5], t)));
    pose({ ...p, swing: 0, load: t > DIG + .12 }); applyPose();
    look(v3(6.2, 2.4, 11), v3(0, 1.3, 4.6), 32); cam.rotateY(whip(t, B[3], .9));
    if (t > DIG) shake(t, .03 * Math.exp(-(t - DIG) * 9), 3);
  },
  ui(t) { P.flash = flashAt(t, DIG, .25, .1); P.zoom = punch(t, DIG, .2, .12); P.chroma = .0018 + punch(t, DIG, .01); tag(t); } });
// 6 – Löffel steigt mit Erde
shot({ a: B[5], b: B[6], mode: 'clay', mb: 2,
  scene(t, u) { pose({ ...blend(POSE.curl, POSE.high, E.inOutSine(u)), swing: 0, load: true }); applyPose(); const b = W_POS(bucketMouth);
    look(v3(3.2, .5, 9.5), b.clone().add(v3(0, -.3, 0)), 28); },
  ui(t) { P.zoom = punch(t, B[5], .2); tag(t); } });
// 7 – Split-Screen: oben Render, unten 3D-Szene
shot({ a: B[6], b: B[8], mode: 'split', mb: 2,
  scene(t) { const u = inv(B[6], B[8], t); pose({ ...POSE.high, swing: lerp(0, 1.5, E.inOutSine(u)), load: true }); applyPose();
    if (t < B[7]) look(v3(-9.5, 3.2, 10.5), v3(0, 2.6, 1.5), 36); else look(v3(4, .8, -11), v3(0, 2.6, 0), 36); },
  ui(t) { add('Final', 'label', 'top:110px'); add('3D-Szene', 'label', 'top:1070px'); P.zoom = punch(t, B[6], .2) + punch(t, B[7], .2); P.flash = flashAt(t, B[6], .3, .07); } });
// 8 – Rush auf die Kabine (Speed-Ramp), bei 3.95 Stillstand
const RUSH_END = 3.95;
function rushScene(t) {
  pose({ ...POSE.high, swing: .25, load: true }); applyPose();
  const p = E.outExpo(inv(B[8], RUSH_END, t));
  look(mix3(v3(18, 7, 26), v3(7.8, 1.5, 10.5), p), mix3(v3(0, 2, 0), v3(0, 2.7, 1.8), p), lerp(42, 33, p));
}
shot({ a: B[8], b: TL.break, mode: 'clay', mb: t => t < B[8] + .2 ? 5 : 1, shutter: 1 / 30, scene: rushScene,
  ui(t) { P.zoom = .35 * (1 - inv(B[8], B[8] + .25, t)); tag(t); } });
// 9 – Break: Freeze-Frame
shot({ a: TL.break, b: ROLL[0], mode: 'clay', mb: 1, scene: () => rushScene(RUSH_END),
  ui(t) { P.sat = 0; P.exposure = .55; P.vig = 1; P.contrast = 1.25; P.grain = .09; P.flash = flashAt(t, TL.break, .5, .05); } });
// 10 – Hi-Hat-Roll: Top-Down auf der Uhr
const tickIdx = t => ROLL.filter(x => x <= t).length;
const tickEase = (t, step) => { const i = tickIdx(t); if (!i) return 0; const p = E.outExpo(inv(ROLL[i - 1], ROLL[i - 1] + .05, t)); return (i - 1 + p) * step; };
shot({ a: ROLL[0], b: B[12], mode: 'clay', mb: 1,
  scene(t) { pose({ ...POSE.rest, swing: tickEase(t, Math.PI / 6), load: false }); applyPose();
    clock.visible = true; hand.rotation.y = -tickEase(t, Math.PI / 6);
    const h = lerp(17, 11.5, tickEase(t, 1 / ROLL.length));
    cam.up.set(0, 0, -1); look(v3(0, h, .001), v3(0, 0, 0), 40, tickEase(t, .06)); },
  ui(t) { const i = tickIdx(t); P.flash = i ? flashAt(t, ROLL[i - 1], .18, .06) : 0; P.zoom = i ? punch(t, ROLL[i - 1], .08, .06) : 0; P.vig = .8; } });
// 11 – Spannung: Low-Angle, Kamera schiebt rein, wird dunkel → Schwarz vor dem Drop
const INSERT = [B[13], B[13] + .07];
shot({ a: B[12], b: DROP, mode: 'clay', mb: 1,
  scene(t, u) {
    pose({ ...blend(POSE.high, POSE.raise, E.inOutSine(u)), swing: 0, load: false }); applyPose();
    if (t >= INSERT[0] && t < INSERT[1]) { const T = W_POS(bucketTip); look(T.clone().add(v3(.9, -.2, 1.0)), T, 26); return; }
    look(v3(lerp(1.6, .8, u), lerp(.45, .75, u), lerp(13, 10, E.inQuad(u))), v3(0, lerp(2.4, 3.2, u), 1), lerp(34, 28, u));
    shake(t, .014 * E.inQuad(u), 5);
  },
  ui(t, u) { P.exposure = lerp(1, .5, u); P.zoom = .16 * E.inQuad(u) + punch(t, B[12], .25); P.fade = inv(5.63, 5.7, t); P.chroma = .0018 + .006 * u;
    if (t >= INSERT[0] && t < INSERT[1]) P.flash = .25; } });
// 12 – DROP: Farbe, Einschlag, Staubexplosion in Zeitlupe
shot({ a: DROP, b: B[15], mode: 'color', mb: 3, shutter: 1 / 40,
  scene(t, u) { pose({ ...POSE.slam, swing: 0, load: false }); applyPose();
    look(v3(lerp(6.4, 5.9, u), .5, lerp(15.5, 14.5, u)), v3(-.5, 1.4, 4.8), 33); shake(t, .05 * Math.exp(-(t - DROP) * 6), 11); },
  ui(t) { P.flash = flashAt(t, DROP, 1, .16); P.chroma = .0018 + punch(t, DROP, .016, .3); P.zoom = punch(t, DROP, .35, .2); P.warm = .5;
    slam(BRAND, t, DROP, 300, 196); } });
// 13 – schneller Orbit (Speed-Ramp schnell → langsam)
shot({ a: B[15], b: B[16], mode: 'color', mb: t => t < B[15] + .15 ? 5 : 2, shutter: 1 / 30,
  scene(t, u) { pose({ ...blend(POSE.slam, POSE.up, E.inOutSine(u) * .5), swing: 0 }); applyPose();
    const a = lerp(-.5, 1.9, E.outCubic(u)); look(v3(Math.sin(a) * 10.5, 2.3, Math.cos(a) * 10.5 + 1.5), v3(0, 1.9, 1.5), 32); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[15], .2); } });
// 14 – Schriftzug-Makro am Ausleger (wie das Logo-Detail im Radlader-Edit)
shot({ a: B[16], b: B[17], mode: 'color', mb: 2,
  scene(t, u) { pose({ ...POSE.up, swing: 0 }); applyPose(); const b = W_POS(brandSpot);
    look(b.clone().add(v3(-2.6, lerp(-.5, .1, u), lerp(1.6, -.6, E.inOutSine(u)))), b.clone().add(v3(0, 0, lerp(.5, -.3, u))), 28); shake(t, .003, 2); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[16], .25); P.flash = flashAt(t, B[16], .2, .06); } });
// 15 – Silhouette gegen die Sonne, Ausleger hebt
shot({ a: B[17], b: B[18], mode: 'color', mb: 2,
  scene(t, u) { pose({ ...blend(POSE.slam, POSE.raise, E.inOutSine(u)), swing: 0, load: true }); applyPose();
    look(v3(11.5, .5, 8.5), v3(0, 3.1, 0), 30); },
  ui(t) { P.warm = .7; P.zoom = punch(t, B[17], .2); P.exposure = 1.1; } });
// 16 – Auskippen
shot({ a: B[18], b: B[19], mode: 'color', mb: 2,
  scene(t, u) { const op = E.outCubic(inv(B[18], B[18] + .2, t)); pose({ ...blend(POSE.high, POSE.dump, op), swing: .5, load: op < .55 }); applyPose();
    const m = W_POS(bucketMouth); look(m.clone().add(v3(-5.5, 2.6, 6)), m.clone().add(v3(0, -1.2, 0)), 32); },
  ui(t) { P.warm = .5; P.zoom = punch(t, B[18], .2); } });
// 17 – Whip-Pan + Kran-Rückfahrt: ganze Baustelle, "Wir schaffen die Grundlage."
shot({ a: B[19], b: B[21], mode: 'color', noDust: true, mb: t => t < B[19] + .16 ? 5 : 2, shutter: 1 / 30,
  scene(t, u) { pose({ ...POSE.raise, swing: .3, load: false }); applyPose(); const p = E.inOutCubic(u);
    shadowAround(v3(-3, 0, 2), 22);
    look(mix3(v3(3.5, 2.2, 9.5), v3(9, 9.5, 17), p), mix3(v3(0, 1.8, 0), v3(-3, .5, 2.5), p), lerp(34, 38, p)); cam.rotateY(whip(t, B[19], -1.0)); },
  ui(t) { P.warm = .5; slam('WIR SCHAFFEN', t, B[19] + .05, 250, 140, 'slam white'); slam('DIE GRUNDLAGE.', t, B[20], 410, 150); P.zoom = punch(t, B[20], .12); } });
// 18 – Logo-Build auf Weiß
shot({ a: B[21], b: 99, mode: 'logo', mb: 1, scene() {}, ui: logoUI });

function logoUI(t) {
  const T0 = B[21];
  const wipe = E.outCubic(inv(T0, T0 + .14, t)) * 1400;
  const zoom = 1 + .04 * inv(T0, TL.duration, t) + punch(t, TL.end_hits[1], .04, .2) + punch(t, TL.end_hits[2], .03, .2);
  let h = `<div style="position:absolute;inset:0;background:#fff;clip-path:circle(${wipe}px at 50% 50%)"></div>`;
  h += `<div style="position:absolute;inset:0;transform:scale(${zoom});transform-origin:50% 44%">`;
  // Logo-Zeichen: zwei Pfeiler + Querbalken = "H" aus Fundamentblöcken
  const drop = (t0, y0) => { const p = E.outBack(inv(t0, t0 + .16, t)); return [y0 * (1 - p), clamp((t - t0) * 25)]; };
  const [y1, o1] = drop(T0 + .03, -500), [y2, o2] = drop(T0 + .11, -500);
  const pb = E.outBack(inv(T0 + .2, T0 + .34, t));
  const cx = 540, cy = 760;
  h += `<div style="position:absolute;left:${cx - 120}px;top:${cy - 130 + y1}px;width:72px;height:260px;background:#F5B800;border-radius:10px;opacity:${o1}"></div>`;
  h += `<div style="position:absolute;left:${cx + 48}px;top:${cy - 130 + y2}px;width:72px;height:260px;background:#F5B800;border-radius:10px;opacity:${o2}"></div>`;
  h += `<div style="position:absolute;left:${cx - 120}px;top:${cy - 26}px;width:240px;height:52px;background:#111;border-radius:8px;transform:scaleX(${pb});transform-origin:0 50%"></div>`;
  h += `<div style="position:absolute;left:${cx - 160}px;top:${cy + 150}px;width:320px;height:14px;background:#111;border-radius:7px;transform:scaleX(${E.outCubic(inv(T0 + .28, T0 + .42, t))})"></div>`;
  // Wortmarke
  const wy = 1010, w0 = TL.end_hits[0];
  let letters = '';
  [...BRAND].forEach((ch, i) => { const p = E.outCubic(inv(w0 + i * .022, w0 + i * .022 + .14, t)); letters += `<span style="display:inline-block;transform:translateY(${(1 - p) * 110}%)">${ch}</span>`; });
  h += `<div class="logo-word" style="left:0;right:0;text-align:center;top:${wy}px;overflow:hidden;height:190px;line-height:190px">${letters}</div>`;
  const s1 = TL.end_hits[1], p1 = E.outCubic(inv(s1, s1 + .2, t));
  h += `<div class="logo-sub" style="left:0;right:0;text-align:center;top:${1230 + 30 * (1 - p1)}px;opacity:${p1}">Erdarbeiten · Fundamente · Pflaster</div>`;
  const s2 = TL.end_hits[2], p2 = E.outCubic(inv(s2, s2 + .2, t));
  h += `<div class="logo-small" style="left:0;right:0;text-align:center;top:${1320 + 30 * (1 - p2)}px;opacity:${p2}"><span class="hl">Augsburg &amp; Umgebung</span>&nbsp;&nbsp;havvambau.de</div>`;
  h += `</div>`;
  ovHTML += h;
  P.grain = 0; P.vig = 0; P.chroma = 0;
}

// ───────────────────────── Frame rendern ─────────────────────────
const FPS = TL.fps;
function renderView(mode, x, y, w, h) {
  setMode(mode);
  cam.aspect = w / h; cam.updateProjectionMatrix();
  sky.position.copy(cam.position);
  dustMat.uniforms.uScale.value = h / (2 * Math.tan(THREE.MathUtils.degToRad(cam.fov / 2)));
  rtScene.viewport.set(x, y, w, h); rtScene.scissor.set(x, y, w, h); rtScene.scissorTest = true;
  renderer.setRenderTarget(rtScene);
  renderer.render(scene, cam);
}
function renderScene(sh, t) {
  cam.up.set(0, 1, 0); clock.visible = false; shadowAround(v3(0, 0, 1.5), 13);
  sh.scene(t, inv(sh.a, sh.b, t));
  updateParticles(sim(t)); dust.visible = !sh.noDust;
  if (sh.mode === 'split') {
    const c = { p: cam.position.clone(), q: cam.quaternion.clone() };
    renderView('color', 0, H / 2, W, H / 2);
    cam.position.copy(c.p); cam.quaternion.copy(c.q);
    renderView('clay', 0, 0, W, H / 2);
  } else renderView(sh.mode, 0, 0, W, H);
}
window.renderFrame = (t) => {
  const sh = S.find(s => t >= s.a && t < s.b) || S[S.length - 1];
  resetPost(sh.mode); ovHTML = '';
  sh.ui(t, inv(sh.a, sh.b, t));
  if (sh.mode === 'logo') {
    renderer.setRenderTarget(null); renderer.setClearColor(0x000000); renderer.clear();
  } else {
    const n = window.FORCE_MB ?? (typeof sh.mb === 'function' ? sh.mb(t) : sh.mb);
    const shutter = sh.shutter ?? .5 / FPS;
    let src = rtScene.texture;
    if (n > 1) {
      for (let k = 0; k < n; k++) {
        const tk = clamp(t + ((k + .5) / n - .5) * shutter, sh.a, sh.b - 1e-4);
        renderScene(sh, tk);
        const dst = rtAcc[k % 2], prv = rtAcc[(k + 1) % 2];
        quad.material = accumMat; Object.assign(accumMat.uniforms.tex, { value: rtScene.texture });
        accumMat.uniforms.prev.value = prv.texture; accumMat.uniforms.k.value = 1 / n; accumMat.uniforms.first.value = k === 0 ? 1 : 0;
        renderer.setRenderTarget(dst); renderer.render(quadScene, quadCam);
        src = dst.texture;
      }
    } else renderScene(sh, t);
    const U = postMat.uniforms;
    U.tex.value = src; U.uTime.value = t; U.uChroma.value = P.chroma; U.uVig.value = P.vig; U.uGrain.value = P.grain; U.uFlash.value = clamp(P.flash);
    U.uExposure.value = P.exposure; U.uSat.value = P.sat; U.uZoom.value = P.zoom; U.uFade.value = clamp(P.fade); U.uContrast.value = P.contrast; U.uWarm.value = P.warm;
    quad.material = postMat; renderer.setRenderTarget(null); renderer.render(quadScene, quadCam);
  }
  ov.innerHTML = ovHTML;
  renderer.getContext().finish(); // GPU fertig, bevor der Screenshot kommt
  return sh.a;
};

window.tipOf = (p) => tipAt({ x: 0, z: 0, swing: 0, ...p }).toArray();
window.mouthOf = (p) => mouthAt({ x: 0, z: 0, swing: 0, ...p }).toArray();
// Debug: beliebige Ansicht rendern  {pos:[x,y,z], target:[x,y,z], fov, pose:'rest'|{...}, swing, mode, t}
window.debugRender = (o) => {
  resetPost(); ovHTML = ''; cam.up.set(0, 1, 0); clock.visible = false; shadowAround(v3(0, 0, 1.5), 13);
  const pz = typeof o.pose === 'string' ? POSE[o.pose] : (o.pose || POSE.rest);
  pose({ x: 0, z: 0, tread: 0, swing: o.swing || 0, load: !!o.load, ...pz }); applyPose();
  updateParticles(o.t ?? -10);
  look(v3(...o.pos), v3(...o.target), o.fov || 35);
  renderView(o.mode || 'color', 0, 0, W, H);
  const U = postMat.uniforms; U.tex.value = rtScene.texture; U.uExposure.value = 1; U.uSat.value = 1; U.uZoom.value = 0; U.uFade.value = 0; U.uFlash.value = 0; U.uContrast.value = 1.05; U.uVig.value = .4; U.uChroma.value = 0; U.uGrain.value = 0;
  quad.material = postMat; renderer.setRenderTarget(null); renderer.render(quadScene, quadCam);
  ov.innerHTML = '';
  return { tip: W_POS(bucketTip).toArray().map(v => +v.toFixed(2)), mouth: W_POS(bucketMouth).toArray().map(v => +v.toFixed(2)), cab: CAB().toArray().map(v => +v.toFixed(2)) };
};

await document.fonts.load('100px Anton'); await document.fonts.load('600 88px Inter');
await document.fonts.ready;
window.ready = true;
