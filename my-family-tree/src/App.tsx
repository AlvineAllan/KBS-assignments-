import React, { useState, useCallback, useRef } from "react";
import TreeComponent from "react-d3-tree";
import type { RawNodeDatum, CustomNodeElementProps } from "react-d3-tree";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Tree = TreeComponent as any;

// ── Types ────────────────────────────────────────────────────────────────────
interface PersonNode extends RawNodeDatum {
  name: string;
  attributes: { gender: "male" | "female"; spouse: string };
  children?: PersonNode[];
}
interface LogEntry {
  type: "system" | "query" | "binding" | "result" | "error";
  text: string;
}
interface Binding { [key: string]: string; }
interface QueryResult {
  type: "result" | "error";
  bindings?: Binding[];
  msg?: string;
}

// ── Constants ────────────────────────────────────────────────────────────────
const MAX_LOG = 30;
const BASE          = "#041824";
const GREEN         = "#33ddff";
const DGREEN        = "#88ffff";
const DIM           = "#1a4a60";
const YELLOW        = "#ffcc44";
const RED           = "#ff6666";
const MALE_BG       = "#062a48";
const MALE_STROKE   = "#1199ee";
const MALE_TEXT     = "#ffffff";
const FEMALE_BG     = "#3a1400";
const FEMALE_STROKE = "#ff7722";
const FEMALE_TEXT   = "#ffffff";
const SPOUSE_BG     = "#1a2a0a";
const SPOUSE_STROKE = "#66cc44";
const SPOUSE_TEXT   = "#ffffff";

// ── Knowledge Base ───────────────────────────────────────────────────────────
const spouseMap: Record<string, string> = {
  "Alistair": "Margaret", "Margaret": "Alistair",
  "Rowan":    "Sylvia",   "Sylvia":   "Rowan",
  "Vivienne": "Edmund",   "Edmund":   "Vivienne",
  "Theo":     "Petra",    "Petra":    "Theo",
};

const spouseSet = new Set(["Margaret", "Sylvia", "Edmund", "Petra"]);

const genderMap: Record<string, "male" | "female"> = {
  "Alistair": "male",   "Margaret": "female",
  "Rowan":    "male",   "Sylvia":   "female",
  "Vivienne": "female", "Edmund":   "male",
  "Theo":     "male",   "Petra":    "female",
  "Celeste":  "female", "Jasper":   "male",
  "Isolde":   "female",
};

const familyTree: PersonNode = {
  name: "Alistair",
  attributes: { gender: "male", spouse: "Margaret" },
  children: [
    {
      name: "Rowan",
      attributes: { gender: "male", spouse: "Sylvia" },
      children: [
        {
          name: "Theo",
          attributes: { gender: "male", spouse: "Petra" },
          children: [
            { name: "Celeste", attributes: { gender: "female", spouse: "" } },
          ],
        },
      ],
    },
    {
      name: "Vivienne",
      attributes: { gender: "female", spouse: "Edmund" },
      children: [
        { name: "Jasper",  attributes: { gender: "male",   spouse: "" } },
        { name: "Isolde",  attributes: { gender: "female", spouse: "" } },
      ],
    },
  ],
};

// ── Inference Engine ─────────────────────────────────────────────────────────
function getAllBloodPeople(node: PersonNode, acc: string[] = []): string[] {
  acc.push(node.name);
  (node.children ?? []).forEach(c => getAllBloodPeople(c as PersonNode, acc));
  return acc;
}
const allBlood = getAllBloodPeople(familyTree);
const allPeople = [...allBlood, ...Object.keys(spouseMap).filter(k => spouseSet.has(k))];

function getParent(name: string, node: PersonNode, parent: PersonNode | null = null): PersonNode | null | undefined {
  if (node.name === name) return parent;
  for (const c of node.children ?? []) {
    const r = getParent(name, c as PersonNode, node);
    if (r !== undefined) return r;
  }
  return undefined;
}

function getAncestors(name: string, root: PersonNode): string[] {
  const results: string[] = [];
  let current = getParent(name, root);
  while (current) {
    results.push(current.name);
    current = getParent(current.name, root);
  }
  return results;
}

