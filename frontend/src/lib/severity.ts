/**
 * Pure logic for the graph's two real visual signals (SPEC.md §8.3):
 *   - color = the worst of a node's signal severities
 *   - size  = how many other nodes depend on it (in-degree)
 *
 * Kept separate from scene/Node.tsx so it's testable without a WebGL
 * context, and reusable once Phase 1 replaces fixture nodes with real ones
 * — the shape (`vuln_severity`, `providence_status`, ...) is already the
 * real API contract (SPEC.md §7.6), only the data source changes later.
 */

export type VulnSeverity = 'none' | 'low' | 'medium' | 'high' | 'critical' | 'unverified'
export type ProvidenceStatus = 'verified' | 'unverified'

export interface GraphNode {
  id: string
  vuln_severity: VulnSeverity
  providence_status: ProvidenceStatus
}

export interface GraphEdge {
  from_node: string
  to_node: string
}

export const COLOR = {
  beam: '#86E9DE',
  escalate: '#E8873B',
  alloy: '#98A3B1',
} as const

/**
 * Vulnerability dominates (a concrete finding beats an absence-of-finding
 * "verified" glow); a clean, providence-verified node gets the one positive
 * color in the system; everything else — drift and policy both always
 * `unverified` until Phase 2/1 land their real checks (SPEC.md §10) — reads
 * as neutral rather than guessed.
 */
export function nodeColor(node: GraphNode): { color: string; emissiveIntensity: number } {
  switch (node.vuln_severity) {
    case 'critical':
      return { color: COLOR.escalate, emissiveIntensity: 1.4 }
    case 'high':
      return { color: COLOR.escalate, emissiveIntensity: 1.1 }
    case 'medium':
      return { color: COLOR.escalate, emissiveIntensity: 0.7 }
    case 'low':
      return { color: COLOR.escalate, emissiveIntensity: 0.4 }
    default:
      if (node.providence_status === 'verified') {
        return { color: COLOR.beam, emissiveIntensity: 1.0 }
      }
      return { color: COLOR.alloy, emissiveIntensity: 0.12 }
  }
}

/** How many other nodes declare this one as a dependency. */
export function computeInDegree(edges: GraphEdge[]): Map<string, number> {
  const counts = new Map<string, number>()
  for (const e of edges) {
    counts.set(e.to_node, (counts.get(e.to_node) ?? 0) + 1)
  }
  return counts
}

const MIN_RADIUS = 0.35
const MAX_RADIUS = 1.4
const RADIUS_STEP = 0.22

export function nodeRadius(inDegree: number): number {
  return Math.min(MAX_RADIUS, MIN_RADIUS + inDegree * RADIUS_STEP)
}
