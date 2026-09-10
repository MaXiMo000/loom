// @ts-expect-error — d3-force-3d ships no published types; its API is the
// same shape as d3-force plus a numDimensions option (see its README).
import { forceCenter, forceLink, forceManyBody, forceSimulation, forceX, forceY, forceZ } from 'd3-force-3d'
import type { ScanEdge, ScanNode } from '../api'

export interface LaidOutNode extends ScanNode {
  x: number
  y: number
  z: number
}

const SETTLE_TICKS = 300

/**
 * Runs the force simulation synchronously to a settled layout and returns
 * static positions — no per-frame physics re-render. SPEC.md §13 leaves
 * exact charge/distance tuning open until real data is in front of it;
 * this is that first real data. Revisit once Phase 1 graphs are bigger and
 * less uniform than the fixture's ~12 nodes.
 */
export function computeLayout(nodes: ScanNode[], edges: ScanEdge[]): Map<string, LaidOutNode> {
  const simNodes = nodes.map((n) => ({ ...n }))
  const simLinks = edges.map((e) => ({ source: e.from_node, target: e.to_node }))

  const sim = forceSimulation(simNodes, 3)
    .force('link', forceLink(simLinks).id((d: { id: string }) => d.id).distance(2.6))
    .force('charge', forceManyBody().strength(-6))
    .force('center', forceCenter())
    // Fixture repos resolve to multiple disconnected components (a "requests"
    // family and a "flask" family, no edge between them) — forceLink can't
    // pull those together and forceCenter only recenters their average, so
    // mutual charge repulsion pushes the components apart without bound. A
    // weak pull toward the origin on every axis keeps everything in frame
    // without fighting the local link/charge structure within each cluster.
    .force('x', forceX(0).strength(0.05))
    .force('y', forceY(0).strength(0.05))
    .force('z', forceZ(0).strength(0.05))
    .stop()

  for (let i = 0; i < SETTLE_TICKS; i++) sim.tick()

  const out = new Map<string, LaidOutNode>()
  for (const n of simNodes as (ScanNode & { x: number; y: number; z: number })[]) {
    out.set(n.id, { ...n, x: n.x, y: n.y, z: n.z })
  }
  return out
}
