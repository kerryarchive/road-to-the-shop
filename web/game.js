/*
 * RepairIQ Academy, Level 1: Rush Hour on the Connector
 *
 * Game states:  READY -> DRIVING -> MECHANIC -> RESULTS
 *
 *   DRIVING   Survive 15 seconds in three lanes of traffic (up to 300 points).
 *   MECHANIC  After a crash: what to inspect (150), repair or replace (150),
 *             and which of three AI quotes is fair (400).
 *   RESULTS   Score out of 1,000 with feedback.
 *
 * Quotes come from the Python server (server.py -> /api/quotes), which calls
 * Gemini and falls back to a clearly labeled offline sample. All server and
 * AI text is shown with textContent, never as HTML.
 */

import * as THREE from "./vendor/three.module.min.js";

// ---------------------------------------------------------------------------
// Settings
// ---------------------------------------------------------------------------

const ROUND_SECONDS = 15;
const LANES = [-2.6, 0, 2.6];
const START_SPEED = 26; // world units per second
const END_SPEED = 46;
const SPAWN_Z = -150;
const DRIVE_POINTS_MAX = 300;
const POINTS = { inspect: 150, repair: 150 };
const QUOTE_POINTS = { quote_fair: 400, quote_dealer: 150, quote_budget: 0 };

// Each obstacle type maps to a hazard key the server knows (HAZARDS in app.py).
const OBSTACLES = {
  car: { hazard: "sideswipe", weight: 0.45, halfLength: 1.7 },
  cone: { hazard: "cone", weight: 0.3, halfLength: 0.45 },
  pothole: { hazard: "pothole", weight: 0.25, halfLength: 1.0 },
};

