import { useState } from 'react'

/** SPEC.md §8.4's "entire home screen": a repo URL + submit, real now that
 * Phase 1 has a real backend behind it. */
export function ScanForm({ onSubmit, busy }: { onSubmit: (repoUrl: string) => void; busy: boolean }) {
  const [value, setValue] = useState('')

  return (
    <form
      className="scan-form"
      onSubmit={(e) => {
        e.preventDefault()
        if (value.trim()) onSubmit(value.trim())
      }}
    >
      <input
        type="text"
        placeholder="https://github.com/owner/repo"
        value={value}
        onChange={(e) => setValue(e.target.value)}
        disabled={busy}
        aria-label="Repository URL"
      />
      <button type="submit" disabled={busy || !value.trim()}>
        {busy ? 'Scanning…' : 'Scan'}
      </button>
    </form>
  )
}
