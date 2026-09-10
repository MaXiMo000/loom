import type { Diff, DiffChange } from '../api'
import { useModalPanel } from '../lib/useModalPanel'

const TONE: Record<DiffChange['change_type'], 'bad' | 'good' | 'neutral'> = {
  added: 'neutral',
  removed: 'neutral',
  changed: 'bad',
}

const LABEL: Record<DiffChange['change_type'], string> = {
  added: '+ added',
  removed: '− removed',
  changed: '± changed',
}

/** "Compare to previous scan" (SPEC.md §8.4) — the drift-over-time payoff
 * SPEC.md §3's persistence decision exists for. */
export function DiffPanel({ diff, onClose }: { diff: Diff | null; onClose: () => void }) {
  const closeRef = useModalPanel(diff !== null, onClose)

  if (!diff) return null

  const from = new Date(diff.from_scan.created_at).toLocaleString()
  const to = new Date(diff.to_scan.created_at).toLocaleString()

  return (
    <div className="dive-backdrop" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="dive" role="dialog" aria-modal="true" aria-labelledby="diff-title">
        <button type="button" className="dive__close" onClick={onClose} ref={closeRef} aria-label="Close diff panel">
          Close ✕
        </button>
        <p className="eyebrow">Drift over time</p>
        <h3 id="diff-title" className="dive__title">What changed</h3>
        <p className="dive__version">{from} → {to}</p>

        {diff.changes.length === 0 ? (
          <p className="dive__detail">No changes — every package matched between these two scans.</p>
        ) : (
          <div className="dive__signals">
            {diff.changes.map((c) => (
              <div key={c.package_name} className={`signal ${TONE[c.change_type]}`}>
                <div>
                  <span className="signal-label">{c.package_name}</span>
                  <p className="dive__detail" style={{ marginTop: 4 }}>{c.detail}</p>
                </div>
                <span className={`signal-value ${TONE[c.change_type]}`}>{LABEL[c.change_type]}</span>
              </div>
            ))}
          </div>
        )}

        <div className="dive__meta">
          {diff.unchanged_count} package{diff.unchanged_count === 1 ? '' : 's'} unchanged
        </div>
      </div>
    </div>
  )
}
