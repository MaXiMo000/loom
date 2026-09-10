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
      scale={hovered ? 1.15 : 1}
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