// Training scenarios written by the team. Steps 1 and 2 of the mechanic
// challenge use these; step 3 uses live AI quotes.
const SCENARIOS = {
  pothole: {
    title: "🕳️ Deep Atlanta Pothole",
    crash: "You slammed into a deep pothole. The steering wheel shakes and the front tire looks low.",
    inspect: {
      question: "What should the mechanic inspect first?",
      options: [
        {
          text: "The tire sidewall, the rim edge, and the wheel alignment",
          correct: true,
          explain: "Pothole hits pinch the tire against the rim. That can bulge the sidewall, bend the rim lip, and knock the alignment out.",
        },
        {
          text: "The engine oil level and the air filter",
          correct: false,
          explain: "Worth checking someday, but a pothole doesn't touch either. Start where the impact happened: the wheel.",
        },
        {
          text: "The rear window seals",
          correct: false,
          explain: "Nothing at the back of the car hit anything. Inspect the corner that took the hit.",
        },
      ],
    },
    repair: {
      finding: "The rim has a visible bend and the tire won't hold air at the bead. The suspension looks straight.",
      question: "Repair or replace?",
      options: [
        {
          text: "Replace the tire, straighten or replace the rim, and check the alignment",
          correct: true,
          explain: "A tire that won't seal at the bead isn't safe to patch, and a bent rim will keep leaking. The alignment check confirms nothing else moved.",
        },
        {
          text: "Just add air and keep driving",
          correct: false,
          explain: "A tire that can't hold air at the bead can fail suddenly at highway speed. Cheap now, dangerous later.",
        },
        {
          text: "Replace all four tires, both front control arms, and the struts",
          correct: false,
          explain: "The suspension looked straight. Replacing parts that aren't damaged is a classic upsell; ask to see the damage first.",
        },
      ],
    },
  },
  cone: {
    title: "🚧 Construction Zone Traffic Cone",
    crash: "A traffic cone bounced off your front end in the construction zone. Something plastic is scraping the road.",
    inspect: {
      question: "What should the mechanic inspect first?",
      options: [
        {
          text: "The front lower bumper lip, its mounting clips, and what's behind it (radiator, sensors)",
          correct: true,
          explain: "The cone hit low on the front. Check the plastic lip and clips, and make sure nothing behind them, like the radiator or a parking sensor, got hit.",
        },
        {
          text: "The brake pads",
          correct: false,
          explain: "Brakes wear from use, not from a cone strike. Look where the impact happened.",
        },
        {
          text: "The spark plugs",
          correct: false,
          explain: "Spark plugs are inside the engine and weren't touched. Start at the front bumper.",
        },
      ],
    },
    repair: {
      finding: "The plastic lower lip is cracked and hanging by one clip. The bumper cover, radiator, and sensors behind it are fine.",
      question: "Repair or replace?",
      options: [
        {
          text: "Replace just the lower lip (valance) and its clips",
          correct: true,
          explain: "Only the lip is damaged, and it's a cheap bolt-on part. Replacing just that is the fair fix.",
        },
        {
          text: "Replace the whole bumper, the grille, and both headlights",
          correct: false,
          explain: "None of that was damaged. A padded estimate often adds whole assemblies when only one small part broke.",
        },
        {
          text: "Tape it up and keep driving",
          correct: false,
          explain: "A loose lip can tear off at speed or get sucked under the car. It's a cheap part; fix it properly.",
        },
      ],
    },
  },
  sideswipe: {
    title: "🚗 Sideswiping a Car in Traffic",
    crash: "You clipped the side of another car. Your mirror is dangling and you heard paint scraping.",
    inspect: {
      question: "What should the mechanic inspect first?",
      options: [
        {
          text: "The side mirror (glass, housing, wiring) and the door panel paint",
          correct: true,
          explain: "A sideswipe hits the mirror and door first. Check the mirror's glass, housing and wiring (it may have a heater or camera), and how deep the scratch goes.",
        },
        {
          text: "The transmission fluid",
          correct: false,
          explain: "A side scrape doesn't reach the transmission. Inspect the side that hit.",
        },
        {
          text: "The cabin air filter",
          correct: false,
          explain: "That's routine maintenance, not crash damage. Start with the mirror and the door.",
        },
      ],
    },
    repair: {
      finding: "The mirror glass is shattered and the housing is cracked. The door has a scratch through the clear coat but no dent.",
      question: "Repair or replace?",
      options: [
        {
          text: "Replace the mirror assembly and refinish the scratched door panel",
          correct: true,
          explain: "A cracked housing can't be glued safely, so the mirror gets replaced. A scratch with no dent only needs that one panel refinished.",
        },
        {
          text: "Repaint both doors and the front fender",
          correct: false,
          explain: "Only one door is scratched. Blending a little into a neighboring panel can be normal, but repainting three full panels is padding.",
        },
        {
          text: "Leave the scratch alone since it's only paint",
          correct: false,
          explain: "A scratch through the clear coat lets water reach the metal, and that turns into rust. Refinishing it now is cheaper than rust repair later.",
        },
      ],
    },
  },
};

const MAINTENANCE_TIPS = [
  "Check your tire pressure once a month, including the spare. Underinflated tires are much more likely to be damaged by potholes.",
  "If your steering wheel is off-center or the car pulls to one side after a pothole, get an alignment check before the tires wear unevenly.",
  "Before any repair, ask for a written, itemized estimate and keep it. A reputable shop will always give you one.",
  "After any damage, photograph it right away with the date and location. It helps with insurance claims and with comparing shop quotes.",
];

const DISCLOSURE =
  "Educational game. Inspection scenarios are written by our team. Prices are illustrative and real repairs need an in-person inspection and local pricing.";

// ---------------------------------------------------------------------------
// Small helpers
// ---------------------------------------------------------------------------

const $ = (id) => document.getElementById(id);

