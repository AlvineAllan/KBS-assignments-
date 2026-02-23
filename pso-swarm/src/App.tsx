import { useState, useRef, useEffect, useCallback } from "react";
import type { CSSProperties } from "react";

// ═══════════════════════════════════════════════════════════════
//  PSO OPTIMIZER  —  Particle Swarm Optimization Dashboard
//  Applied to: Mathematical Function Optimization
// ═══════════════════════════════════════════════════════════════

// ── Color Palette ─────────────────────────────────────────────
const C = {
  bg:      "#0d0f00",
  surface: "#141800",
  border:  "#3a3d00",
  accent:  "#f5d800",
  green:   "#aacc00",
  orange:  "#ffaa00",
  red:     "#ff5533",
  purple:  "#ddcc44",
  text:    "#f0eecc",
  muted:   "#999966",
  dim:     "#222400",
} as const;

// ── Types ─────────────────────────────────────────────────────
interface FnDef {
  name: string;
  equation: string;
  fn: (x: number, y: number) => number;
  min: [number, number];
  minVal: number;
  range: number;
  difficulty: "Easy" | "Medium" | "Hard";
  about: string;
}

interface Particle {
  id: number;
  x: number; y: number;
  vx: number; vy: number;
  bx: number; by: number;
  bf: number;
}

interface GBest {
  x: number;
  y: number;
  fitness: number;
}

interface HistPoint {
  i: number;
  f: number;
}

interface LogEvent {
  tag: string;
  color: string;
  text: string;
}

type FnKey = "sphere" | "rosenbrock" | "rastrigin" | "ackley";

// ── Benchmark Functions ───────────────────────────────────────
const FNS: Record<FnKey, FnDef> = {
  sphere: {
    name: "Sphere",
    equation: "f(x,y) = x² + y²",
    fn: (x: number, y: number) => x * x + y * y,
    min: [0, 0], minVal: 0, range: 5,
    difficulty: "Easy",
    about: "Simple convex bowl. Global minimum at origin (0,0). PSO converges quickly — good starting point.",
  },
  rosenbrock: {
    name: "Rosenbrock",
    equation: "f(x,y) = 100(y−x²)² + (1−x)²",
    fn: (x: number, y: number) => 100 * Math.pow(y - x * x, 2) + Math.pow(1 - x, 2),
    min: [1, 1], minVal: 0, range: 3,
    difficulty: "Medium",
    about: "Banana-shaped curved valley. Minimum at (1,1). Hard to follow the valley floor — tests velocity tuning.",
  },
  rastrigin: {
    name: "Rastrigin",
    equation: "f(x,y) = 20 + Σ[xᵢ² − 10cos(2πxᵢ)]",
    fn: (x: number, y: number) =>
      20 + x * x - 10 * Math.cos(2 * Math.PI * x) + y * y - 10 * Math.cos(2 * Math.PI * y),
    min: [0, 0], minVal: 0, range: 5,
    difficulty: "Hard",
    about: "Highly multimodal surface. Many local minima trap particles. Tests global exploration of the swarm.",
  },
  ackley: {
    name: "Ackley",
    equation: "f(x,y) = −20e^(−0.2√(0.5Σxᵢ²)) − e^(0.5Σcos(2πxᵢ)) + e + 20",
    fn: (x: number, y: number) =>
      -20 * Math.exp(-0.2 * Math.sqrt(0.5 * (x * x + y * y))) -
      Math.exp(0.5 * (Math.cos(2 * Math.PI * x) + Math.cos(2 * Math.PI * y))) +
      Math.E + 20,
    min: [0, 0], minVal: 0, range: 4,
    difficulty: "Hard",
    about: "Deceptive flat outer region with a deep hole at origin. Classic benchmark for global optimizers.",
  },
};

// ── PSO Engine ────────────────────────────────────────────────
function createSwarm(n: number, range: number): Particle[] {
  return Array.from({ length: n }, (_, id) => {
    const x = (Math.random() * 2 - 1) * range;
    const y = (Math.random() * 2 - 1) * range;
    return { id, x, y, vx: (Math.random() - 0.5) * range * 0.3, vy: (Math.random() - 0.5) * range * 0.3, bx: x, by: y, bf: Infinity };
  });
}

