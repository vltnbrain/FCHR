import { useEffect, useMemo, useState } from 'react'

const TITLE = 'Гид по голосовому режиму'
const DESCRIPTION = 'AI Hub подскажет, как быстрее всего внести идею голосом и что происходит после отправки.'
const INSTRUCTIONS = 'Нажмите «Запустить», чтобы прослушать краткую инструкцию и подключить микрофон.'
const FALLBACK = 'Похоже, что ваш браузер не поддерживает синтез речи. Воспользуйтесь текстовой инструкцией.'
const BUTTON_SPEAK = 'Запустить'
const BUTTON_STOP = 'Остановить'
const EXTRA_LINE = 'Если звук не воспроизводится, убедитесь, что вкладке разрешён доступ к динамикам.'
const INTRO = 'Привет! Я голосовой помощник AI Hub.'

export default function VoiceGuide() {
  const [supported, setSupported] = useState(false)
  const [speaking, setSpeaking] = useState(false)

  useEffect(() => {
    setSupported(typeof window !== 'undefined' && 'speechSynthesis' in window)
    return () => {
      if (typeof window !== 'undefined' && window.speechSynthesis) {
        window.speechSynthesis.cancel()
      }
    }
  }, [])

  const script = useMemo(
    () => [INTRO, DESCRIPTION, INSTRUCTIONS, EXTRA_LINE].join(' '),
    [],
  )

  const toggleSpeech = () => {
    if (!supported || typeof window === 'undefined') {
      return
    }
    const synth = window.speechSynthesis
    if (speaking) {
      synth.cancel()
      setSpeaking(false)
      return
    }
    synth.cancel()
    const utterance = new SpeechSynthesisUtterance(script)
    utterance.lang = 'ru-RU'
    utterance.rate = 1
    utterance.pitch = 1
    utterance.onend = () => setSpeaking(false)
    utterance.onerror = () => setSpeaking(false)
    setSpeaking(true)
    synth.speak(utterance)
  }

  return (
    <section className="section">
      <header className="section__header">
        <h2>{TITLE}</h2>
        <p>{DESCRIPTION}</p>
      </header>
      <p className="voice-guide__summary">{INSTRUCTIONS}</p>
      <p className="voice-guide__summary">{EXTRA_LINE}</p>
      <div className="voice-guide__controls">
        <button type="button" className="button" disabled={!supported} onClick={toggleSpeech}>
          {speaking ? BUTTON_STOP : BUTTON_SPEAK}
        </button>
        {!supported && <span className="helper-text">{FALLBACK}</span>}
      </div>
    </section>
  )
}