function el(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function button(label, onClick, primary = false) {
  const b = el("button", primary ? "btn primary" : "btn", label);
  b.addEventListener("click", onClick);
  return b;
}

function money(n) {
  return "$" + Math.round(n).toLocaleString("en-US");
}

function shuffle(items) {
  const a = [...items];
  for (let i = a.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [a[i], a[j]] = [a[j], a[i]];
  }
  return a;
}

function pickWeighted(table) {
  const entries = Object.entries(table);
  let roll = Math.random() * entries.reduce((sum, [, v]) => sum + v.weight, 0);
  for (const [key, value] of entries) {
    roll -= value.weight;
    if (roll <= 0) return key;
  }
  return entries[0][0];
}

function showPanel(...children) {
  const body = $("panel-body");
  body.replaceChildren(...children);
  body.scrollTop = 0;
  $("panel").hidden = false;
}

function hidePanel() {
  $("panel").hidden = true;
}

function setDrivingUI(on) {
  $("hud").hidden = !on;
  $("touch").hidden = !on;
}

// ---------------------------------------------------------------------------
// 3D scene
// ---------------------------------------------------------------------------

const canvas = $("scene");
const renderer = new THREE.WebGLRenderer({ canvas, antialias: true });
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));

const scene = new THREE.Scene();
scene.background = new THREE.Color(0x9fc6e8);
scene.fog = new THREE.Fog(0x9fc6e8, 45, 160);

const camera = new THREE.PerspectiveCamera(60, 1, 0.1, 400);
camera.position.set(0, 4.6, 9);
camera.lookAt(0, 1, -12);

scene.add(new THREE.HemisphereLight(0xffffff, 0x4a5a3a, 2.2));
const sun = new THREE.DirectionalLight(0xffffff, 1.8);
sun.position.set(6, 12, 4);
scene.add(sun);

const mat = (color) => new THREE.MeshLambertMaterial({ color });

// Ground and road (static; the scenery on them moves instead).
const grass = new THREE.Mesh(new THREE.PlaneGeometry(240, 420), mat(0x6f9a52));
grass.rotation.x = -Math.PI / 2;
grass.position.z = -150;
scene.add(grass);

const road = new THREE.Mesh(new THREE.PlaneGeometry(9.2, 420), mat(0x3b3f45));
road.rotation.x = -Math.PI / 2;
road.position.set(0, 0.01, -150);
scene.add(road);

for (const x of [-4.75, 4.75]) {
  const curb = new THREE.Mesh(new THREE.BoxGeometry(0.3, 0.2, 420), mat(0xcfcfcf));
  curb.position.set(x, 0.1, -150);
  scene.add(curb);
}

// Things that scroll toward the camera and wrap around: lane dashes and buildings.
const scrollers = [];

const dashGeo = new THREE.BoxGeometry(0.16, 0.02, 3);
const dashMat = mat(0xf2f2f2);
const DASH_SPAN = 168;
for (let z = 10; z > 10 - DASH_SPAN; z -= 8) {
  for (const x of [-1.3, 1.3]) {
    const dash = new THREE.Mesh(dashGeo, dashMat);
    dash.position.set(x, 0.03, z);
    scene.add(dash);
    scrollers.push({ mesh: dash, span: DASH_SPAN });
  }
}

const buildingColors = [0x8a8f98, 0xa8836a, 0x6e7b8b, 0xb9a88f, 0x5d6470, 0x9c6b5a].map(mat);
const BUILDING_SPAN = 210;
for (let z = 10; z > 10 - BUILDING_SPAN; z -= 15) {
  for (const side of [-1, 1]) {
    const w = 4 + Math.random() * 4;
    const h = 5 + Math.random() * 16;
    const d = 5 + Math.random() * 5;
    const building = new THREE.Mesh(
      new THREE.BoxGeometry(w, h, d),
      buildingColors[Math.floor(Math.random() * buildingColors.length)],
    );
    building.position.set(side * (9 + Math.random() * 7), h / 2, z - Math.random() * 6);
    scene.add(building);
    scrollers.push({ mesh: building, span: BUILDING_SPAN });
  }
}

// Cars, cones and potholes share geometry so spawning is cheap.
const carParts = {
  body: new THREE.BoxGeometry(1.7, 0.6, 3.4),
  cabin: new THREE.BoxGeometry(1.4, 0.55, 1.7),
  wheel: new THREE.CylinderGeometry(0.35, 0.35, 0.3, 14).rotateZ(Math.PI / 2),
  cabinMat: mat(0x223344),
  wheelMat: mat(0x111111),
};
const trafficColors = [0x2f6db5, 0xf2f2f2, 0x1d1d1d, 0x8c8c8c, 0x2e8b57, 0xe0b100].map(mat);