function psoStep(
  particles: Particle[],
  gbest: GBest,
  fnKey: FnKey,
  w: number, c1: number, c2: number
): { particles: Particle[]; gbest: GBest } {
  const { fn, range } = FNS[fnKey];
  let g: GBest = { ...gbest };
  const next: Particle[] = particles.map((p) => {
    const r1 = Math.random(), r2 = Math.random();
    let vx = w * p.vx + c1 * r1 * (p.bx - p.x) + c2 * r2 * (g.x - p.x);
    let vy = w * p.vy + c1 * r1 * (p.by - p.y) + c2 * r2 * (g.y - p.y);
    const vm = range * 0.4;
    vx = Math.max(-vm, Math.min(vm, vx));
    vy = Math.max(-vm, Math.min(vm, vy));
    const nx = Math.max(-range, Math.min(range, p.x + vx));
    const ny = Math.max(-range, Math.min(range, p.y + vy));
    const fit = fn(nx, ny);
    const improved = fit < p.bf;
    if (fit < g.fitness) g = { x: nx, y: ny, fitness: fit };
    return { ...p, x: nx, y: ny, vx, vy, bx: improved ? nx : p.bx, by: improved ? ny : p.by, bf: improved ? fit : p.bf };
  });
  return { particles: next, gbest: g };
}

// ── Helpers ───────────────────────────────────────────────────
function fmt(n: number, d = 5): string {
  return isFinite(n) ? n.toFixed(d) : "—";
}
function fmtE(n: number): string {
  return isFinite(n) ? n.toExponential(3) : "—";
}
function diffColor(d: "Easy" | "Medium" | "Hard"): string {
  return d === "Easy" ? C.green : d === "Medium" ? C.orange : C.red;
}

// ── Runtime state ref (avoids stale closure in interval) ──────
interface RunState {
  particles: Particle[];
  gbest: GBest;
  iter: number;
}

