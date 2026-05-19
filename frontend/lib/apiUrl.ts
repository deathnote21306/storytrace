let cached: string | null = null

/** Resolve backend URL: prefers runtime API_URL from /api/config (Render/Vultr swaps). */
export async function getApiUrl(): Promise<string> {
  if (cached) return cached
  const fallback = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000'
  try {
    const res = await fetch('/api/config', { cache: 'no-store' })
    if (res.ok) {
      const { apiUrl } = await res.json()
      if (apiUrl) {
        cached = String(apiUrl).replace(/\/$/, '')
        return cached
      }
    }
  } catch {
    /* use fallback */
  }
  cached = fallback
  return cached
}
