import type { Metadata } from 'next'
import { Hanken_Grotesk, JetBrains_Mono } from 'next/font/google'
import Link from 'next/link'
import './globals.css'

const hanken = Hanken_Grotesk({
  variable: '--font-hanken',
  subsets: ['latin'],
  weight: ['400', '500', '600', '700'],
})

const jetbrains = JetBrains_Mono({
  variable: '--font-jetbrains',
  subsets: ['latin'],
  weight: ['400', '500', '700'],
})

export const metadata: Metadata = {
  title: 'StoryTrace — Git for News',
  description: 'Track how news stories mutate across countries and outlets',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html
      lang="en"
      className={`dark ${hanken.variable} ${jetbrains.variable} h-full antialiased`}
    >
      <head>
        <link
          href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@24,400,0,0"
          rel="stylesheet"
        />
      </head>
      <body className="min-h-full flex flex-col bg-background text-on-background font-sans overflow-x-hidden selection:bg-primary-container/40">
        <nav className="bg-surface-container-high flex justify-between items-center px-4 md:px-10 h-16 w-full fixed top-0 border-b border-outline-variant z-50">
          <div className="flex items-center gap-6 md:gap-8">
            <Link
              href="/"
              className="text-lg md:text-xl font-bold text-on-surface tracking-tight"
            >
              StoryTrace
            </Link>
            <div className="hidden md:flex gap-6">
              <Link
                href="/explore"
                className="text-[11px] font-mono font-bold uppercase tracking-wider text-on-surface-variant hover:text-on-surface transition-colors"
              >
                Explore
              </Link>
            </div>
          </div>
          <Link
            href="/"
            className="flex items-center gap-2 bg-primary-container text-on-primary-container px-4 py-2 rounded-lg text-[11px] font-mono font-bold uppercase tracking-wider hover:opacity-90 transition-opacity active:scale-95"
          >
            <span className="material-symbols-outlined text-[18px]">add</span>
            New Trace
          </Link>
        </nav>
        <main className="flex-1 pt-16">{children}</main>
      </body>
    </html>
  )
}