// ═══════════════════════════════════════════════════════════════
//  COMPONENT
// ═══════════════════════════════════════════════════════════════
export default function App() {
  const [fnKey,   setFnKey]   = useState<FnKey>("sphere");
  const [n,       setN]       = useState<number>(25);
  const [w,       setW]       = useState<number>(0.72);
  const [c1,      setC1]      = useState<number>(1.49);
  const [c2,      setC2]      = useState<number>(1.49);
  const [maxIter, setMaxIter] = useState<number>(100);

  const [status,    setStatus]    = useState<"idle" | "running" | "done">("idle");
  const [iter,      setIter]      = useState<number>(0);
  const [particles, setParticles] = useState<Particle[]>([]);
  const [gbest,     setGbest]     = useState<GBest>({ x: 0, y: 0, fitness: Infinity });
  const [history,   setHistory]   = useState<HistPoint[]>([]);
  const [events,    setEvents]    = useState<LogEvent[]>([
    { tag: "INFO", color: C.accent,  text: "PSO Optimizer loaded. Configure parameters and press Run." },
    { tag: "INFO", color: C.accent,  text: "Algorithm: Kennedy & Eberhart (1995) — Particle Swarm Optimization." },
    { tag: "ALGO", color: C.purple,  text: "v(t+1) = w·v(t) + c1·r1·(pBest−x) + c2·r2·(gBest−x)" },
    { tag: "ALGO", color: C.purple,  text: "x(t+1) = x(t) + v(t+1)" },
  ]);

  const timerRef  = useRef<ReturnType<typeof setInterval> | null>(null);
  const logRef    = useRef<HTMLDivElement>(null);
  const stateRef  = useRef<RunState>({ particles: [], gbest: { x: 0, y: 0, fitness: Infinity }, iter: 0 });

  const addEvent = useCallback((tag: string, color: string, text: string) => {
    setEvents((prev) => [...prev, { tag, color, text }].slice(-80));
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 20);
  }, []);

  const stop = useCallback(() => {
    if (timerRef.current) { clearInterval(timerRef.current); timerRef.current = null; }
    setStatus("done");
  }, []);

  const run = useCallback(() => {
    if (timerRef.current) clearInterval(timerRef.current);
    const { fn, range } = FNS[fnKey];
    const sw = createSwarm(n, range);
    let g: GBest = { x: 0, y: 0, fitness: Infinity };
    sw.forEach((p) => {
      const f = fn(p.x, p.y);
      p.bf = f; p.bx = p.x; p.by = p.y;
      if (f < g.fitness) g = { x: p.x, y: p.y, fitness: f };
    });
    stateRef.current = { particles: sw, gbest: g, iter: 0 };
    setParticles([...sw]);
    setGbest({ ...g });
    setIter(0);
    setHistory([{ i: 0, f: g.fitness }]);
    setStatus("running");

    addEvent("RUN",  C.green,  "── Starting: " + FNS[fnKey].name + " | N=" + n + " w=" + w + " c1=" + c1 + " c2=" + c2);
    addEvent("INIT", C.orange, "Swarm initialised. Initial gBest = " + g.fitness.toExponential(3));

    timerRef.current = setInterval(() => {
      const s = stateRef.current;
      const res = psoStep(s.particles, s.gbest, fnKey, w, c1, c2);
      const ni = s.iter + 1;
      stateRef.current = { particles: res.particles, gbest: res.gbest, iter: ni };
      setParticles([...res.particles]);
      setGbest({ ...res.gbest });
      setIter(ni);
      setHistory((h) => [...h, { i: ni, f: res.gbest.fitness }].slice(-150));

      if (ni % 10 === 0 || ni <= 3) {
        const tag = res.gbest.fitness < 0.001 ? "BEST" : "ITER";
        const col = res.gbest.fitness < 0.001 ? C.green : C.accent;
        addEvent(tag, col,
          "[" + String(ni).padStart(3, "0") + "]  fitness = " + res.gbest.fitness.toExponential(4) +
          "  pos = (" + res.gbest.x.toFixed(3) + ", " + res.gbest.y.toFixed(3) + ")"
        );
      }
      if (ni >= maxIter || res.gbest.fitness < 1e-7) {
        clearInterval(timerRef.current!);
        timerRef.current = null;
        setStatus("done");
        const quality = res.gbest.fitness < 0.001 ? "EXCELLENT" : res.gbest.fitness < 1 ? "GOOD" : "POOR";
        const qcol    = res.gbest.fitness < 0.001 ? C.green : res.gbest.fitness < 1 ? C.orange : C.red;
        addEvent("DONE", qcol, "── Finished at iter " + ni + " | " + quality + " convergence");
        addEvent("DONE", qcol, "   gBest fitness = " + res.gbest.fitness.toExponential(4));
        addEvent("DONE", qcol, "   gBest pos     = (" + res.gbest.x.toFixed(5) + ", " + res.gbest.y.toFixed(5) + ")");
        addEvent("DONE", qcol, "   Known min     = (" + FNS[fnKey].min.join(", ") + ")");
      }
    }, 75);
  }, [fnKey, n, w, c1, c2, maxIter, addEvent]);

  const reset = useCallback(() => {
    stop();
    setParticles([]);
    setGbest({ x: 0, y: 0, fitness: Infinity });
    setIter(0);
    setHistory([]);
    setStatus("idle");
    addEvent("INFO", C.muted, "System reset.");
  }, [stop, addEvent]);

  useEffect(() => () => { if (timerRef.current) clearInterval(timerRef.current); }, []);

  // ── SVG canvas helpers ────────────────────────────────────────
  const { range } = FNS[fnKey];
  const SW = 370, SH = 320;
  const px = (v: number) => SW / 2 + (v / range) * (SW / 2 - 18);
  const py = (v: number) => SH / 2 - (v / range) * (SH / 2 - 18);

  // convergence sparkline
  const sparkW = 340, sparkH = 52;
  const sparkLine = (): string => {
    if (history.length < 2) return "";
    const mx = Math.max(...history.map((h) => h.f));
    const mn = Math.min(...history.map((h) => h.f));
    const span = mx - mn || 1;
    return history.map((h, i) => {
      const cx = (i / (history.length - 1)) * sparkW;
      const cy = sparkH - 4 - ((h.f - mn) / span) * (sparkH - 8);
      return cx + "," + cy;
    }).join(" ");
  };

  const statusColor = status === "running" ? C.green : status === "done" ? C.orange : C.muted;
  const statusText  = status === "running" ? "● RUNNING" : "■ " + (status === "done" ? "FINISHED" : "IDLE");

  // ── Render ────────────────────────────────────────────────────
  return (
    <div style={r.wrap}>

      {/* ── TOP NAV ── */}
      <div style={r.nav}>
        <div style={r.navLeft}>
          <div style={r.navLogo}>⬡ PSO</div>
          <span style={r.navTitle}>Particle Swarm Optimizer</span>
          <span style={r.navSub}>Population-Based Metaheuristic · 2D Function Minimization</span>
        </div>
        <div style={r.navRight}>
          <span style={{ ...r.pill, background: status === "running" ? "#1a3a00" : "#1a1a00", color: statusColor, borderColor: statusColor }}>
            {statusText}
          </span>
          {status === "running" && <span style={r.iterBadge}>iter {iter} / {maxIter}</span>}
        </div>
      </div>

      {/* ── MAIN GRID ── */}
      <div style={r.grid}>

        {/* ── COL A: Config ── */}
        <div style={r.colA}>

          {/* Function selector */}
          <div style={r.card}>
            <div style={r.cardHead}>OBJECTIVE FUNCTION</div>
            <div style={{ display: "flex", flexDirection: "column" as const, gap: 5 }}>
              {(Object.entries(FNS) as [FnKey, FnDef][]).map(([k, v]) => (
                <button key={k} onClick={() => setFnKey(k)} disabled={status === "running"} style={{
                  ...r.fnBtn,
                  background: fnKey === k ? "#1c2800" : "transparent",
                  borderColor: fnKey === k ? C.accent : C.border,
                  color: fnKey === k ? C.accent : C.muted,
                }}>
                  <span style={{ fontWeight: fnKey === k ? 700 : 400, fontSize: 13 }}>{v.name}</span>
                  <span style={{ fontSize: 10, color: diffColor(v.difficulty) }}>{v.difficulty}</span>
                </button>
              ))}
            </div>
            <div style={r.eqBox}>
              <div style={{ color: C.purple, fontSize: 11, marginBottom: 4, letterSpacing: 1 }}>EQUATION</div>
              <div style={{ color: C.text, fontSize: 12, fontFamily: "'Georgia',serif", marginBottom: 6 }}>{FNS[fnKey].equation}</div>
              <div style={{ color: C.muted, fontSize: 11, lineHeight: 1.6 }}>{FNS[fnKey].about}</div>
              <div style={{ marginTop: 6, display: "flex", gap: 12 }}>
                <span style={{ fontSize: 10, color: C.muted }}>Known min: <span style={{ color: C.green }}>({FNS[fnKey].min.join(", ")})</span></span>
                <span style={{ fontSize: 10, color: C.muted }}>Range: <span style={{ color: C.accent }}>[−{range}, {range}]²</span></span>
              </div>
            </div>
          </div>

          {/* Parameters */}
          <div style={r.card}>
            <div style={r.cardHead}>PARAMETERS</div>
            <div style={{ display: "flex", flexDirection: "column" as const, gap: 8 }}>
              {([
                { label: "Particles  N", val: n,       set: setN,       min: 5,  max: 60,  step: 1,    hint: "Swarm size — more = better exploration" },
                { label: "Inertia  w",   val: w,       set: setW,       min: 0,  max: 1,   step: 0.01, hint: "Controls momentum. 0.7–0.9 recommended" },
                { label: "Cognitive c₁", val: c1,      set: setC1,      min: 0,  max: 4,   step: 0.01, hint: "Pull toward personal best" },
                { label: "Social  c₂",   val: c2,      set: setC2,      min: 0,  max: 4,   step: 0.01, hint: "Pull toward global best" },
                { label: "Max Iter",      val: maxIter, set: setMaxIter, min: 10, max: 500, step: 10,   hint: "Maximum iterations before stopping" },
              ] as { label: string; val: number; set: (v: number) => void; min: number; max: number; step: number; hint: string }[]).map((p) => (
                <div key={p.label} style={{ display: "flex", flexDirection: "column" as const, gap: 2 }}>
                  <div style={{ display: "flex", justifyContent: "space-between" }}>
                    <span style={r.paramLabel}>{p.label}</span>
                    <span style={r.paramVal}>{p.val}</span>
                  </div>
                  <input type="range" min={p.min} max={p.max} step={p.step} value={p.val}
                    onChange={(e) => p.set(+e.target.value)} disabled={status === "running"}
                    style={r.slider} />
                  <div style={r.paramHint}>{p.hint}</div>
                </div>
              ))}
            </div>
            <div style={{ display: "flex", gap: 8, marginTop: 12 }}>
              <button style={{ ...r.actionBtn, background: C.green, color: "#0d0f00", border: "none" }}
                onClick={run} disabled={status === "running"}>▶ Run</button>
              <button style={{ ...r.actionBtn, background: "transparent", color: C.red, border: "1px solid " + C.red }}
                onClick={stop} disabled={status !== "running"}>■ Stop</button>
              <button style={{ ...r.actionBtn, background: "transparent", color: C.muted, border: "1px solid " + C.border }}
                onClick={reset} disabled={status === "running"}>↺ Reset</button>
            </div>
          </div>
        </div>

        {/* ── COL B: Canvas ── */}
        <div style={r.colB}>
          <div style={r.card}>
            <div style={r.cardHead}>SEARCH SPACE  ·  LIVE SWARM</div>
            <svg width={SW} height={SH} style={r.svgCanvas}>
              <defs>
                <filter id="gp">
                  <feGaussianBlur stdDeviation="3" result="b"/>
                  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
                <filter id="gg">
                  <feGaussianBlur stdDeviation="5" result="b"/>
                  <feMerge><feMergeNode in="b"/><feMergeNode in="SourceGraphic"/></feMerge>
                </filter>
              </defs>

              {/* grid */}
              {[-4, -3, -2, -1, 0, 1, 2, 3, 4].map((v) => (
                <g key={v}>
                  <line x1={px(v)} y1={10} x2={px(v)} y2={SH - 10} stroke={C.border} strokeWidth="0.5" opacity="0.6" />
                  <line x1={10} y1={py(v)} x2={SW - 10} y2={py(v)} stroke={C.border} strokeWidth="0.5" opacity="0.6" />
                </g>
              ))}
              {/* axes */}
              <line x1={SW / 2} y1={8} x2={SW / 2} y2={SH - 8} stroke={C.dim} strokeWidth="1.2" />
              <line x1={8} y1={SH / 2} x2={SW - 8} y2={SH / 2} stroke={C.dim} strokeWidth="1.2" />
              <text x={SW - 14} y={SH / 2 - 5} fill={C.muted} fontSize="10" fontFamily="'Segoe UI',sans-serif">x</text>
              <text x={SW / 2 + 5} y={16}        fill={C.muted} fontSize="10" fontFamily="'Segoe UI',sans-serif">y</text>
              {([-range, range] as number[]).map((v) => (
                <g key={v}>
                  <text x={px(v) - 8} y={SH / 2 + 14} fill={C.border} fontSize="8" fontFamily="monospace">{v}</text>
                  <text x={SW / 2 + 4} y={py(v) + 4}   fill={C.border} fontSize="8" fontFamily="monospace">{v}</text>
                </g>
              ))}

              {/* known global min ring */}
              {(() => {
                const [gx, gy] = FNS[fnKey].min;
                return (
                  <g>
                    <circle cx={px(gx)} cy={py(gy)} r={12} fill="none" stroke={C.green} strokeWidth="1" strokeDasharray="3,3" opacity="0.5" />
                    <circle cx={px(gx)} cy={py(gy)} r={3}  fill={C.green} opacity="0.4" />
                  </g>
                );
              })()}

              {/* pBest ghosts */}
              {particles.map((p) => (
                <circle key={"pb" + p.id} cx={px(p.bx)} cy={py(p.by)} r={2} fill={C.accent} opacity="0.18" />
              ))}

              {/* velocity lines */}
              {particles.map((p) => (
                <line key={"v" + p.id}
                  x1={px(p.x)} y1={py(p.y)}
                  x2={px(p.x) + p.vx * 20} y2={py(p.y) - p.vy * 20}
                  stroke={C.accent} strokeWidth="0.6" opacity="0.3" />
              ))}

              {/* particles */}
              {particles.map((p) => (
                <circle key={"p" + p.id} cx={px(p.x)} cy={py(p.y)}
                  r={4.5} fill={C.accent} opacity={0.8} filter="url(#gp)" />
              ))}

              {/* gBest star */}
              {gbest.fitness < Infinity && (
                <g filter="url(#gg)">
                  <circle cx={px(gbest.x)} cy={py(gbest.y)} r={7}
                    fill={C.orange} stroke="#fff" strokeWidth="1.5" opacity="0.95" />
                  <text x={px(gbest.x) + 10} y={py(gbest.y) - 8}
                    fill={C.orange} fontSize="9" fontFamily="'Segoe UI',sans-serif">gBest</text>
                </g>
              )}
            </svg>

            {/* legend */}
            <div style={{ display: "flex", gap: 14, marginTop: 8, flexWrap: "wrap" as const }}>
              {([[C.accent, "Particle"], [C.orange, "Global Best"], [C.green, "Known Min"], [C.accent, "pBest trail"]] as [string, string][]).map(([c, l]) => (
                <span key={l} style={{ display: "flex", alignItems: "center", gap: 5 }}>
                  <span style={{ width: 8, height: 8, borderRadius: "50%", background: c, display: "inline-block" }} />
                  <span style={{ color: C.muted, fontSize: 10 }}>{l}</span>
                </span>
              ))}
            </div>
          </div>

          {/* Convergence chart + stats */}
          <div style={r.card}>
            <div style={r.cardHead}>CONVERGENCE  ·  gBest FITNESS OVER ITERATIONS</div>
            <svg width={sparkW} height={sparkH + 10} style={{ display: "block" }}>
              <rect x={0} y={0} width={sparkW} height={sparkH} fill={C.bg} rx={3} />
              {history.length > 1 && <polyline points={sparkLine()} fill="none" stroke={C.orange} strokeWidth="1.8" />}
              <text x={2}           y={sparkH - 2} fill={C.border} fontSize="8" fontFamily="monospace">0</text>
              <text x={sparkW - 20} y={sparkH - 2} fill={C.border} fontSize="8" fontFamily="monospace">{iter}</text>
            </svg>
            <div style={{ display: "flex", gap: 8, marginTop: 10, flexWrap: "wrap" as const }}>
              {([
                { l: "gBest Fitness", v: fmtE(gbest.fitness), c: C.orange },
                { l: "Position X",    v: fmt(gbest.x, 4),      c: C.accent },
                { l: "Position Y",    v: fmt(gbest.y, 4),      c: C.accent },
                { l: "Iteration",     v: iter + " / " + maxIter, c: C.text },
                { l: "Particles",     v: String(n),              c: C.purple },
              ] as { l: string; v: string; c: string }[]).map((s) => (
                <div key={s.l} style={r.statBox}>
                  <div style={{ color: C.muted, fontSize: 9, letterSpacing: 1, marginBottom: 2 }}>{s.l.toUpperCase()}</div>
                  <div style={{ color: s.c, fontSize: 13, fontWeight: 700 }}>{s.v}</div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* ── COL C: Algo + Log ── */}
        <div style={r.colC}>

          {/* Algorithm steps */}
          <div style={r.card}>
            <div style={r.cardHead}>HOW PSO WORKS</div>
            <div style={{ display: "flex", flexDirection: "column" as const, gap: 10 }}>
              {([
                { step: "01", title: "Initialise",      body: "Scatter N particles randomly across the search space. Each gets a random position (x,y) and random initial velocity." },
                { step: "02", title: "Evaluate",        body: "Compute f(x,y) for every particle. Set each particle's personal best (pBest) to its starting position." },
                { step: "03", title: "Update gBest",    body: "Scan all pBest values. Whichever has the lowest fitness becomes the new global best — shared by the whole swarm." },
                { step: "04", title: "Update Velocity", body: "v = w·v + c1·r1·(pBest−x) + c2·r2·(gBest−x). Inertia + cognitive pull + social pull." },
                { step: "05", title: "Move Particle",   body: "x = x + v. Add new velocity to position. Clamp to stay inside the search boundary." },
                { step: "06", title: "Repeat",          body: "Return to step 2. Iterate until maxIter reached or fitness drops below threshold." },
              ] as { step: string; title: string; body: string }[]).map((s) => (
                <div key={s.step} style={{ display: "flex", gap: 10, alignItems: "flex-start" }}>
                  <div style={r.algoNum}>{s.step}</div>
                  <div>
                    <div style={{ color: C.text, fontWeight: 600, fontSize: 12, marginBottom: 2 }}>{s.title}</div>
                    <div style={{ color: C.muted, fontSize: 11, lineHeight: 1.55 }}>{s.body}</div>
                  </div>
                </div>
              ))}
            </div>
          </div>

          {/* Event log */}
          <div style={r.card}>
            <div style={r.cardHead}>EVENT LOG</div>
            <div style={r.logBox} ref={logRef}>
              {events.map((e, i) => (
                <div key={i} style={{ display: "flex", alignItems: "flex-start", gap: 7 }}>
                  <span style={{ ...r.logTag, color: e.color, borderColor: e.color + "44" }}>{e.tag}</span>
                  <span style={{ color: C.muted, fontSize: 11 }}>{e.text}</span>
                </div>
              ))}
              <div style={{ color: C.border, fontSize: 12 }}>▌</div>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}

// ── Styles ─────────────────────────────────────────────────────
const r: Record<string, CSSProperties> = {
  wrap: {
    position: "fixed", inset: 0,
    background: C.bg, color: C.text,
    fontFamily: "'Segoe UI', 'Inter', system-ui, sans-serif",
    display: "flex", flexDirection: "column",
    overflow: "hidden",
  },
  nav: {
    display: "flex", alignItems: "center", justifyContent: "space-between",
    padding: "10px 20px", borderBottom: "1px solid " + C.border,
    background: C.bg, flexShrink: 0,
  },
  navLeft:   { display: "flex", alignItems: "center", gap: 12 },
  navLogo:   { background: C.accent, color: "#0d0f00", padding: "4px 10px", fontSize: 13, fontWeight: 800, borderRadius: 4 },
  navTitle:  { fontSize: 14, fontWeight: 600, color: C.text },
  navSub:    { fontSize: 11, color: C.muted },
  navRight:  { display: "flex", alignItems: "center", gap: 10 },
  pill: {
    fontSize: 11, fontWeight: 600, padding: "3px 10px", borderRadius: 12,
    border: "1px solid", letterSpacing: 1,
  },
  iterBadge: { fontSize: 11, color: C.muted },

  grid: {
    display: "grid", gridTemplateColumns: "220px 1fr 260px",
    gap: 12, padding: 12, flex: 1, minHeight: 0, overflow: "hidden",
  },
  colA: { display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" },
  colB: { display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" },
  colC: { display: "flex", flexDirection: "column", gap: 12, overflowY: "auto" },

  card: {
    background: C.surface, border: "1px solid " + C.border,
    borderRadius: 6, padding: "12px 14px",
  },
  cardHead: {
    fontSize: 9, fontWeight: 700, letterSpacing: 2,
    color: C.muted, textTransform: "uppercase",
    marginBottom: 10, paddingBottom: 6,
    borderBottom: "1px solid " + C.border,
  },

  fnBtn: {
    display: "flex", justifyContent: "space-between", alignItems: "center",
    padding: "7px 10px", border: "1px solid",
    borderRadius: 4, cursor: "pointer", fontFamily: "inherit",
    transition: "all 0.15s",
  },
  eqBox: {
    marginTop: 10, padding: "8px 10px",
    background: C.bg, borderRadius: 4, border: "1px solid " + C.border,
  },

  paramLabel: { fontSize: 11, color: C.muted },
  paramVal:   { fontSize: 11, color: C.accent, fontWeight: 600 },
  paramHint:  { fontSize: 10, color: C.border },
  slider:     { width: "100%", accentColor: C.accent, cursor: "pointer" },

  actionBtn: {
    flex: 1, padding: "7px 0", borderRadius: 4,
    cursor: "pointer",
    fontFamily: "'Segoe UI',sans-serif", fontSize: 12, fontWeight: 600,
    letterSpacing: 0.5,
  },

  svgCanvas: { background: "#090d00", border: "1px solid " + C.border, borderRadius: 4, display: "block" },

  statBox: {
    background: C.bg, border: "1px solid " + C.border,
    borderRadius: 4, padding: "6px 10px", flex: "1 1 60px",
  },

  algoNum: {
    minWidth: 26, height: 26, borderRadius: "50%",
    background: C.dim, border: "1px solid " + C.border,
    display: "flex", alignItems: "center", justifyContent: "center",
    fontSize: 10, fontWeight: 700, color: C.muted, flexShrink: 0,
  },

  logBox: {
    overflowY: "auto",
    display: "flex", flexDirection: "column", gap: 4,
    maxHeight: 240,
  },
  logTag: {
    fontSize: 9, fontWeight: 700, letterSpacing: 1,
    padding: "1px 5px", border: "1px solid",
    borderRadius: 3, flexShrink: 0, marginTop: 1,
  },
};