function makeCar(bodyMaterial) {
  const car = new THREE.Group();
  const body = new THREE.Mesh(carParts.body, bodyMaterial);
  body.position.y = 0.6;
  car.add(body);
  const cabin = new THREE.Mesh(carParts.cabin, carParts.cabinMat);
  cabin.position.set(0, 1.15, 0.2);
  car.add(cabin);
  for (const [x, z] of [[-0.85, 1.1], [0.85, 1.1], [-0.85, -1.1], [0.85, -1.1]]) {
    const wheel = new THREE.Mesh(carParts.wheel, carParts.wheelMat);
    wheel.position.set(x, 0.35, z);
    car.add(wheel);
  }
  return car;
}

const coneParts = {
  cone: new THREE.ConeGeometry(0.35, 0.9, 16),
  base: new THREE.BoxGeometry(0.7, 0.08, 0.7),
  band: new THREE.CylinderGeometry(0.2, 0.25, 0.14, 16),
  orange: mat(0xff6a00),
  white: mat(0xffffff),
};

function makeCone() {
  const g = new THREE.Group();
  const base = new THREE.Mesh(coneParts.base, coneParts.orange);
  base.position.y = 0.04;
  const cone = new THREE.Mesh(coneParts.cone, coneParts.orange);
  cone.position.y = 0.5;
  const band = new THREE.Mesh(coneParts.band, coneParts.white);
  band.position.y = 0.55;
  g.add(base, cone, band);
  return g;
}

const potholeParts = {
  hole: new THREE.CylinderGeometry(1, 1, 0.03, 20),
  rim: new THREE.CylinderGeometry(1.15, 1.15, 0.02, 20),
  dark: mat(0x141414),
  crack: mat(0x55585c),
};

function makePothole() {
  const g = new THREE.Group();
  const rim = new THREE.Mesh(potholeParts.rim, potholeParts.crack);
  rim.position.y = 0.02;
  const hole = new THREE.Mesh(potholeParts.hole, potholeParts.dark);
  hole.position.y = 0.04;
  g.add(rim, hole);
  g.scale.z = 1.3;
  return g;
}

const builders = {
  car: () => makeCar(trafficColors[Math.floor(Math.random() * trafficColors.length)]),
  cone: makeCone,
  pothole: makePothole,
};

const player = makeCar(mat(0xd7263d));
scene.add(player);

function resize() {
  const w = window.innerWidth;
  const h = window.innerHeight;
  renderer.setSize(w, h, false);
  camera.aspect = w / h;
  camera.fov = w < h ? 80 : 60; // wider view on a phone held upright
  camera.updateProjectionMatrix();
}
window.addEventListener("resize", resize);
resize();

// ---------------------------------------------------------------------------
// Game state
// ---------------------------------------------------------------------------

let state = "READY";
let run = newRun();
let obstacles = [];
let targetLane = 1;
let elapsed = 0;
let speed = START_SPEED;
let distanceSinceSpawn = 0;

function newRun() {
  return {
    drivePlayed: false,
    drive: 0,
    crashed: false,
    crashTime: 0,
    hazard: null,
    sample: false,
    mechanicPlayed: false,
    answers: {},
    quotes: null, // Promise for the server's quote response
    quoteData: null,
    choice: null,
  };
}

function scrollScenery(distance) {
  for (const s of scrollers) {
    s.mesh.position.z += distance;
    if (s.mesh.position.z > 12) s.mesh.position.z -= s.span;
  }
}

function clearObstacles() {
  for (const o of obstacles) scene.remove(o.mesh);
  obstacles = [];
}

function spawnRow(progress) {
  const count = progress > 0.3 && Math.random() < 0.4 ? 2 : 1; // never block all three lanes
  for (const lane of shuffle([0, 1, 2]).slice(0, count)) {
    const type = pickWeighted(OBSTACLES);
    const mesh = builders[type]();
    mesh.position.set(LANES[lane], 0, SPAWN_Z - Math.random() * 6);
    scene.add(mesh);
    obstacles.push({ type, mesh });
  }
}

