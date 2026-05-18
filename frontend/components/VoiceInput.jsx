'use client'
import { useState, useRef } from 'react'

export default function VoiceInput({ onTranscript }) {
  const [listening, setListening] = useState(false)
  const [error, setError] = useState('')
  const wsRef = useRef(null)
  const streamRef = useRef(null)
  const ctxRef = useRef(null)

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
        ws.send(JSON.stringify({
          message: 'StartRecognition',
          audio_format: { type: 'raw', encoding: 'pcm_f32le', sample_rate: 44100 },
          transcription_config: { language: 'en', enable_partials: true },
        }))

        const ctx = new AudioContext({ sampleRate: 44100 })
        ctxRef.current = ctx
        const source = ctx.createMediaStreamSource(stream)
        // ScriptProcessor is deprecated but universally supported without a bundler-compatible worklet
        const processor = ctx.createScriptProcessor(4096, 1, 1)
        processor.onaudioprocess = (e) => {
          if (ws.readyState === WebSocket.OPEN) {
            const pcm = e.inputBuffer.getChannelData(0)
            ws.send(pcm.buffer)
          }
        }
        source.connect(processor)
        processor.connect(ctx.destination)
      }

      ws.onmessage = (e) => {
        const data = JSON.parse(e.data)
        if (
          (data.message === 'AddTranscript' || data.message === 'AddPartialTranscript') &&
          data.metadata?.transcript
        ) {
          onTranscript(data.metadata.transcript)
        }
      }

      ws.onerror = () => {
        setError('WebSocket error — check Speechmatics API key')
        stopListening()
      }

      ws.onclose = () => setListening(false)

      setListening(true)
    } catch (err) {
      setError(err.message || 'Could not start recording')
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
        className={`p-3 rounded-full transition-colors ${
          listening
            ? 'bg-red-500 animate-pulse text-white'
            : 'bg-[#2E5FA3] hover:bg-[#1B3A6B] text-white'
        }`}
      >
        {listening ? '⏹' : '🎙'}
      </button>
      {error && <p className="text-xs text-red-500 max-w-xs text-center">{error}</p>}
    </div>
  )
}
