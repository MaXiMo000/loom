import type { Scan } from '../api'

export function Legend({ scan }: { scan: Scan }) {
  return (
    <div className="legend">
      <h4>Legend</h4>
      <div className="legend-row"><span className="legend-swatch" style={{ background: '#E8873B' }} /> vulnerable (worse = brighter)</div>
      <div className="legend-row"><span className="legend-swatch" style={{ background: '#86E9DE' }} /> providence-verified, clean</div>
      <div className="legend-row"><span className="legend-swatch" style={{ background: '#98A3B1' }} /> unverified / no finding</div>
      <div className="legend-row">size ∝ how many packages depend on it</div>
      <div className="legend-note">
        Showing {scan.nodes.length} of {scan.total_package_count} dependencies,
        depth-capped at {scan.depth_cap} levels (SPEC.md §7.2). Drift and policy
        signals are always <code>unverified</code> in this phase — not computed yet.
      </div>
    </div>
  )
}