function drivePoints() {
  return Math.round(DRIVE_POINTS_MAX * Math.min(1, elapsed / ROUND_SECONDS));
}

function steer(direction) {
  if (state !== "DRIVING") return;
  targetLane = Math.max(0, Math.min(2, targetLane + direction));
}

function update(dt) {
  elapsed += dt;
  const progress = Math.min(1, elapsed / ROUND_SECONDS);
  speed = START_SPEED + (END_SPEED - START_SPEED) * progress;
  const move = speed * dt;

  scrollScenery(move);

  // Slide toward the chosen lane and lean into the turn.
  const dx = LANES[targetLane] - player.position.x;
  player.position.x += dx * Math.min(1, dt * 10);
  player.rotation.y = -dx * 0.08;
  player.rotation.z = -dx * 0.03;

  distanceSinceSpawn += move;
  if (distanceSinceSpawn >= 30 - 12 * progress) {
    spawnRow(progress);
    distanceSinceSpawn = 0;
  }

  for (const o of obstacles) {
    // Traffic cars drive away from you a little, so they close in slower.
    o.mesh.position.z += o.type === "car" ? move * 0.75 : move;
  }
  const passed = obstacles.filter((o) => o.mesh.position.z > 15);
  for (const o of passed) scene.remove(o.mesh);
  obstacles = obstacles.filter((o) => o.mesh.position.z <= 15);

  for (const o of obstacles) {
    const gapX = Math.abs(o.mesh.position.x - player.position.x);
    const gapZ = Math.abs(o.mesh.position.z - player.position.z);
    if (gapX < 1.45 && gapZ < OBSTACLES[o.type].halfLength + 1.6) {
      crash(o);
      return;
    }
  }

  $("hud-time").textContent = Math.max(0, ROUND_SECONDS - elapsed).toFixed(1);
  $("hud-speed").textContent = `${Math.round(speed * 1.6)} mph`;
  $("hud-points").textContent = drivePoints();

  if (elapsed >= ROUND_SECONDS) finishCleanRun();
}

// ---------------------------------------------------------------------------
// Screens
// ---------------------------------------------------------------------------

function showReady() {
  state = "READY";
  setDrivingUI(false);
  showPanel(
    el("p", "eyebrow", "RepairIQ Academy · Level 1"),
    el("h1", null, "Rush Hour on the Connector"),
    el(
      "p",
      null,
      `Survive ${ROUND_SECONDS} seconds of Atlanta traffic. Crash, and you're off to the mechanic: ` +
        "decide what to inspect, whether to repair or replace, and which of three shop quotes is fair.",
    ),
    el("p", "muted", "Steer with ← → or A / D. On a phone, tap the arrow buttons or swipe."),
    el("div", "actions"),
    el("p", "muted small", DISCLOSURE),
  );
  const actions = $("panel-body").querySelector(".actions");
  actions.append(
    button("Start driving", startDrive, true),
    button("Try Mechanic Challenge (sample scenario)", () => {
      run = newRun();
      startMechanic(randomHazard(), true);
    }),
  );
}

function startDrive() {
  clearObstacles();
  run = newRun();
  run.drivePlayed = true;
  targetLane = 1;
  player.position.x = LANES[1];
  player.rotation.set(0, 0, 0);
  elapsed = 0;
  speed = START_SPEED;
  distanceSinceSpawn = -20; // a short calm stretch before the first obstacle
  hidePanel();
  setDrivingUI(true);
  state = "DRIVING";
}

function crash(obstacle) {
  state = "MECHANIC";
  run.crashed = true;
  run.crashTime = elapsed;
  run.drive = drivePoints();
  const flash = $("flash");
  flash.classList.add("on");
  requestAnimationFrame(() => requestAnimationFrame(() => flash.classList.remove("on")));
  setTimeout(() => startMechanic(OBSTACLES[obstacle.type].hazard, false), 900);
}

