import { describe, expect, it } from 'vitest'
import { COLOR, computeInDegree, nodeColor, nodeRadius } from './severity'

describe('nodeColor', () => {
  it('colors a critical-vuln node escalate regardless of providence', () => {
    const c = nodeColor({ id: 'a', vuln_severity: 'critical', providence_status: 'verified' })
    expect(c.color).toBe(COLOR.escalate)
  })

  it('vulnerability beats a verified providence status', () => {
    const c = nodeColor({ id: 'a', vuln_severity: 'high', providence_status: 'verified' })
    expect(c.color).toBe(COLOR.escalate)
  })

  it('a clean, providence-verified node glows beam', () => {
    const c = nodeColor({ id: 'a', vuln_severity: 'none', providence_status: 'verified' })
    expect(c.color).toBe(COLOR.beam)
  })

  it('a clean node with nothing verified reads neutral, not guessed-good', () => {
    const c = nodeColor({ id: 'a', vuln_severity: 'none', providence_status: 'unverified' })
    expect(c.color).toBe(COLOR.alloy)
    expect(c.emissiveIntensity).toBeLessThan(0.5)
  })
})

describe('computeInDegree', () => {
  it('counts how many edges point at each node', () => {
    const edges = [
      { from_node: 'a', to_node: 'b' },
      { from_node: 'c', to_node: 'b' },
      { from_node: 'a', to_node: 'd' },
    ]
    const counts = computeInDegree(edges)
    expect(counts.get('b')).toBe(2)
    expect(counts.get('d')).toBe(1)
    expect(counts.get('a')).toBeUndefined()
  })
})

describe('nodeRadius', () => {
  it('grows monotonically with in-degree, and clamps at a max', () => {
    const r0 = nodeRadius(0)
    const r1 = nodeRadius(1)
    const r100 = nodeRadius(100)
    expect(r1).toBeGreaterThan(r0)
    expect(r100).toBeLessThanOrEqual(1.4)
  })
})