function getDescendants(node: PersonNode, acc: string[] = []): string[] {
  (node.children ?? []).forEach(c => {
    acc.push(c.name);
    getDescendants(c as PersonNode, acc);
  });
  return acc;
}

function getSiblings(name: string, root: PersonNode): string[] {
  const parent = getParent(name, root);
  if (!parent) return [];
  return (parent.children ?? []).map(c => c.name).filter(n => n !== name);
}

function findNode(name: string, node: PersonNode): PersonNode | null {
  if (node.name === name) return node;
  for (const c of node.children ?? []) {
    const r = findNode(name, c as PersonNode);
    if (r) return r;
  }
  return null;
}

function runQuery(query: string, root: PersonNode): QueryResult {
  const q = query.trim().toLowerCase().replace(/\.$/, "");
  const lookup = (name: string): string | undefined =>
    allPeople.find(p => p.toLowerCase() === name);

  const spouseX  = q.match(/^spouse\(x,\s*(\w+)\)$/);
  const spouseXr = q.match(/^spouse\((\w+),\s*x\)$/);
  const spouseTarget = spouseX?.[1] ?? spouseXr?.[1];
  if (spouseTarget) {
    const found = lookup(spouseTarget);
    if (!found) return { type: "error", msg: `Unknown individual: ${spouseTarget}` };
    const sp = spouseMap[found];
    return sp
      ? { type: "result", bindings: [{ X: sp }] }
      : { type: "result", bindings: [], msg: "false." };
  }

  const ancMatch  = q.match(/^ancestor\(x,\s*(\w+)\)$/);
  const descMatch = q.match(/^descendant\(x,\s*(\w+)\)$/);
  const sibMatch  = q.match(/^sibling\(x,\s*(\w+)\)$/);
  const parMatch  = q.match(/^parent\(x,\s*(\w+)\)$/);

  if (ancMatch) {
    const p = lookup(ancMatch[1]);
    if (!p) return { type: "error", msg: `Unknown: ${ancMatch[1]}` };
    const ancs = getAncestors(p, root);
    return ancs.length
      ? { type: "result", bindings: ancs.map(a => ({ X: a })) }
      : { type: "result", bindings: [], msg: "false." };
  }
  if (descMatch) {
    const p = lookup(descMatch[1]);
    if (!p) return { type: "error", msg: `Unknown: ${descMatch[1]}` };
    const node = findNode(p, root);
    if (!node) return { type: "result", bindings: [], msg: "false." };
    const descs = getDescendants(node);
    return descs.length
      ? { type: "result", bindings: descs.map(d => ({ X: d })) }
      : { type: "result", bindings: [], msg: "false." };
  }
  if (sibMatch) {
    const p = lookup(sibMatch[1]);
    if (!p) return { type: "error", msg: `Unknown: ${sibMatch[1]}` };
    const sibs = getSiblings(p, root);
    return sibs.length
      ? { type: "result", bindings: sibs.map(s => ({ X: s })) }
      : { type: "result", bindings: [], msg: "false." };
  }
  if (parMatch) {
    const p = lookup(parMatch[1]);
    if (!p) return { type: "error", msg: `Unknown: ${parMatch[1]}` };
    const par = getParent(p, root);
    return par
      ? { type: "result", bindings: [{ X: par.name }] }
      : { type: "result", bindings: [], msg: "false." };
  }

  if (q === "male(x)")
    return { type: "result", bindings: allPeople.filter(p => genderMap[p] === "male").map(p => ({ X: p })) };
  if (q === "female(x)")
    return { type: "result", bindings: allPeople.filter(p => genderMap[p] === "female").map(p => ({ X: p })) };

  return { type: "error", msg: "ERROR: Try: ancestor(X,name) parent(X,name) sibling(X,name) descendant(X,name) spouse(X,name) male(X) female(X)" };
}

// ── Custom Node ──────────────────────────────────────────────────────────────
// Omit the conflicting onNodeClick from CustomNodeElementProps, then add our own
type NodeElProps = Omit<CustomNodeElementProps, "onNodeClick"> & {
  selected: string | null;
  onNodeClick: (nd: PersonNode) => void;
};

