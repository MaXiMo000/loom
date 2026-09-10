/** Typed client for the backend's 4 real routes (SPEC.md §7.7). */

export interface ScanNode {
  id: string
  package_name: string
  package_version: string
  depth: number
  vuln_severity: 'none' | 'low' | 'medium' | 'high' | 'critical' | 'unverified'
  vuln_detail: string | null
  drift_status: 'matched' | 'version_mismatch' | 'missing' | 'extra' | 'unverified'
  providence_status: 'verified' | 'unverified'
  policy_status: 'pass' | 'fail' | 'unverified'
  repo_stars: number | null
  repo_last_commit: string | null
}

export interface ScanEdge {
  id: string
  from_node: string
  to_node: string
}

export interface Scan {
  id: string
  repo_url: string
  ref: string
  commit_sha: string | null
  status: 'pending' | 'cloning' | 'resolving' | 'scanning' | 'complete' | 'failed'
  error: string | null
  lockfile_kind: string | null
  depth_cap: number
  total_package_count: number
  created_at: string
  completed_at: string | null
  nodes: ScanNode[]
  edges: ScanEdge[]
}

export interface ScanSummary {
  id: string
  repo_url: string
  ref: string
  status: Scan['status']
  created_at: string
  node_count: number
}

async function json<T>(res: Response): Promise<T> {
  if (!res.ok) {
    const detail = await res.text().catch(() => res.statusText)
    throw new Error(`${res.status} ${detail}`)
  }
  return res.json() as Promise<T>
}

export function createScan(repo_url: string, ref?: string): Promise<{ id: string; status: string }> {
  return fetch('/api/scans', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ repo_url, ref }),
  }).then((res) => json<{ id: string; status: string }>(res))
}

export function getScan(id: string): Promise<Scan> {
  return fetch(`/api/scans/${encodeURIComponent(id)}`).then((res) => json<Scan>(res))
}

export function listScans(repoUrl: string): Promise<ScanSummary[]> {
  return fetch(`/api/scans?repo_url=${encodeURIComponent(repoUrl)}`).then((res) => json<ScanSummary[]>(res))
}
