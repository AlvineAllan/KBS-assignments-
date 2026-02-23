import React, { useState, useCallback, useRef } from "react";
import type { CSSProperties } from "react";
import TreeComponent from "react-d3-tree";
import type { RawNodeDatum, CustomNodeElementProps, TreeProps } from "react-d3-tree";

// eslint-disable-next-line @typescript-eslint/no-explicit-any
const Tree = TreeComponent as any;

// ── Types ────────────────────────────────────────────────────────────────────
interface Person {
  name: string;
  attributes: { gender: "male" | "female" };
  children?: Person[];
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

// ── Knowledge Base ───────────────────────────────────────────────────────────
const familyKB: Person = {
  name: "Alistair",
  attributes: { gender: "male" },
  children: [
    {
      name: "Rowan",
      attributes: { gender: "male" },
      children: [{
        name: "Theo",
        attributes: { gender: "male" },
        children: [{ name: "Celeste", attributes: { gender: "female" } }],
      }],
    },
    {
      name: "Vivienne",
      attributes: { gender: "female" },
      children: [
        { name: "Jasper", attributes: { gender: "male" } },
        { name: "Isolde", attributes: { gender: "female" } },
      ],
    },
  ],
};

// ── Inference Engine ─────────────────────────────────────────────────────────
function getAllPeople(node: Person, acc: Person[] = []): Person[] {
  acc.push(node);
  (node.children ?? []).forEach((c) => getAllPeople(c, acc));
  return acc;
}

function getParent(name: string, node: Person, parent: Person | null = null): Person | null | undefined {
  if (node.name === name) return parent;
  for (const c of node.children ?? []) {
    const r = getParent(name, c, node);
    if (r !== undefined) return r;
  }
  return undefined;
}

function getAncestors(name: string, root: Person): string[] {
  const results: string[] = [];
  let current = getParent(name, root);
  while (current) {
    results.push(current.name);
    current = getParent(current.name, root);
  }
  return results;
}

function getDescendants(node: Person, acc: string[] = []): string[] {
  (node.children ?? []).forEach((c) => { acc.push(c.name); getDescendants(c, acc); });
  return acc;
}

function getSiblings(name: string, root: Person): string[] {
  const parent = getParent(name, root);
  if (!parent) return [];
  return (parent.children ?? []).map((c) => c.name).filter((n) => n !== name);
}

function runQuery(query: string, root: Person): QueryResult {
  const all = getAllPeople(root);
  const q = query.trim().toLowerCase().replace(/\.$/, "");

  const ancMatch = q.match(/^ancestor\(x,\s*(\w+)\)$/);
  if (ancMatch) {
    const person = all.find((p) => p.name.toLowerCase() === ancMatch[1]);
    if (!person) return { type: "error", msg: `Unknown individual: ${ancMatch[1]}` };
    const ancs = getAncestors(person.name, root);
    return ancs.length
      ? { type: "result", bindings: ancs.map((a) => ({ X: a })) }
      : { type: "result", bindings: [], msg: "false." };
  }

  const descMatch = q.match(/^descendant\(x,\s*(\w+)\)$/);
  if (descMatch) {
    const person = all.find((p) => p.name.toLowerCase() === descMatch[1]);
    if (!person) return { type: "error", msg: `Unknown individual: ${descMatch[1]}` };
    const descs = getDescendants(person);
    return descs.length
      ? { type: "result", bindings: descs.map((d) => ({ X: d })) }
      : { type: "result", bindings: [], msg: "false." };
  }

  const sibMatch = q.match(/^sibling\(x,\s*(\w+)\)$/);
  if (sibMatch) {
    const person = all.find((p) => p.name.toLowerCase() === sibMatch[1]);
    if (!person) return { type: "error", msg: `Unknown individual: ${sibMatch[1]}` };
    const sibs = getSiblings(person.name, root);
    return sibs.length
      ? { type: "result", bindings: sibs.map((s) => ({ X: s })) }
      : { type: "result", bindings: [], msg: "false." };
  }

  const parMatch = q.match(/^parent\(x,\s*(\w+)\)$/);
  if (parMatch) {
    const person = all.find((p) => p.name.toLowerCase() === parMatch[1]);
    if (!person) return { type: "error", msg: `Unknown individual: ${parMatch[1]}` };
    const par = getParent(person.name, root);
    return par
      ? { type: "result", bindings: [{ X: par.name }] }
      : { type: "result", bindings: [], msg: "false." };
  }

  const genMatch = q.match(/^gender\((\w+),\s*g\)$/);
  if (genMatch) {
    const person = all.find((p) => p.name.toLowerCase() === genMatch[1]);
    if (!person) return { type: "error", msg: `Unknown individual: ${genMatch[1]}` };
    return { type: "result", bindings: [{ G: person.attributes.gender }] };
  }

  if (q === "male(x)")
    return { type: "result", bindings: all.filter((p) => p.attributes.gender === "male").map((p) => ({ X: p.name })) };
  if (q === "female(x)")
    return { type: "result", bindings: all.filter((p) => p.attributes.gender === "female").map((p) => ({ X: p.name })) };

  return { type: "error", msg: "ERROR: Unknown predicate. Try: ancestor(X,name) parent(X,name) sibling(X,name) descendant(X,name) male(X) female(X)" };
}

// ── Custom Node ──────────────────────────────────────────────────────────────
interface NodeElProps extends CustomNodeElementProps {
  selected: string | null;
  onNodeClick: (nd: RawNodeDatum) => void;
}

const NodeEl = ({ nodeDatum, selected, onNodeClick }: NodeElProps) => {
  const isMale = (nodeDatum.attributes as Record<string, string>)?.gender === "male";
  const isSelected = selected === nodeDatum.name;
  return (
    <g onClick={() => onNodeClick(nodeDatum)} style={{ cursor: "pointer" }}>
      <rect
        x="-48" y="-20" width="96" height="40" rx="4"
        fill={isSelected ? DGREEN : isMale ? MALE_BG : FEMALE_BG}
        stroke={isSelected ? DGREEN : isMale ? MALE_STROKE : FEMALE_STROKE}
        strokeWidth={isSelected ? 2 : 1}
        filter={isSelected ? "url(#glow)" : undefined}
      />
      <text
        textAnchor="middle" dominantBaseline="middle"
        fill={isSelected ? "#000a1a" : isMale ? MALE_TEXT : FEMALE_TEXT}
        fontFamily="'Courier New', monospace"
        fontSize="13"
        fontWeight={isSelected ? "bold" : "normal"}
      >
        {nodeDatum.name}
      </text>
      <text
        textAnchor="middle" y="28"
        fill={isMale ? "#2a6a8a" : "#7a3a10"}
        fontFamily="'Courier New', monospace"
        fontSize="11"
      >
        {isMale ? "♂" : "♀"}
      </text>
    </g>
  );
};

// ── Constants ────────────────────────────────────────────────────────────────
const MAX_LOG = 20;
const BASE         = "#041824";
const GREEN        = "#33ddff";
const DGREEN       = "#88ffff";
const DIM          = "#1a4a60";
const YELLOW       = "#ffcc44";
const RED          = "#ff6666";
const MALE_BG      = "#062a48";
const MALE_STROKE  = "#1199ee";
const MALE_TEXT    = "#55ccff";
const FEMALE_BG     = "#3a1400";
const FEMALE_STROKE = "#ff7722";
const FEMALE_TEXT   = "#ffaa55";

// ── App ──────────────────────────────────────────────────────────────────────
export default function App() {
  const [selected, setSelected] = useState<string | null>(null);
  const [input, setInput]       = useState<string>("");
  const [log, setLog]           = useState<LogEntry[]>([
    { type: "system", text: "% Family Expert System v1.0" },
    { type: "system", text: "% Knowledge base loaded: 7 facts" },
    { type: "system", text: "% Click a node or type a query below." },
    { type: "system", text: "% e.g.  ancestor(X, celeste)." },
  ]);
  const logRef = useRef<HTMLDivElement>(null);

  const pushLog = useCallback((entries: LogEntry[]) => {
    setLog((prev) => [...prev, ...entries].slice(-MAX_LOG));
    setTimeout(() => {
      if (logRef.current) logRef.current.scrollTop = logRef.current.scrollHeight;
    }, 30);
  }, []);

  const handleNodeClick = useCallback((nd: RawNodeDatum) => {
    setSelected(nd.name);
    const q = `ancestor(X, ${nd.name.toLowerCase()})`;
    const result = runQuery(q, familyKB);
    const entries: LogEntry[] = [
      { type: "query", text: `?- ${q}.` },
      ...(result.bindings?.length
        ? result.bindings.map((b, i) => ({
            type: "binding" as const,
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
    const result = runQuery(input, familyKB);
    const entries: LogEntry[] = [
      { type: "query", text: `?- ${input.trim()}` },
      ...(result.type === "error"
        ? [{ type: "error" as const, text: result.msg ?? "Error." }]
        : result.bindings?.length
        ? result.bindings.map((b, i) => ({
            type: "binding" as const,
            text: `${Object.entries(b).map(([k, v]) => `${k} = ${v}`).join(", ")} ${
              i < (result.bindings?.length ?? 0) - 1 ? ";" : "."
            }`,
          }))
        : [{ type: "result" as const, text: result.msg ?? "false." }]),
    ];
    pushLog(entries);
    setInput("");
  };

  const logStyleMap: Record<LogEntry["type"], CSSProperties> = {
    system:  { color: "#3a7a9a", fontSize: 13 },
    query:   { color: DGREEN,    fontSize: 13, fontWeight: "bold" },
    binding: { color: GREEN,     paddingLeft: 16, fontSize: 13 },
    result:  { color: YELLOW,    paddingLeft: 16, fontSize: 13 },
    error:   { color: RED,       fontSize: 13 },
  };

  const treeProps: TreeProps = {
    data: familyKB as unknown as RawNodeDatum,
    orientation: "vertical",
    pathFunc: "step",
    translate: { x: 260, y: 60 },
    separation: { siblings: 1.4, nonSiblings: 1.8 },
    nodeSize: { x: 140, y: 100 },
    onNodeClick: (nd: { data: RawNodeDatum }) => handleNodeClick(nd.data),
    renderCustomNodeElement: (props: CustomNodeElementProps) => (
      <NodeEl
        {...props}
        selected={selected}
        onNodeClick={(nd: RawNodeDatum) => handleNodeClick(nd)}
      />
    ),
  };

  return (
    <div style={styles.root}>
      <div style={styles.scanlines} />

      <div style={styles.header}>
        <span style={styles.headerBadge}>KBS</span>
        <span style={styles.headerTitle}>FAMILY KNOWLEDGE BASE · EXPERT SYSTEM</span>
        <span style={styles.headerSub}>
          {selected ? `CONTEXT: ${selected.toUpperCase()}` : "NO SELECTION"}
        </span>
      </div>

      <div style={styles.body}>
        <div style={styles.treePanel}>
          <div style={styles.panelLabel}>FACT DATABASE · KINSHIP GRAPH</div>
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
            {...treeProps}
            styles={{ links: { stroke: "#1a4a60", strokeWidth: 1.5 } }}
          />
        </div>

        <div style={styles.termPanel}>
          <div style={styles.panelLabel}>INFERENCE ENGINE · PROLOG TERMINAL</div>

          <div style={styles.helpBar}>
            {[
              "ancestor(X, name)",
              "parent(X, name)",
              "sibling(X, name)",
              "descendant(X, name)",
              "male(X)",
              "female(X)",
            ].map((hint) => (
              <button key={hint} style={styles.hintBtn} onClick={() => setInput(hint)}>
                {hint}
              </button>
            ))}
          </div>

          <div style={styles.logArea} ref={logRef}>
            {log.map((entry, i) => (
              <div key={i} style={{ ...styles.logLine, ...logStyleMap[entry.type] }}>
                {entry.text}
              </div>
            ))}
            <div style={styles.cursor}>█</div>
          </div>

          <form onSubmit={handleSubmit} style={styles.inputRow}>
            <span style={styles.prompt}>?-</span>
            <input
              style={styles.input}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="ancestor(X, celeste)."
              spellCheck={false}
              autoComplete="off"
            />
            <button type="submit" style={styles.submitBtn}>▶ RUN</button>
          </form>
        </div>
      </div>
    </div>
  );
}

// ── Styles ────────────────────────────────────────────────────────────────────
const styles: Record<string, CSSProperties> = {
  root: {
    position: "fixed",
    inset: 0,
    background: BASE,
    fontFamily: "'Courier New', Courier, monospace",
    color: GREEN,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
  },
  scanlines: {
    position: "fixed",
    inset: 0,
    background: "repeating-linear-gradient(0deg, transparent, transparent 3px, rgba(0,30,60,0.08) 3px, rgba(0,30,60,0.08) 4px)",
    pointerEvents: "none",
    zIndex: 999,
  },
  header: {
    display: "flex",
    alignItems: "center",
    gap: 16,
    padding: "9px 20px",
    borderBottom: "1px solid " + DIM,
    background: "#061e30",
    flexShrink: 0,
  },
  headerBadge: {
    background: GREEN,
    color: "#041824",
    padding: "3px 9px",
    fontSize: 11,
    fontWeight: "bold",
    letterSpacing: 2,
  },
  headerTitle: {
    fontSize: 12,
    letterSpacing: 3,
    color: GREEN,
    flex: 1,
  },
  headerSub: {
    fontSize: 11,
    color: YELLOW,
    letterSpacing: 2,
  },
  body: {
    display: "flex",
    flex: 1,
    overflow: "hidden",
    minHeight: 0,
  },
  treePanel: {
    flex: "0 0 56%",
    position: "relative",
    borderRight: "1px solid " + DIM,
    overflow: "hidden",
    display: "flex",
    flexDirection: "column",
  },
  termPanel: {
    flex: 1,
    display: "flex",
    flexDirection: "column",
    overflow: "hidden",
    background: "#051520",
  },
  panelLabel: {
    padding: "5px 14px",
    fontSize: 10,
    letterSpacing: 3,
    color: "#3a7a9a",
    borderBottom: "1px solid " + DIM,
    background: "#061e30",
    textTransform: "uppercase",
  },
  helpBar: {
    display: "flex",
    flexWrap: "wrap",
    gap: 5,
    padding: "7px 14px",
    borderBottom: "1px solid " + DIM,
    background: "#061e30",
  },
  hintBtn: {
    background: "transparent",
    border: "1px solid " + DIM,
    color: "#4a9ab8",
    fontFamily: "'Courier New', monospace",
    fontSize: 11,
    padding: "3px 8px",
    cursor: "pointer",
    letterSpacing: 0.5,
    transition: "all 0.15s",
  },
  logArea: {
    flex: 1,
    overflowY: "auto",
    padding: "14px 18px",
    fontSize: 14,
    lineHeight: 1.8,
  },
  logLine: {
    display: "block",
    whiteSpace: "pre-wrap",
    wordBreak: "break-all",
  },
  cursor: {
    color: DGREEN,
    animation: "blink 1s step-end infinite",
    fontSize: 14,
  },
  inputRow: {
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: "10px 16px",
    borderTop: "1px solid " + DIM,
    background: "#061e30",
  },
  prompt: {
    color: DGREEN,
    fontWeight: "bold",
    fontSize: 15,
    flexShrink: 0,
  },
  input: {
    flex: 1,
    background: "transparent",
    border: "none",
    outline: "none",
    color: GREEN,
    fontFamily: "'Courier New', monospace",
    fontSize: 14,
    caretColor: DGREEN,
  },
  submitBtn: {
    background: "transparent",
    border: "1px solid " + GREEN,
    color: GREEN,
    fontFamily: "'Courier New', monospace",
    fontSize: 11,
    padding: "5px 12px",
    cursor: "pointer",
    letterSpacing: 1,
    flexShrink: 0,
  },
};