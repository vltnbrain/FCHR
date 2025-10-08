import { useCallback, useEffect, useRef, useState } from 'react'
import { Modality } from '@google/genai'
import { useLiveAPIContext } from '../../contexts/LiveAPIContext'
import { AudioRecorder } from '../../lib/audio-recorder'

type IdeaStatus = {
  id: number
  title: string
  status?: string | null
  created_at?: string | null
}

type DialogueEntry = {
  id: string
  role: 'bot' | 'user'
  text: string
}

type StatusCount = {
  status: string
  count: number
}

type ProjectCard = {
  id: number
  title: string
  status?: string | null
  owner_email?: string | null
  created_at?: string | null
}

type ReviewCard = {
  id: number
  idea_id: number
  idea_title: string
  stage: string
  decision?: string | null
  created_at?: string | null
}

type AssignmentCard = {
  id: number
  idea_id: number
  idea_title: string
  assignment_status: string
  idea_status?: string | null
  created_at?: string | null
}

type ProjectsOverview = {
  role: string
  my_projects: ProjectCard[]
  company_projects: ProjectCard[]
  status_counts: StatusCount[]
  analyst_queue: ReviewCard[]
  finance_queue: ReviewCard[]
  developer_assignments: AssignmentCard[]
  invites: AssignmentCard[]
}

const MAX_DIALOG_LINES = 12

export type VoiceConsoleProps = {
  token: string | null
  currentUser: { email: string; role: string } | null
  introText: string
  overview: ProjectsOverview | null
  onRegister: (email: string, password: string) => Promise<boolean>
  onLogin: (email: string, password: string) => Promise<boolean>
  onCreateIdea: (title: string, description: string) => Promise<boolean>
  onRefresh: () => void
  onFetchStatuses: () => Promise<{ ok: boolean; items?: IdeaStatus[]; error?: string }>
  onFetchOverview: () => Promise<void>
  authError?: string | null
  registrationError?: string | null
}

const SYSTEM_PROMPT = `Ты HUB BOT — голосовой наставник AI HUB IT-MONSTERS. Помогай гостям разобраться с площадкой, а авторизованным пользователям рассказывай о проектах, статусах и задачах. Говори коротко, дружелюбно и по делу.`
const DEFAULT_IDEA_TITLE = 'Идея от HUB BOT'

const makeEntry = (role: 'bot' | 'user', text: string): DialogueEntry => ({
  id: `${Date.now()}-${Math.random().toString(16).slice(2)}`,
  role,
  text: text.trim(),
})

const formatStatusList = (items: IdeaStatus[]): string => {
  if (!items.length) {
    return 'В базе пока нет идей, связанных с вашей учётной записью.'
  }
  const limited = items.slice(0, 3)
  const fragments = limited.map((item) => {
    const status = (item.status ?? 'статус не указан').replace(/_/g, ' ')
    const created = item.created_at ? `, создана ${new Date(item.created_at).toLocaleDateString('ru-RU')}` : ''
    return `${item.title}: ${status}${created}.`
  })
  if (items.length > limited.length) {
    fragments.push(`Всего идей в работе: ${items.length}.`)
  }
  return fragments.join(' ')
}

const summarizeProjects = (label: string, items: ProjectCard[], limit = 3): string => {
  if (!items.length) {
    return `${label}: пока ничего нет.`
  }
  const parts = items.slice(0, limit).map((item) => {
    const status = (item.status ?? 'статус не указан').replace(/_/g, ' ')
    return `${item.title} — ${status}.`
  })
  if (items.length > limit) {
    parts.push(`Всего ${items.length} проектов.`)
  }
  return `${label}: ${parts.join(' ')}`
}

const summarizeQueue = (label: string, items: ReviewCard[]): string => {
  if (!items.length) {
    return `${label}: очередь пуста.`
  }
  return `${label}: ${items.length} задач(и), например ${items[0].idea_title}.`
}

const summarizeAssignments = (label: string, items: AssignmentCard[]): string => {
  if (!items.length) {
    return `${label}: нет активных назначений.`
  }
  const first = items[0]
  return `${label}: ${items.length} назначений, ближайшее — ${first.idea_title} (${first.assignment_status}).`
}

