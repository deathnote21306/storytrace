import type { Metadata } from 'next'
import { Geist, Geist_Mono } from 'next/font/google'
import Link from 'next/link'
import './globals.css'

const geistSans = Geist({ variable: '--font-geist-sans', subsets: ['latin'] })
const geistMono = Geist_Mono({ variable: '--font-geist-mono', subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'StoryTrace — Git for News',
  description: 'Track how news stories mutate across countries and outlets',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-white text-gray-900">
        <nav className="bg-[#1B3A6B] px-6 py-3 flex items-center gap-8">
          <Link href="/" className="text-white font-bold text-lg tracking-tight">
            StoryTrace
          </Link>
          <Link href="/explore" className="text-blue-200 hover:text-white text-sm transition-colors">
            Explore
          </Link>
        </nav>
        <main className="flex-1">{children}</main>
      </body>
    </html>
  )
}
