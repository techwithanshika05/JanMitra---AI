import { useEffect, useRef, useState } from 'react'
import { Mic, MicOff, Phone, PhoneOff, Volume2, VolumeX } from 'lucide-react'
import { api } from '@/utils/api'
import { useLanguage } from '@/contexts/LanguageContext'

const formatDuration = totalSeconds => {
  const seconds = Math.max(0, totalSeconds || 0)
  const minutes = Math.floor(seconds / 60)
  const remainder = seconds % 60
  return `${String(minutes).padStart(2, '0')}:${String(remainder).padStart(2, '0')}`
}

export default function Voice() {
  const { t } = useLanguage()
  const [ready, setReady] = useState(false)
  const [session, setSession] = useState(null)
  const [busy, setBusy] = useState(false)
  const [connectionState, setConnectionState] = useState('loading')
  const [elapsed, setElapsed] = useState(0)
  const [muted, setMuted] = useState(false)
  const [speakerMuted, setSpeakerMuted] = useState(false)
  const [agentSpeaking, setAgentSpeaking] = useState(false)
  const roomRef = useRef(null)
  const sessionRef = useRef(null)
  const audioRef = useRef(null)
  const startedAtRef = useRef(null)

  useEffect(() => {
    api.voiceHealth()
      .then(health => {
        const available = health?.status === 'ready'
        setReady(available)
        setConnectionState(available ? 'idle' : 'unavailable')
      })
      .catch(() => setConnectionState('unavailable'))

    return () => {
      roomRef.current?.disconnect()
      roomRef.current = null
    }
  }, [])

  useEffect(() => {
    if (!session || !startedAtRef.current) {
      setElapsed(0)
      return undefined
    }
    const update = () => setElapsed(Math.floor((Date.now() - startedAtRef.current) / 1000))
    update()
    const timer = window.setInterval(update, 1000)
    return () => window.clearInterval(timer)
  }, [session])

  const start = async () => {
    if (!ready || busy) return
    setBusy(true)
    setConnectionState('connecting')
    let created = null

    try {
      created = await api.startVoice('hi-IN')
      const { Room, RoomEvent, Track } = await import('livekit-client')
      const room = new Room({ adaptiveStream: true, dynacast: true })

      room.on(RoomEvent.TrackSubscribed, track => {
        if (track.kind !== Track.Kind.Audio || !audioRef.current) return
        const element = track.attach()
        element.autoplay = true
        element.muted = speakerMuted
        audioRef.current.appendChild(element)
      })
      room.on(RoomEvent.TrackUnsubscribed, track => track.detach().forEach(element => element.remove()))
      room.on(RoomEvent.ActiveSpeakersChanged, speakers => {
        setAgentSpeaking(speakers.some(participant => participant.identity !== room.localParticipant.identity))
      })
      room.on(RoomEvent.ParticipantConnected, () => setConnectionState('listening'))
      room.on(RoomEvent.ParticipantDisconnected, () => setAgentSpeaking(false))
      room.on(RoomEvent.Disconnected, () => {
        setConnectionState('ended')
        setAgentSpeaking(false)
      })

      await room.connect(created.livekit_url, created.token)
      await room.startAudio().catch(() => undefined)
      await room.localParticipant.setMicrophoneEnabled(true)

      roomRef.current = room
      sessionRef.current = created
      startedAtRef.current = Date.now()
      setSession(created)
      setMuted(false)
      setSpeakerMuted(false)
      setConnectionState(room.remoteParticipants.size > 0 ? 'listening' : 'connecting')
    } catch {
      roomRef.current?.disconnect()
      roomRef.current = null
      if (created?.session_id) {
        await api.endVoice(created.session_id, 'connection_failed').catch(() => undefined)
      }
      setConnectionState('error')
    } finally {
      setBusy(false)
    }
  }

  const end = async () => {
    if (!sessionRef.current || busy) return
    setBusy(true)
    const currentSession = sessionRef.current
    roomRef.current?.disconnect()
    await api.endVoice(currentSession.session_id).catch(() => undefined)
    roomRef.current = null
    sessionRef.current = null
    startedAtRef.current = null
    setSession(null)
    setConnectionState('idle')
    setAgentSpeaking(false)
    setMuted(false)
    setSpeakerMuted(false)
    audioRef.current?.replaceChildren()
    setBusy(false)
  }

  const toggleMicrophone = async () => {
    if (!roomRef.current) return
    const nextMuted = !muted
    await roomRef.current.localParticipant.setMicrophoneEnabled(!nextMuted).catch(() => undefined)
    setMuted(nextMuted)
  }

  const toggleSpeaker = () => {
    const nextMuted = !speakerMuted
    audioRef.current?.querySelectorAll('audio').forEach(element => {
      element.muted = nextMuted
    })
    setSpeakerMuted(nextMuted)
  }

  const status = {
    loading: t('loading'),
    idle: t('start_speaking'),
    connecting: t('connecting'),
    listening: agentSpeaking ? t('speaking') : muted ? t('muted') : t('listening'),
    ended: t('ended'),
    unavailable: t('unavailable'),
    error: t('try_again')
  }[connectionState]

  const active = Boolean(session)
  const animated = active && !muted

  return (
    <main className="min-h-[calc(100vh-90px)] grid place-items-center px-4 py-8 bg-[#fbfdfc] dark:bg-[#0b1210]">
      <section className="w-full max-w-3xl min-h-[620px] flex flex-col items-center justify-center text-center">
        <div className="relative w-64 h-64 sm:w-72 sm:h-72 grid place-items-center">
          <span className={`absolute inset-0 rounded-full bg-[#d9f7ef] dark:bg-[#153b32] ${animated ? 'animate-ping [animation-duration:2.4s]' : ''}`} />
          <span className={`absolute inset-8 rounded-full bg-[#a9ead9] dark:bg-[#176852] transition-transform duration-300 ${agentSpeaking ? 'scale-110' : ''}`} />
          <span className="relative w-40 h-40 sm:w-44 sm:h-44 flex items-center justify-center gap-2 rounded-full border-[7px] border-white/80 dark:border-[#b6e7da]/30 bg-[#0f5d4c] shadow-[0_28px_70px_rgba(13,124,102,.26)]">
            {[34, 58, 78, 48, 66].map((height, index) => (
              <i
                key={height}
                className={`w-2.5 rounded-full bg-white transition-all ${animated ? 'animate-pulse' : 'opacity-55'}`}
                style={{
                  height: animated ? height : 24,
                  animationDelay: `${index * 100}ms`,
                  animationDuration: agentSpeaking ? '650ms' : '1100ms'
                }}
              />
            ))}
          </span>
        </div>

        <h1 className="mt-10 text-[clamp(38px,6vw,68px)] font-black tracking-[-.06em] text-[#10271f] dark:text-white">
          {status}
        </h1>

        {active ? (
          <div className="mt-10 flex items-center justify-center gap-4">
            <button
              onClick={toggleMicrophone}
              className={`w-14 h-14 grid place-items-center rounded-full border ${muted ? 'bg-[#10271f] text-white border-[#10271f]' : 'bg-white dark:bg-[#17231f] border-[#dce6e1] dark:border-white/10'}`}
              aria-label={muted ? 'Unmute' : 'Mute'}
            >
              {muted ? <MicOff size={21} /> : <Mic size={21} />}
            </button>
            <button
              onClick={end}
              disabled={busy}
              className="h-16 px-8 inline-flex items-center gap-3 rounded-full bg-gradient-to-r from-[#ff6b6b] to-[#ed2f55] text-white font-black shadow-[0_17px_35px_rgba(237,47,85,.30)] disabled:opacity-60"
              aria-label="End call"
            >
              <span className="font-mono text-lg">{formatDuration(elapsed)}</span>
              <PhoneOff size={23} />
            </button>
            <button
              onClick={toggleSpeaker}
              className={`w-14 h-14 grid place-items-center rounded-full border ${speakerMuted ? 'bg-[#10271f] text-white border-[#10271f]' : 'bg-white dark:bg-[#17231f] border-[#dce6e1] dark:border-white/10'}`}
              aria-label={speakerMuted ? 'Speaker on' : 'Speaker off'}
            >
              {speakerMuted ? <VolumeX size={21} /> : <Volume2 size={21} />}
            </button>
          </div>
        ) : (
          <button
            onClick={start}
            disabled={!ready || busy}
            className="mt-10 w-16 h-16 grid place-items-center rounded-full bg-[#0d7c66] text-white shadow-[0_18px_36px_rgba(13,124,102,.28)] hover:scale-105 transition-transform disabled:opacity-40 disabled:transform-none"
            aria-label="Start speaking"
          >
            <Phone size={24} />
          </button>
        )}

        <div ref={audioRef} className="hidden" aria-label="Call audio" />
      </section>
    </main>
  )
}