export default function VoiceConsole({
  token,
  currentUser,
  introText,
  overview,
  onRegister,
  onLogin,
  onCreateIdea,
  onRefresh,
  onFetchStatuses,
  onFetchOverview,
  authError,
  registrationError,
}: VoiceConsoleProps) {
  const { client, connect, disconnect, connected, setConfig, spokenText, volume, inputVolume, setInputVolume } =
    useLiveAPIContext()
  const recorderRef = useRef<AudioRecorder | null>(null)
  const lastStreamRef = useRef<string>('')
  const introSpokenRef = useRef(false)
  const lastAuthErrorRef = useRef<string | null>(null)
  const lastRegErrorRef = useRef<string | null>(null)

  const [muted, setMuted] = useState(false)
  const [dialogue, setDialogue] = useState<DialogueEntry[]>([])
  const [pendingAction, setPendingAction] = useState<'register' | 'login' | 'idea' | null>(null)
  const [cachedEmail, setCachedEmail] = useState('')
  const [cachedPassword, setCachedPassword] = useState('')
  const [cachedIdea, setCachedIdea] = useState('')
  const [cachedIdeaTitle, setCachedIdeaTitle] = useState(DEFAULT_IDEA_TITLE)
  const [busy, setBusy] = useState(false)

  const appendDialogue = useCallback((entry: DialogueEntry) => {
    if (!entry.text) {
      return
    }
    setDialogue((prev) => {
      if (prev.length && prev[prev.length - 1].role === entry.role && prev[prev.length - 1].text === entry.text) {
        return prev
      }
      const next = [...prev, entry]
      if (next.length > MAX_DIALOG_LINES) {
        return next.slice(next.length - MAX_DIALOG_LINES)
      }
      return next
    })
  }, [])

  const speak = useCallback(
    (message: string) => {
      const trimmed = message.trim()
      if (!trimmed) {
        return
      }
      appendDialogue(makeEntry('bot', trimmed))
      if (connected) {
        try {
          client.send({ text: trimmed }, true)
        } catch {
          // ignore transport errors
        }
      }
    },
    [appendDialogue, client, connected],
  )

  useEffect(() => {
    setConfig({
      responseModalities: [Modality.AUDIO, Modality.TEXT],
      speechConfig: {
        voiceConfig: {
          voiceName: 'ru-RU-Standard-A',
        },
      },
      systemInstruction: {
        parts: [{ text: SYSTEM_PROMPT }],
      },
    })
  }, [setConfig])

  useEffect(() => {
    appendDialogue(makeEntry('bot', introText))
    introSpokenRef.current = false
  }, [introText, appendDialogue])

  useEffect(() => {
    if (connected && !introSpokenRef.current) {
      speak(introText)
      introSpokenRef.current = true
    }
  }, [connected, introText, speak])

  useEffect(() => {
    if (!connected) {
      return
    }
    if (!recorderRef.current) {
      recorderRef.current = new AudioRecorder()
    }
    const recorder = recorderRef.current

    const handleData = (base64: string) => {
      client.sendRealtimeInput([
        {
          mimeType: 'audio/pcm;rate=16000',
          data: base64,
        },
      ])
    }

    const handleVolume = (value: number) => {
      setInputVolume(value)
    }

    if (!muted) {
      recorder.on('data', handleData).on('volume', handleVolume).start()
    }

    return () => {
      recorder.off('data', handleData)
      recorder.off('volume', handleVolume)
      recorder.stop()
    }
  }, [client, connected, muted, setInputVolume])

  useEffect(() => {
    if (!spokenText) {
      return
    }
    const trimmed = spokenText.trim()
    if (!trimmed || trimmed === lastStreamRef.current) {
      return
    }
    lastStreamRef.current = trimmed
    appendDialogue(makeEntry('bot', trimmed))
  }, [spokenText, appendDialogue])

  const requireAuth = useCallback(() => {
    speak('Чтобы выполнить это действие, сначала авторизуйтесь.')
  }, [speak])

  const handleStatusRequest = useCallback(async () => {
    if (!token) {
      requireAuth()
      return
    }
    setBusy(true)
    try {
      const result = await onFetchStatuses()
      if (!result.ok) {
        speak(result.error ?? 'Не удалось получить статусы ваших идей.')
        return
      }
      speak(formatStatusList(result.items ?? []))
    } finally {
      setBusy(false)
    }
  }, [onFetchStatuses, requireAuth, speak, token])

  const handleOverviewRequest = useCallback(
    async (scope: 'mine' | 'company' | 'queues') => {
      if (!token) {
        requireAuth()
        return
      }
      if (!overview) {
        await onFetchOverview()
      }
      const data = overview
      if (!data) {
        speak('Не удалось получить данные о проектах.')
        return
      }
      if (scope === 'mine') {
        speak(summarizeProjects('Ваши проекты', data.my_projects))
      } else if (scope === 'company') {
        speak(summarizeProjects('Проекты компании', data.company_projects))
      } else {
        const fragments: string[] = []
        if (data.analyst_queue.length) {
          fragments.push(summarizeQueue('Очередь аналитика', data.analyst_queue))
        }
        if (data.finance_queue.length) {
          fragments.push(summarizeQueue('Очередь финансов', data.finance_queue))
        }
        if (data.developer_assignments.length) {
          fragments.push(summarizeAssignments('Назначения разработчика', data.developer_assignments))
        }
        if (!fragments.length) {
          fragments.push('Очереди сейчас пусты.')
        }
        speak(fragments.join(' '))
      }
    },
    [onFetchOverview, overview, requireAuth, speak, token],
  )

  useEffect(() => {
    if (!spokenText) {
      return
    }
    const normalized = spokenText.toLowerCase()
    if (normalized.includes('регист')) {
      setPendingAction('register')
    } else if (normalized.includes('логин') || normalized.includes('вход') || normalized.includes('авториз')) {
      setPendingAction('login')
    } else if (normalized.includes('иде') && (normalized.includes('создай') || normalized.includes('добав') || normalized.includes('запиши'))) {
      setPendingAction('idea')
      setCachedIdea(spokenText)
    } else if (normalized.includes('статус') || normalized.includes('что с иде') || normalized.includes('прогресс')) {
      void handleStatusRequest()
    } else if (normalized.includes('мои проект') || normalized.includes('мои задачи')) {
      void handleOverviewRequest('mine')
    } else if (normalized.includes('проекты компании') || normalized.includes('все проекты')) {
      void handleOverviewRequest('company')
    } else if (normalized.includes('очередь') || normalized.includes('аналит') || normalized.includes('финанс')) {
      void handleOverviewRequest('queues')
    }

    const emailMatch = spokenText.match(/[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}/)
    if (emailMatch) {
      setCachedEmail(emailMatch[0])
    }

    const passwordMatch = spokenText.match(/парол[ья]\s+(\S+)/i)
    if (passwordMatch) {
      setCachedPassword(passwordMatch[1])
    }
  }, [spokenText, handleOverviewRequest, handleStatusRequest])

  useEffect(() => {
    if (!authError || authError === lastAuthErrorRef.current) {
      return
    }
    lastAuthErrorRef.current = authError
    speak(`Авторизация: ${authError}`)
  }, [authError, speak])

  useEffect(() => {
    if (!registrationError || registrationError === lastRegErrorRef.current) {
      return
    }
    lastRegErrorRef.current = registrationError
    speak(`Регистрация: ${registrationError}`)
  }, [registrationError, speak])

  const handleAction = async () => {
    if (!pendingAction) {
      return
    }
    setBusy(true)
    try {
      if (pendingAction === 'register') {
        if (!cachedEmail || !cachedPassword) {
          speak('Назовите email и пароль, чтобы я мог зарегистрировать вас.')
          return
        }
        const ok = await onRegister(cachedEmail, cachedPassword)
        speak(ok ? 'Регистрация завершена. Проверьте почту и продолжайте.' : 'Не удалось зарегистрироваться. Проверьте данные в форме.')
      } else if (pendingAction === 'login') {
        if (!cachedEmail || !cachedPassword) {
          speak('Чтобы войти, назовите email и пароль.')
          return
        }
        const ok = await onLogin(cachedEmail, cachedPassword)
        speak(ok ? 'Вы успешно вошли. Готов рассказать про ваши проекты.' : 'Не удалось войти. Проверьте реквизиты на форме.')
      } else if (pendingAction === 'idea') {
        if (!token) {
          requireAuth()
          return
        }
        const ideaText = cachedIdea.trim()
        if (!ideaText) {
          speak('Опишите идею, которую нужно сохранить.')
          return
        }
        const ok = await onCreateIdea(cachedIdeaTitle || DEFAULT_IDEA_TITLE, ideaText)
        speak(ok ? 'Идея зафиксирована и отправлена на рассмотрение.' : 'Не удалось сохранить идею. Попробуйте ещё раз.')
        if (ok) {
          setCachedIdea('')
          setCachedIdeaTitle(DEFAULT_IDEA_TITLE)
        }
      }
      onRefresh()
    } finally {
      setBusy(false)
      setPendingAction(null)
    }
  }

  const connectionLabel = connected ? 'Отключить HUB BOT' : 'Подключить HUB BOT'

  return (
    <div className="voice-console">
      <div className="voice-console__controls">
        <button type="button" className="button button--solid" onClick={connected ? disconnect : connect}>
          {connectionLabel}
        </button>
        <button
          type="button"
          className="button button--outline"
          onClick={() => setMuted(!muted)}
          disabled={!connected}
        >
          {muted ? 'Включить звук' : 'Выключить звук'}
        </button>
        <div className="voice-console__meters">
          <span>Бот: {Math.round(volume * 100)}%</span>
          <span>Микрофон: {Math.round(inputVolume * 100)}%</span>
          <span>{busy ? 'Обрабатываю…' : 'Готов к диалогу'}</span>
        </div>
      </div>

      <div className="voice-console__stream">
        {dialogue.length === 0 ? (
          <div className="voice-console__notice">HUB BOT ждёт голосовую команду.</div>
        ) : (
          <ul>
            {dialogue.map((entry) => (
              <li key={entry.id} className={`voice-console__line voice-console__line--${entry.role}`}>
                <span>{entry.text}</span>
              </li>
            ))}
          </ul>
        )}
      </div>

      {pendingAction && (
        <div className="voice-console__pending">
          <p>
            {pendingAction === 'register'
              ? 'Запрос на регистрацию. HUB BOT использует найденные email и пароль.'
              : pendingAction === 'login'
              ? 'Запрос на авторизацию. Проверьте данные перед подтверждением.'
              : 'HUB BOT подготовил текст идеи. Перед отправкой можно отредактировать.'}
          </p>
          {pendingAction !== 'idea' && (
            <p className="voice-console__notice">
              Email: {cachedEmail || '—'} · Пароль: {cachedPassword || '—'}
            </p>
          )}
          {pendingAction === 'idea' && (
            <textarea
              rows={4}
              value={cachedIdea}
              onChange={(event) => setCachedIdea(event.target.value)}
              placeholder="Опишите идею своими словами"
            />
          )}
          <div className="voice-console__actions">
            {pendingAction === 'idea' && (
              <input
                value={cachedIdeaTitle}
                onChange={(event) => setCachedIdeaTitle(event.target.value)}
                placeholder="Заголовок идеи"
              />
            )}
            <button type="button" className="button button--solid" onClick={handleAction} disabled={busy}>
              {busy ? 'Обрабатываю…' : 'Подтвердить'}
            </button>
          </div>
        </div>
      )}

      {!token && (
        <div className="voice-console__notice">
          HUB BOT доступен без регистрации: спросите, как устроена площадка и как предложить идею.
        </div>
      )}

      {currentUser && token && (
        <div className="voice-console__notice">
          HUB BOT знает, что вы — {currentUser.email}. Спросите о статусах, очередях или назначениях.
        </div>
      )}
    </div>
  )
}
