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
          <p className="text-red-500 text-sm">Something went wrong while rendering this page.</p>
          <button
            onClick={() => this.setState({ error: null })}
            className="px-4 py-2 bg-[#1B3A6B] text-white rounded-lg text-sm hover:bg-[#2E5FA3] transition-colors"
          >
            Try again
          </button>
        </div>
      )
    }
    return this.props.children
  }
}