function finishCleanRun() {
  state = "RESULTS";
  run.drive = DRIVE_POINTS_MAX;
  setDrivingUI(false);
  const tip = MAINTENANCE_TIPS[Math.floor(Math.random() * MAINTENANCE_TIPS.length)];
  showPanel(
    el("p", "eyebrow", "Clean run"),
    el("h2", null, `You made it! +${DRIVE_POINTS_MAX} driving points`),
    el("div", "feedback good"),
    el("p", null, "You still have 700 points to earn. Try the mechanic challenge to see how you'd handle a repair shop."),
    el("div", "actions"),
    el("p", "muted small", DISCLOSURE),
  );
  const body = $("panel-body");
  body.querySelector(".feedback").append(el("strong", null, "Preventive maintenance tip"), el("p", null, tip));
  body.querySelector(".actions").append(
    button("Take the Mechanic Challenge (sample scenario)", () => startMechanic(randomHazard(), true), true),
    button("Drive again", startDrive),
    button("Finish and see score", showResults),
  );
}

function randomHazard() {
  const keys = Object.keys(SCENARIOS);
  return keys[Math.floor(Math.random() * keys.length)];
}

// ---------------------------------------------------------------------------
// Mechanic challenge
// ---------------------------------------------------------------------------

async function requestQuotes(hazard) {
  const res = await fetch("/api/quotes", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hazards: [hazard] }),
  });
  if (!res.ok) throw new Error(`Server error ${res.status}`);
  return res.json();
}

function loadQuotes() {
  run.quotes = requestQuotes(run.hazard);
  run.quotes.catch(() => {}); // handled when step 3 awaits it
}

function startMechanic(hazard, sample) {
  state = "MECHANIC";
  setDrivingUI(false);
  run.hazard = hazard;
  run.sample = sample;
  run.mechanicPlayed = true;
  run.answers = {};
  run.choice = null;
  run.quoteData = null;
  loadQuotes(); // the AI writes quotes while the player answers steps 1 and 2
  showInspectStep();
}

function stepHeader(step, label) {
  const scenario = SCENARIOS[run.hazard];
  const parts = [el("p", "eyebrow", `Mechanic challenge · Step ${step} of 3 · ${label}`), el("h2", null, scenario.title)];
  if (run.sample) {
    parts.push(el("p", "notice", "Sample scenario: no crash happened. This is a practice repair so you can try the challenge."));
  }
  return parts;
}

function choiceStep({ step, label, intro, question, options, scoreKey, next }) {
  const list = el("div", "choices");
  const feedback = el("div", "feedback");
  feedback.hidden = true;
  const nextButton = button(step === 2 ? "Next: get quotes" : "Next", next, true);
  nextButton.hidden = true;

  for (const option of shuffle(options)) {
    const choice = el("button", "choice", option.text);
    choice.addEventListener("click", () => {
      if (scoreKey in run.answers) return;
      run.answers[scoreKey] = option.correct ? POINTS[scoreKey] : 0;
      for (const other of list.children) other.disabled = true;
      choice.classList.add(option.correct ? "right" : "wrong");
      feedback.className = `feedback ${option.correct ? "good" : "bad"}`;
      feedback.replaceChildren(
        el("strong", null, option.correct ? `Correct! +${POINTS[scoreKey]}` : "Not quite. +0"),
        el("p", null, option.explain),
      );
      if (!option.correct) {
        feedback.append(el("p", null, `Best answer: ${options.find((o) => o.correct).text}`));
      }
      feedback.hidden = false;
      nextButton.hidden = false;
    });
    list.append(choice);
  }

  showPanel(...stepHeader(step, label), ...intro, el("h3", null, question), list, feedback, nextButton);
}

function showInspectStep() {
  const scenario = SCENARIOS[run.hazard];
  choiceStep({
    step: 1,
    label: "Inspect",
    intro: [el("p", null, scenario.crash)],
    question: scenario.inspect.question,
    options: scenario.inspect.options,
    scoreKey: "inspect",
    next: showRepairStep,
  });
}

