import { NextResponse } from 'next/server'

/** Server-side API base URL — change API_URL on Render without rebuilding. */
export async function GET() {
  const apiUrl =
    process.env.API_URL?.replace(/\/$/, '') ||
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') ||
    'http://localhost:8000'

  return NextResponse.json({ apiUrl })
}
