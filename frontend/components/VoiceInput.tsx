'use client'
import { useState, useRef, useEffect } from 'react'

type Props = { onTranscript: (t: string) => void }

export default function VoiceInput({ onTranscript }: Props) {
  const [listening, setListening] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef<WebSocket | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const ctxRef = useRef<AudioContext | null>(null)

  useEffect(() => {
    return () => {
      wsRef.current?.close()
      streamRef.current?.getTracks().forEach(t => t.stop())
      ctxRef.current?.close()
    }
  }, [])

  const startListening = async () => {
    setError('')
    try {
      const res = await fetch('/api/speechmatics-token')
      if (!res.ok) throw new Error('Could not fetch Speechmatics token')
      const { token, error: tokenError } = await res.json()
      if (tokenError) throw new Error(tokenError)

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream

      const ws = new WebSocket(`wss://eu2.rt.speechmatics.com/v2?jwt=${token}`)
      wsRef.current = ws

      ws.onopen = () => {
        ws.send(
          JSON.stringify({
            message: 'StartRecognition',
            audio_format: { type: 'raw', encoding: 'pcm_f32le', sample_rate: 44100 },
            transcription_config: { language: 'en', enable_partials: true },
          }),
        )

        const ctx = new AudioContext({ sampleRate: 44100 })
        ctxRef.current = ctx
        const source = ctx.createMediaStreamSource(stream)
        const processor = ctx.createScriptProcessor(4096, 1, 1)
        processor.onaudioprocess = e => {
          if (ws.readyState === WebSocket.OPEN) {
            const pcm = e.inputBuffer.getChannelData(0)
            ws.send(pcm.buffer)
          }
        }
        source.connect(processor)
        processor.connect(ctx.destination)
        setListening(true)
      }

      ws.onmessage = e => {
        const data = JSON.parse(e.data)
        if (data.message === 'AddTranscript' && data.metadata?.transcript) {
          onTranscript(data.metadata.transcript)
        }
      }

      ws.onerror = () => {
        setError('WebSocket error — check Speechmatics API key')
        stopListening()
      }

      ws.onclose = () => setListening(false)
    } catch (err) {
      setError((err as Error).message || 'Could not start recording')
    }
  }

  const stopListening = () => {
    wsRef.current?.close()
    streamRef.current?.getTracks().forEach(t => t.stop())
    ctxRef.current?.close()
    wsRef.current = null
    streamRef.current = null
    ctxRef.current = null
    setListening(false)
  }

  return (
    <div className="flex flex-col items-center gap-1">
      <button
        type="button"
        onClick={listening ? stopListening : startListening}
        title={listening ? 'Stop recording' : 'Speak your topic'}
        className={`p-3 rounded-lg transition-all ${
          listening
            ? 'bg-error-container text-error animate-pulse'
            : 'bg-surface-container-highest border border-outline-variant text-on-surface hover:border-primary hover:text-primary'
        }`}
      >
        <span className="material-symbols-outlined text-[20px]">
          {listening ? 'stop_circle' : 'mic'}
        </span>
      </button>
      {error && (
        <p className="text-xs text-error max-w-xs text-center absolute -bottom-8">{error}</p>
      )}
    </div>
  )
}
