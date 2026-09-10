/** Phase 0's "entire home screen" (SPEC.md §8.4) — present so the chrome
 * reads complete, but disabled: real scanning is Phase 1. Submitting a URL
 * here does nothing yet on purpose, rather than faking a scan. */
export function ScanForm() {
  return (
    <form className="scan-form" onSubmit={(e) => e.preventDefault()}>
      <input
        type="text"
        placeholder="github.com/owner/repo (real scanning arrives in Phase 1)"
        disabled
        aria-label="Repository URL"
      />
      <button type="submit" disabled title="Real scanning arrives in Phase 1">
        Scan
      </button>
    </form>
  )
}
