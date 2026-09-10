import { useEffect, useState } from 'react'
import { getScan, type Scan } from './api'
import { DetailPanel } from './components/DetailPanel'
import { Legend } from './components/Legend'
import { ScanForm } from './components/ScanForm'
import { MODE } from './lib/mode'
import { Graph } from './scene/Graph'

const FIXTURE_SCAN_ID = 'phase0-fixture-scan'

export function App() {
  const [scan, setScan] = useState<Scan | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    getScan(FIXTURE_SCAN_ID).then(setScan).catch((e) => setError(String(e)))
  }, [])

  if (error) return <div className="app"><p style={{ padding: 28, fontFamily: 'var(--mono)' }}>Failed to load scan: {error}</p></div>
  if (!scan) return <div className="app"><p style={{ padding: 28, fontFamily: 'var(--mono)' }}>Loading…</p></div>

  const selected = scan.nodes.find((n) => n.id === selectedId) ?? null

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
          <ScanForm />
        </div>

        {MODE === 'off' ? (
          <ul style={{ padding: '80px 28px', fontFamily: 'var(--mono)', fontSize: 13, listStyle: 'none' }}>
            {scan.nodes.map((n) => (
              <li key={n.id} style={{ marginBottom: 8, cursor: 'pointer' }} onClick={() => setSelectedId(n.id)}>
                {n.package_name}@{n.package_version} — vuln: {n.vuln_severity}
              </li>
            ))}
          </ul>
        ) : (
          <Graph nodes={scan.nodes} edges={scan.edges} onSelect={setSelectedId} />
        )}

        <Legend scan={scan} />
      </div>
      <DetailPanel node={selected} onClose={() => setSelectedId(null)} />
    </div>
  )
}