function showRepairStep() {
  const scenario = SCENARIOS[run.hazard];
  const finding = el("div", "finding");
  finding.append(el("strong", null, "Inspection finding"), el("p", null, scenario.repair.finding));
  finding.lastChild.style.marginBottom = "0";
  choiceStep({
    step: 2,
    label: "Repair or replace",
    intro: [finding],
    question: scenario.repair.question,
    options: scenario.repair.options,
    scoreKey: "repair",
    next: showQuoteStep,
  });
}

async function showQuoteStep() {
  const header = stepHeader(3, "Pick a quote");
  showPanel(...header, el("p", "muted", "The estimator is writing up three quotes…"));

  let data;
  try {
    data = await run.quotes;
  } catch {
    showPanel(
      ...stepHeader(3, "Pick a quote"),
      el("p", "feedback bad", "Couldn't reach the game server. Make sure `python server.py` is still running, then retry."),
      button("Retry", () => {
        loadQuotes();
        showQuoteStep();
      }, true),
    );
    return;
  }
  run.quoteData = data;

  const [low, high] = data.reference_range;
  const parts = [...stepHeader(3, "Pick a quote")];
  if (data.greeting) parts.push(el("p", "greeting", `“${data.greeting}”`));
  parts.push(
    el(
      "p",
      null,
      `Three shops quoted the repair. Fair range for this damage: ${money(low)} – ${money(high)} ` +
        "(illustrative game data, not a real quote). Which shop do you trust?",
    ),
  );
  if (data.notice) parts.push(el("p", "notice", `AI estimator unavailable (${data.notice}) Showing offline sample quotes.`));
  for (const warning of data.warnings || []) parts.push(el("p", "notice", warning));

  const shops = el("div", "shops");
  const cards = {};
  const letters = ["A", "B", "C"];
  shuffle(Object.keys(QUOTE_POINTS)).forEach((key, i) => {
    const quote = data.quotes[key];
    const card = el("div", "shop");
    card.dataset.key = key;
    const pick = button(`Choose Shop ${letters[i]}`, () => chooseQuote(key, cards, feedback, nextButton));
    card.append(el("h3", null, `Shop ${letters[i]}`), el("div", "price", money(quote.cost)), el("p", "desc", quote.description), pick);
    cards[key] = card;
    shops.append(card);
  });

  const feedback = el("div", "feedback");
  feedback.hidden = true;
  const nextButton = button("See my score", showResults, true);
  nextButton.hidden = true;

  parts.push(shops, feedback, nextButton, el("p", "muted small", data.source || ""));
  showPanel(...parts);
}

function chooseQuote(key, cards, feedback, nextButton) {
  if (run.choice) return;
  run.choice = key;
  run.answers.quote = QUOTE_POINTS[key];
  const quotes = run.quoteData.quotes;

  // Reveal what each shop really was.
  for (const [k, card] of Object.entries(cards)) {
    card.classList.add(`is-${k.replace("quote_", "")}`);
    if (k === key) card.classList.add("picked");
    card.querySelector("button").remove();
    const reveal = el("div", "reveal", `${quotes[k].title} · ${quotes[k].risk}`);
    card.insertBefore(reveal, card.querySelector(".price"));
  }

  const fair = quotes.quote_fair.cost;
  const dealer = quotes.quote_dealer.cost;
  const budget = quotes.quote_budget.cost;
  let good = false;
  let title;
  let text;
  if (key === "quote_fair") {
    good = true;
    title = `Smart choice! +${QUOTE_POINTS[key]}`;
    text = `You picked the certified independent shop: a safe repair at a fair price, and you skipped ${money(Math.max(0, dealer - fair))} of dealer padding.`;
  } else if (key === "quote_dealer") {
    title = `Safe, but you got upsold. +${QUOTE_POINTS[key]}`;
    text = `The repair is safe, but you paid ${money(Math.max(0, dealer - fair))} more than a fair shop would charge. Always ask for an itemized estimate.`;
  } else {
    title = `Cheap now, risky later. +${QUOTE_POINTS[key]}`;
    text = `You saved ${money(Math.max(0, fair - budget))}, but this shop cuts safety corners. A bad repair can fail at highway speed and cost more to redo.`;
  }
  feedback.className = `feedback ${good ? "good" : "bad"}`;
  feedback.replaceChildren(el("strong", null, title), el("p", null, text));
  feedback.hidden = false;
  nextButton.hidden = false;
}

