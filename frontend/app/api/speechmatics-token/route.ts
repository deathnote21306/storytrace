export async function GET() {
  const r = await fetch('https://mp.speechmatics.com/v1/api_keys?type=rt', {
    method: 'POST',
    headers: {
      // SPEECHMATICS_KEY — no NEXT_PUBLIC_ prefix; stays server-side only
      'Authorization': `Bearer ${process.env.SPEECHMATICS_KEY}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ ttl: 60 }),
  })

  if (!r.ok) {
    return Response.json({ error: 'Failed to fetch Speechmatics token' }, { status: r.status })
  }

  const data = await r.json()
  return Response.json({ token: data.key_value })
}