const NodeEl = ({ nodeDatum, selected, onNodeClick }: NodeElProps) => {
  const attrs = nodeDatum.attributes as { gender: string; spouse: string };
  const isMale        = attrs.gender === "male";
  const isSelected    = selected === nodeDatum.name;
  const spouseName    = attrs.spouse ?? "";
  const hasSpouse     = spouseName !== "";
  const spouseGender: "male" | "female" = spouseName ? genderMap[spouseName] ?? "female" : "female";
  const spouseIsMale  = spouseGender === "male";

  const nodeW = 96, nodeH = 40, gap = 22;
  const spouseOffsetX = nodeW / 2 + gap;

  const handleBloodClick = () =>
    onNodeClick(nodeDatum as unknown as PersonNode);

  const handleSpouseClick = () => {
    if (!spouseName) return;
    onNodeClick({
      name: spouseName,
      attributes: { gender: spouseGender, spouse: nodeDatum.name },
    } as PersonNode);
  };

  return (
    <g style={{ cursor: "pointer" }}>
      {/* Blood node */}
      <g onClick={handleBloodClick}>
        <rect
          x={-nodeW / 2} y={-nodeH / 2} width={nodeW} height={nodeH} rx={4}
          fill={isSelected ? DGREEN : isMale ? MALE_BG : FEMALE_BG}
          stroke={isSelected ? DGREEN : isMale ? MALE_STROKE : FEMALE_STROKE}
          strokeWidth={isSelected ? 2 : 1}
        />
        <text
          textAnchor="middle" dominantBaseline="middle"
          fill={isSelected ? "#000a1a" : isMale ? MALE_TEXT : FEMALE_TEXT}
          fontFamily="'Courier New', monospace" fontSize="12"
          fontWeight={isSelected ? "bold" : "normal"}
        >
          {nodeDatum.name}
        </text>
        <text
          textAnchor="middle" y={nodeH / 2 + 10}
          fill={isMale ? "#4a9abb" : "#bb6a3a"}
          fontFamily="'Courier New', monospace" fontSize="11"
        >
          {isMale ? "♂" : "♀"}
        </text>
      </g>

      {/* Spouse node */}
      {hasSpouse && (
        <g onClick={handleSpouseClick}>
          <line
            x1={nodeW / 2} y1={0} x2={spouseOffsetX} y2={0}
            stroke={SPOUSE_STROKE} strokeWidth={1.5} strokeDasharray="4,3"
          />
          <text
            x={nodeW / 2 + gap / 2} y={-8} textAnchor="middle"
            fill="#ff7788" fontFamily="'Courier New', monospace" fontSize="9"
          >
            ♥
          </text>
          <rect
            x={spouseOffsetX} y={-nodeH / 2} width={nodeW} height={nodeH} rx={4}
            fill={SPOUSE_BG} stroke={SPOUSE_STROKE} strokeWidth={1}
          />
          <text
            textAnchor="middle" x={spouseOffsetX + nodeW / 2} dominantBaseline="middle"
            fill={SPOUSE_TEXT} fontFamily="'Courier New', monospace" fontSize="12"
          >
            {spouseName}
          </text>
          <text
            textAnchor="middle" x={spouseOffsetX + nodeW / 2} y={nodeH / 2 + 10}
            fill="#4a8a3a" fontFamily="'Courier New', monospace" fontSize="11"
          >
            {spouseIsMale ? "♂" : "♀"}
          </text>
        </g>
      )}
    </g>
  );
};

