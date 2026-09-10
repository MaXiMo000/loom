/**
 * Same three-mode discipline as the parent portfolio's own
 * `portfolio/web/src/lib/mode.ts` — copied directly, not reinvented.
 *
 *   live  — full experience (orbit controls, force-layout settle, bloom)
 *   still — a single frozen frame (settled layout, no camera auto-motion)
 *   off   — no canvas at all (save-data, or no WebGL)
 */
export type Mode = 'live' | 'still' | 'off'

export function detectMode(): Mode {
  if (typeof window === 'undefined') return 'off'
  const saveData = (navigator as unknown as { connection?: { saveData?: boolean } })
    .connection?.saveData === true
  let webgl = false
  try {
    webgl = !!document.createElement('canvas').getContext('webgl2')
  } catch { /* no webgl */ }
  if (!webgl || saveData) return 'off'
  return matchMedia('(prefers-reduced-motion: reduce)').matches ? 'still' : 'live'
}

export const MODE: Mode = detectMode()
export const STILL = MODE === 'still'
