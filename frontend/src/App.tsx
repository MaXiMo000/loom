import { useEffect, useRef, useState } from 'react'
import { createScan, getScan, type Scan } from './api'
import { DetailPanel } from './components/DetailPanel'
import { Legend } from './components/Legend'
import { ScanForm } from './components/ScanForm'
import { MODE } from './lib/mode'
import { Graph } from './scene/Graph'

// Simple GET polling, not WebSockets (SPEC.md §7.4) — a scan takes seconds
// to a couple of minutes; 2s matches the spec's own stated interval.
const POLL_INTERVAL_MS = 2000

const STAGE_LABEL: Record<string, string> = {
  pending: 'Queued…',
  cloning: 'Cloning the repository…',
  resolving: 'Resolving the dependency graph…',
  scanning: 'Checking vulnerability, drift, tamper-evidence and policy signals…',
}

export function App() {
  const [scan, setScan] = useState<Scan | null>(null)
  const [scanId, setScanId] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const pollRef = useRef<ReturnType<typeof setInterval> | null>(null)

  useEffect(() => () => { if (pollRef.current) clearInterval(pollRef.current) }, [])

  function startScan(repoUrl: string) {
    setSubmitError(null)
    setScan(null)
    setSelectedId(null)
    createScan(repoUrl)
      .then(({ id }) => {
        setScanId(id)
        if (pollRef.current) clearInterval(pollRef.current)
        const poll = () => getScan(id).then((s) => {
          setScan(s)
          if (s.status === 'complete' || s.status === 'failed') {
            if (pollRef.current) clearInterval(pollRef.current)
          }
        }).catch((e) => setSubmitError(String(e)))
        poll()
        pollRef.current = setInterval(poll, POLL_INTERVAL_MS)
      })
      .catch((e) => setSubmitError(String(e)))
  }

  const busy = scanId !== null && scan?.status !== 'complete' && scan?.status !== 'failed'
  const selected = scan?.nodes.find((n) => n.id === selectedId) ?? null

  return (
    <div className="app">
      {/* DetailPanel below is a SIBLING of this wrapper, not a descendant —
          it sets `inert` on `.scene-root` while open (portfolio's own
          DeepDive/`<main>` split, App.tsx:112+358); if the panel were nested
          inside the element it inerts, its own Close button would inert
          itself. */}
      <div className="scene-root">
        <div className="hud-top">
          <div className="brand"><em>loom</em> — weaves four tools' answers into one graph</div>
          <ScanForm onSubmit={startScan} busy={busy} />
        </div>

        {!scan && !submitError && (
          <div className="scan-status">
            <p className="stage">Paste a public GitHub repo URL above to scan its real dependency graph.</p>
            <p className="hint">Requires a fully-pinned requirements.txt (pip-compile) or poetry.lock — SPEC.md §3.</p>
          </div>
        )}

        {submitError && (
          <div className="scan-status">
            <p className="error">{submitError}</p>
          </div>
        )}

        {scan && scan.status !== 'complete' && scan.status !== 'failed' && (
          <div className="scan-status">
            <p className="stage">{STAGE_LABEL[scan.status] ?? scan.status}</p>
          </div>
        )}

        {scan && scan.status === 'failed' && (
          <div className="scan-status">
            <p className="error">{scan.error ?? 'Scan failed.'}</p>
          </div>
        )}

        {scan && scan.status === 'complete' && (
          MODE === 'off' ? (
            <ul style={{ padding: '80px 28px', fontFamily: 'var(--mono)', fontSize: 13, listStyle: 'none' }}>
              {scan.nodes.map((n) => (
                <li key={n.id} style={{ marginBottom: 8, cursor: 'pointer' }} onClick={() => setSelectedId(n.id)}>
                  {n.package_name}@{n.package_version} — vuln: {n.vuln_severity}
                </li>
              ))}
            </ul>
          ) : (
            <Graph nodes={scan.nodes} edges={scan.edges} onSelect={setSelectedId} />
          )
        )}

        {scan && scan.status === 'complete' && <Legend scan={scan} />}
      </div>
      <DetailPanel node={selected} onClose={() => setSelectedId(null)} />
    </div>
  )
}
