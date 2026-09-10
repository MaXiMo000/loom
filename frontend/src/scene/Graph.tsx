import { Bounds, OrbitControls } from '@react-three/drei'
import { Canvas } from '@react-three/fiber'
import { Bloom, EffectComposer } from '@react-three/postprocessing'
import { useMemo } from 'react'
import type { ScanEdge, ScanNode } from '../api'
import { computeInDegree, nodeRadius } from '../lib/severity'
import { STILL } from '../lib/mode'
import { computeLayout } from './layout'
import { Edge } from './Edge'
import { Node } from './Node'

export function Graph({ nodes, edges, onSelect }: {
  nodes: ScanNode[]
  edges: ScanEdge[]
  onSelect: (id: string) => void
}) {
  // Settled once per graph, not re-run every frame — see layout.ts.
  const laidOut = useMemo(() => computeLayout(nodes, edges), [nodes, edges])
  const inDegree = useMemo(() => computeInDegree(edges), [edges])

  return (
    <Canvas camera={{ position: [0, 0, 14], fov: 50 }} dpr={[1, 2]}>
      <color attach="background" args={['#08090C']} />
      <ambientLight intensity={0.5} />
      <directionalLight position={[6, 8, 6]} intensity={1.1} />
      <directionalLight position={[-6, -4, -6]} intensity={0.3} color="#86E9DE" />

      {/* d3-force-3d's settled coordinates land at whatever scale its charge/
          link constants produce — SPEC.md §13 says that tuning can't be
          right until real data is in front of it, so instead of guessing
          constants, Bounds auto-fits the camera to whatever comes out. */}
      {/* No `observe`: the node set is static once a scan is complete, and
          `observe` re-fits on any bounding-box change, including a mesh's
          own hover material state — fit once (keyed on the graph itself)
          instead of continuously watching for changes that shouldn't move
          the camera. */}
      <Bounds key={`${nodes.length}-${edges.length}`} fit clip margin={1.4}>
        {edges.map((e) => {
          const a = laidOut.get(e.from_node)
          const b = laidOut.get(e.to_node)
          if (!a || !b) return null
          return <Edge key={e.id} from={[a.x, a.y, a.z]} to={[b.x, b.y, b.z]} />
        })}

        {[...laidOut.values()].map((n) => (
          <Node key={n.id} node={n} radius={nodeRadius(inDegree.get(n.id) ?? 0)} onSelect={onSelect} />
        ))}
      </Bounds>

      <OrbitControls enableDamping={!STILL} autoRotate={false} makeDefault />

      {!STILL && (
        <EffectComposer>
          <Bloom luminanceThreshold={0.65} luminanceSmoothing={0.3} intensity={0.8} mipmapBlur />
        </EffectComposer>
      )}
    </Canvas>
  )
}
