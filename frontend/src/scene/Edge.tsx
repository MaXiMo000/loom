import { useMemo } from 'react'
import * as THREE from 'three'

const UP = new THREE.Vector3(0, 1, 0)

/** A thin machined cylinder between two points — reads correctly under the
 * bloom pass, unlike THREE.Line, which ignores lighting entirely (SPEC.md
 * §8.3). */
export function Edge({ from, to }: { from: [number, number, number]; to: [number, number, number] }) {
  const { position, quaternion, length } = useMemo(() => {
    const a = new THREE.Vector3(...from)
    const b = new THREE.Vector3(...to)
    const dir = new THREE.Vector3().subVectors(b, a)
    const len = dir.length()
    const mid = a.clone().add(b).multiplyScalar(0.5)
    const quat = new THREE.Quaternion().setFromUnitVectors(UP, dir.normalize())
    return { position: mid, quaternion: quat, length: len }
  }, [from, to])

  return (
    <mesh position={position} quaternion={quaternion}>
      <cylinderGeometry args={[0.05, 0.05, length, 6]} />
      <meshStandardMaterial color="#3C4351" roughness={0.6} metalness={0.1} />
    </mesh>
  )
}
