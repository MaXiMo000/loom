import { useEffect, useRef } from 'react'
import type { ScanNode } from '../api'

/** Click-a-node → detail panel. Focus/inert/Escape handling ported directly
 * from portfolio/web/src/DeepDive.tsx's own pattern (SPEC.md §8.3) — native
 * `inert` instead of a hand-rolled focus trap, focus returned on close. */
export function DetailPanel({ node, onClose }: { node: ScanNode | null; onClose: () => void }) {
  const closeRef = useRef<HTMLButtonElement>(null)
  const returnFocusTo = useRef<Element | null>(null)

  useEffect(() => {
    if (!node) return
    returnFocusTo.current = document.activeElement
    closeRef.current?.focus()

    const root = document.querySelector('.scene-root')
    root?.setAttribute('inert', '')

    const onKey = (e: KeyboardEvent) => { if (e.key === 'Escape') onClose() }
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('keydown', onKey)
      root?.removeAttribute('inert')
      ;(returnFocusTo.current as HTMLElement | null)?.focus?.()
    }
  }, [node, onClose])

  if (!node) return null

  const vulnBad = node.vuln_severity !== 'none' && node.vuln_severity !== 'unverified'
  const provGood = node.providence_status === 'verified'

  return (
    <div className="dive-backdrop" onClick={(e) => { if (e.target === e.currentTarget) onClose() }}>
      <div className="dive" role="dialog" aria-modal="true" aria-labelledby="detail-title">
        <button type="button" className="dive__close" onClick={onClose} ref={closeRef} aria-label="Close detail panel">
          Close ✕
        </button>
        <p className="eyebrow">Package · the receipt, not a claim</p>
        <h3 id="detail-title" className="dive__title">{node.package_name}</h3>
        <p className="dive__version">v{node.package_version} · depth {node.depth}</p>

        <div className="dive__signals">
          <Signal label="Vulnerability" value={node.vuln_severity} tone={vulnBad ? 'bad' : node.vuln_severity === 'unverified' ? 'neutral' : 'good'} />
          <Signal label="Drift (lockstep)" value={node.drift_status} tone={node.drift_status === 'unverified' ? 'neutral' : node.drift_status === 'matched' ? 'good' : 'bad'} />
          <Signal label="Tamper-evidence (providence)" value={node.providence_status} tone={provGood ? 'good' : 'neutral'} />
          <Signal label="Policy (invariant)" value={node.policy_status} tone={node.policy_status === 'unverified' ? 'neutral' : node.policy_status === 'pass' ? 'good' : 'bad'} />
        </div>

        {node.vuln_detail && <p className="dive__detail">{node.vuln_detail}</p>}
        {node.drift_detail && <p className="dive__detail">{node.drift_detail}</p>}

        <div className="dive__meta">
          {node.repo_stars != null && <div>★ {node.repo_stars.toLocaleString()} stars</div>}
          {node.repo_last_commit && <div>last commit {new Date(node.repo_last_commit).toLocaleDateString()}</div>}
        </div>
      </div>
    </div>
  )
}

function Signal({ label, value, tone }: { label: string; value: string; tone: 'bad' | 'good' | 'neutral' }) {
  return (
    <div className={`signal ${tone}`}>
      <span className="signal-label">{label}</span>
      <span className={`signal-value ${tone}`}>{value}</span>
    </div>
  )
}