// ── Log color map ─────────────────────────────────────────────────────────────
const logColors: Record<LogEntry["type"], string> = {
  system:  "#3a7a9a",
  query:   DGREEN,
  binding: GREEN,
  result:  YELLOW,
  error:   RED,
};

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [selected, setSelected] = useState<string | null>(null);
  const [input, setInput]       = useState<string>("");
  const [log, setLog]           = useState<LogEntry[]>([
    { type: "system", text: "% Family Expert System v2.0" },
    { type: "system", text: "% Knowledge base loaded: 3 generations, 11 individuals" },
    { type: "system", text: "% Click any node or type a Prolog-style query." },
    { type: "system", text: "% e.g.  spouse(X, rowan).  or  ancestor(X, celeste)." },
  ]);
  const logRef = useRef<HTMLDivElement>(null);

  const pushLog = useCallback((entries: LogEntry[]) => {
    setLog(prev => [...prev, ...entries].slice(-MAX_LOG));
    setTimeout(() => {
      if (logRef.current) {
        logRef.current.scrollTop = logRef.current.scrollHeight;
      }
    }, 30);
  }, []);

  const handleNodeClick = useCallback((nd: PersonNode) => {
    const name = nd.name;
    setSelected(name);
    const isBlood = allBlood.includes(name);
    const q = isBlood
      ? `ancestor(X, ${name.toLowerCase()})`
      : `spouse(X, ${name.toLowerCase()})`;
    const result = runQuery(q, familyTree);
    const entries: LogEntry[] = [
      { type: "query", text: `?- ${q}.` },
      ...(result.bindings?.length
        ? result.bindings.map((b, i): LogEntry => ({
            type: "binding",
            text: `${Object.entries(b).map(([k, v]) => `${k} = ${v}`).join(", ")} ${
              i < (result.bindings?.length ?? 0) - 1 ? ";" : "."
            }`,
          }))
        : [{ type: "result" as const, text: result.msg ?? "false." }]),
    ];
    pushLog(entries);
  }, [pushLog]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    const result = runQuery(input, familyTree);
    const entries: LogEntry[] = [
      { type: "query", text: `?- ${input.trim()}` },
      ...(result.type === "error"
        ? [{ type: "error" as const, text: result.msg ?? "Error." }]
        : result.bindings?.length
        ? result.bindings.map((b, i): LogEntry => ({
            type: "binding",
            text: `${Object.entries(b).map(([k, v]) => `${k} = ${v}`).join(", ")} ${
              i < (result.bindings?.length ?? 0) - 1 ? ";" : "."
            }`,
          }))
        : [{ type: "result" as const, text: result.msg ?? "false." }]),
    ];
    pushLog(entries);
    setInput("");
  };

  return (
    <div style={{ position: "fixed", inset: 0, background: BASE, fontFamily: "'Courier New',monospace", color: GREEN, display: "flex", flexDirection: "column", overflow: "hidden" }}>
      {/* Scanlines */}
      <div style={{ position: "fixed", inset: 0, background: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,30,60,0.08) 3px, rgba(0,30,60,0.08) 4px)", pointerEvents: "none", zIndex: 999 }} />

      {/* Header */}
      <div style={{ display: "flex", alignItems: "center", gap: 16, padding: "9px 20px", borderBottom: `1px solid ${DIM}`, background: "#061e30", flexShrink: 0 }}>
        <span style={{ background: GREEN, color: "#041824", padding: "3px 9px", fontSize: 11, fontWeight: "bold", letterSpacing: 2 }}>KBS</span>
        <span style={{ fontSize: 12, letterSpacing: 3, color: GREEN, flex: 1 }}>FAMILY KNOWLEDGE BASE · EXPERT SYSTEM v2.0</span>
        <span style={{ fontSize: 11, color: YELLOW, letterSpacing: 2 }}>
          {selected ? `CONTEXT: ${selected.toUpperCase()}` : "NO SELECTION"}
        </span>
      </div>

      {/* Body */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", minHeight: 0 }}>

        {/* Tree panel */}
        <div style={{ flex: "0 0 60%", position: "relative", borderRight: `1px solid ${DIM}`, overflow: "hidden", display: "flex", flexDirection: "column" }}>
          <div style={{ padding: "5px 14px", fontSize: 10, letterSpacing: 3, color: "#3a7a9a", borderBottom: `1px solid ${DIM}`, background: "#061e30" }}>
            FACT DATABASE · KINSHIP GRAPH · 3 GENERATIONS
          </div>
          <svg width="0" height="0" style={{ position: "absolute" }}>
            <defs>
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="blur" />
                <feMerge>
                  <feMergeNode in="blur" />
                  <feMergeNode in="SourceGraphic" />
                </feMerge>
              </filter>
            </defs>
          </svg>
          <Tree
            data={familyTree}
            orientation="vertical"
            pathFunc="step"
            translate={{ x: 200, y: 70 }}
            separation={{ siblings: 2.2, nonSiblings: 2.6 }}
            nodeSize={{ x: 240, y: 130 }}
            onNodeClick={(nd: { data: RawNodeDatum }) =>
              handleNodeClick(nd.data as unknown as PersonNode)
            }
            renderCustomNodeElement={(props: CustomNodeElementProps) => (
              <NodeEl
                {...props}
                selected={selected}
                onNodeClick={handleNodeClick}
              />
            )}
            styles={{ links: { stroke: DIM, strokeWidth: 1.5 } }}
          />
        </div>

        {/* Terminal panel */}
        <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden", background: "#051520" }}>
          <div style={{ padding: "5px 14px", fontSize: 10, letterSpacing: 3, color: "#3a7a9a", borderBottom: `1px solid ${DIM}`, background: "#061e30" }}>
            INFERENCE ENGINE · PROLOG TERMINAL
          </div>

          {/* Hint buttons */}
          <div style={{ display: "flex", flexWrap: "wrap", gap: 5, padding: "7px 14px", borderBottom: `1px solid ${DIM}`, background: "#061e30" }}>
            {[
              "ancestor(X, celeste)",
              "parent(X, theo)",
              "sibling(X, jasper)",
              "descendant(X, rowan)",
              "spouse(X, rowan)",
              "spouse(X, margaret)",
              "male(X)",
              "female(X)",
            ].map(hint => (
              <button
                key={hint}
                style={{ background: "transparent", border: `1px solid ${DIM}`, color: "#4a9ab8", fontFamily: "'Courier New',monospace", fontSize: 10, padding: "3px 7px", cursor: "pointer", letterSpacing: 0.5 }}
                onClick={() => setInput(hint)}
              >
                {hint}
              </button>
            ))}
          </div>

          {/* Legend */}
          <div style={{ display: "flex", gap: 14, padding: "5px 14px", borderBottom: `1px solid ${DIM}`, background: "#051e30", fontSize: 10, color: "#4a7a9a" }}>
            <span><span style={{ color: MALE_TEXT }}>■</span> Male (blood)</span>
            <span><span style={{ color: FEMALE_TEXT }}>■</span> Female (blood)</span>
            <span><span style={{ color: SPOUSE_TEXT }}>■</span> Spouse</span>
            <span style={{ color: "#ff7788" }}>♥ married</span>
            <span style={{ color: "#66cc44" }}>╌ union</span>
          </div>

          {/* Log */}
          <div
            ref={logRef}
            style={{ flex: 1, overflowY: "auto", padding: "14px 18px", fontSize: 13, lineHeight: 1.8 }}
          >
            {log.map((entry, i) => (
              <div
                key={i}
                style={{
                  display: "block",
                  whiteSpace: "pre-wrap",
                  wordBreak: "break-all",
                  color: logColors[entry.type],
                  fontWeight: entry.type === "query" ? "bold" : "normal",
                  paddingLeft: (["binding", "result"] as LogEntry["type"][]).includes(entry.type) ? 16 : 0,
                }}
              >
                {entry.text}
              </div>
            ))}
            <div style={{ color: DGREEN, fontSize: 14 }}>█</div>
          </div>

          {/* Input */}
          <form
            onSubmit={handleSubmit}
            style={{ display: "flex", alignItems: "center", gap: 10, padding: "10px 16px", borderTop: `1px solid ${DIM}`, background: "#061e30" }}
          >
            <span style={{ color: DGREEN, fontWeight: "bold", fontSize: 15, flexShrink: 0 }}>?-</span>
            <input
              style={{ flex: 1, background: "transparent", border: "none", outline: "none", color: GREEN, fontFamily: "'Courier New',monospace", fontSize: 14, caretColor: DGREEN }}
              value={input}
              onChange={(e: React.ChangeEvent<HTMLInputElement>) => setInput(e.target.value)}
              placeholder="spouse(X, alistair)."
              spellCheck={false}
              autoComplete="off"
            />
            <button
              type="submit"
              style={{ background: "transparent", border: `1px solid ${GREEN}`, color: GREEN, fontFamily: "'Courier New',monospace", fontSize: 11, padding: "5px 12px", cursor: "pointer", letterSpacing: 1 }}
            >
              ▶ RUN
            </button>
          </form>
        </div>
      </div>

      <style>{`@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }`}</style>
    </div>
  );
}