// ---------------------------------------------------------------------------
// Results
// ---------------------------------------------------------------------------

function gradeFor(total) {
  if (total >= 850) return "A";
  if (total >= 700) return "B";
  if (total >= 550) return "C";
  if (total >= 400) return "D";
  return "F";
}

function showResults() {
  state = "RESULTS";
  setDrivingUI(false);
  const a = run.answers;
  const mechanic = run.mechanicPlayed ? (a.inspect || 0) + (a.repair || 0) + (a.quote || 0) : 0;
  const total = run.drive + mechanic;

  const heading = el("div", "score", `${total.toLocaleString("en-US")} / 1,000`);
  heading.append(el("span", "grade", gradeFor(total)));

  const rows = [];
  if (run.drivePlayed) {
    const how = run.crashed ? `crashed at ${run.crashTime.toFixed(1)}s` : "clean run";
    rows.push(["Driving", `${run.drive} / ${DRIVE_POINTS_MAX} (${how})`]);
  } else {
    rows.push(["Driving", "not played (sample scenario)"]);
  }
  if (run.mechanicPlayed) {
    rows.push(["What to inspect", `${a.inspect || 0} / ${POINTS.inspect}`]);
    rows.push(["Repair or replace", `${a.repair || 0} / ${POINTS.repair}`]);
    rows.push(["Quote choice", `${a.quote || 0} / ${QUOTE_POINTS.quote_fair}`]);
  } else {
    rows.push(["Mechanic challenge", "not played"]);
  }
  const list = el("ul", "breakdown");
  for (const [name, value] of rows) {
    const li = el("li");
    li.append(el("span", null, name), el("strong", null, value));
    list.append(li);
  }

  const parts = [el("p", "eyebrow", "Results"), el("h2", null, "Your score"), heading, list];

  const tips = run.quoteData?.tips || [];
  if (tips.length) {
    parts.push(el("h3", null, "🛡️ Ask these before you sign anything"));
    const ul = el("ul", "tips");
    for (const tip of tips) ul.append(el("li", null, tip));
    parts.push(ul);
  }

  const actions = el("div", "actions");
  actions.append(
    button("Drive again", startDrive, true),
    button("Try another Mechanic Challenge", () => {
      run = newRun();
      startMechanic(randomHazard(), true);
    }),
    button("Main menu", showReady),
  );
  parts.push(actions, el("p", "muted small", DISCLOSURE));
  showPanel(...parts);
}

// ---------------------------------------------------------------------------
// Input
// ---------------------------------------------------------------------------

window.addEventListener("keydown", (e) => {
  if (state !== "DRIVING") return;
  if (e.key === "ArrowLeft" || e.key === "a" || e.key === "A") {
    steer(-1);
    e.preventDefault();
  } else if (e.key === "ArrowRight" || e.key === "d" || e.key === "D") {
    steer(1);
    e.preventDefault();
  }
});

$("btn-left").addEventListener("pointerdown", (e) => {
  e.preventDefault();
  steer(-1);
});
$("btn-right").addEventListener("pointerdown", (e) => {
  e.preventDefault();
  steer(1);
});

let swipeStartX = null;
canvas.addEventListener("pointerdown", (e) => {
  swipeStartX = e.clientX;
});
canvas.addEventListener("pointerup", (e) => {
  if (swipeStartX === null) return;
  const dx = e.clientX - swipeStartX;
  swipeStartX = null;
  if (Math.abs(dx) > 30) steer(dx > 0 ? 1 : -1);
});

// ---------------------------------------------------------------------------
// Main loop
// ---------------------------------------------------------------------------

const clock = new THREE.Clock();

function frame() {
  const dt = Math.min(clock.getDelta(), 0.05);
  if (state === "DRIVING") update(dt);
  else if (state === "READY") scrollScenery(10 * dt);
  renderer.render(scene, camera);
  requestAnimationFrame(frame);
}

showReady();
frame();
