'use client'
import { Component, ReactNode } from 'react'

type Props = { children: ReactNode }
type State = { error: Error | null }

export default class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  render() {
    if (this.state.error) {
      return (
        <div className="flex flex-col items-center justify-center min-h-[60vh] gap-3 text-center px-4">
          <span className="material-symbols-outlined text-error text-[40px]">error</span>
          <p className="text-error text-sm">Something went wrong while rendering this page.</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="px-4 py-2 bg-primary-container text-on-primary-container rounded-lg text-sm font-mono uppercase tracking-wider hover:opacity-90 transition-opacity"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
