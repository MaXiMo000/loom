import type { ScanSummary } from '../api'

/** Scan history for the currently-viewed repo (SPEC.md §8.4) — visual
 * language ported from portfolio/web's own `.rail` (vertical, thin,
 * numbered), repurposed from "which section" to "which scan". `<button>`s
 * here, not `<a>`s — these change state, they don't navigate. */
export function HistoryRail({ scans, currentId, onSelect, onCompare }: {
  scans: ScanSummary[]
  currentId: string | null
  onSelect: (id: string) => void
  onCompare: (id: string, previousId: string) => void
}) {
  if (scans.length === 0) return null

  return (
    <div className="rail">
      {scans.map((s, i) => {
        const previous = scans[i + 1] // list is newest-first
        return (
          <div key={s.id} className={`rail-row ${s.id === currentId ? 'on' : ''}`}>
            <button type="button" className="rail-item" onClick={() => onSelect(s.id)}>
              <u>{scans.length - i}</u>
              {new Date(s.created_at).toLocaleString(undefined, { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}
              {s.status !== 'complete' && <span className="rail-status">{s.status}</span>}
            </button>
            {previous && s.status === 'complete' && previous.status === 'complete' && (
              <button type="button" className="rail-compare" onClick={() => onCompare(s.id, previous.id)} title="Compare to previous scan">
                Δ
              </button>
            )}
          </div>
        )
      })}
    </div>
  )
}
