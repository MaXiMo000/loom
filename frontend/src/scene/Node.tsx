import { useState } from 'react'
import { nodeColor } from '../lib/severity'
import type { LaidOutNode } from './layout'

export function Node({ node, radius, onSelect }: {
  node: LaidOutNode
  radius: number
  onSelect: (id: string) => void
}) {
  const [hovered, setHovered] = useState(false)
  const { color, emissiveIntensity } = nodeColor(node)

  return (
    <mesh
      position={[node.x, node.y, node.z]}
      onClick={(e) => { e.stopPropagation(); onSelect(node.id) }}
      onPointerOver={(e) => { e.stopPropagation(); setHovered(true); document.body.style.cursor = 'pointer' }}
      onPointerOut={() => { setHovered(false); document.body.style.cursor = 'auto' }}
      // No scale-on-hover: <Bounds observe> in Graph.tsx re-fits the camera
      // to its children's real bounding box, so scaling one node on hover
      // shifted that box and made the camera visibly drift with the mouse.
      // Brightness alone is enough hover feedback.
    >
      <sphereGeometry args={[radius, 24, 24]} />
      <meshStandardMaterial
        color={color}
        emissive={color}
        emissiveIntensity={hovered ? emissiveIntensity + 0.4 : emissiveIntensity}
        roughness={0.35}
        metalness={0.2}
      />
    </mesh>
  )
}
