import { useEffect, useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Lock } from 'lucide-react'
import { APP_PASSWORD_STORAGE_KEY, getJson } from '../lib/api'

type GateStatus = 'checking' | 'locked' | 'open'

/** App.tsx 를 감싸는 게이트. 서버에 접속 암호(APP_PASSWORD)가 설정돼 있으면
 *  암호를 입력받아 localStorage 에 저장한 뒤에만 실제 화면을 보여준다.
 *  이 게이트는 UX 편의일 뿐 보안 경계가 아니다 — 실제 방어선은 서버의
 *  require_app_password 의존성이며, 여기서 무엇을 하든 AI 호출 엔드포인트는
 *  서버에서 다시 한 번 암호를 검사한다. */
export default function AuthGate({ children }: { children: ReactNode }) {
  const [status, setStatus] = useState<GateStatus>('checking')
  const [password, setPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)

  useEffect(() => {
    getJson<{ required: boolean }>('/api/auth/required')
      .then(({ required }) => {
        if (!required) {
          setStatus('open')
          return
        }
        setStatus(localStorage.getItem(APP_PASSWORD_STORAGE_KEY) ? 'open' : 'locked')
      })
      // 확인 자체가 실패해도(백엔드가 아직 안 깨어남 등) 화면을 잠그지 않는다 —
      // 어차피 실제 AI 호출은 서버가 다시 암호를 검사한다.
      .catch(() => setStatus('open'))
  }, [])

  async function submit(e: FormEvent) {
    e.preventDefault()
    if (!password || busy) return
    setError(null)
    setBusy(true)
    try {
      const res = await fetch('/api/auth/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ password }),
      })
      if (!res.ok) {
        setError('접속 암호가 올바르지 않습니다.')
        return
      }
      localStorage.setItem(APP_PASSWORD_STORAGE_KEY, password)
      setStatus('open')
    } catch {
      setError('서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.')
    } finally {
      setBusy(false)
    }
  }

  if (status === 'open') return <>{children}</>

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-white via-slate-50 to-blue-50 p-4 sm:p-6">
      <div className="w-full max-w-sm rounded-2xl border border-slate-200 bg-white p-6 sm:p-8">
        <div className="mb-4 flex items-center gap-2">
          <span className="rounded-lg bg-blue-50 p-2">
            <Lock className="h-5 w-5 text-blue-600" />
          </span>
          <h1 className="text-lg font-semibold text-slate-900">접속 암호</h1>
        </div>

        {status === 'checking' ? (
          <p className="text-sm text-slate-500">확인 중...</p>
        ) : (
          <>
            <p className="mb-4 text-sm text-slate-600">담당자에게 받은 접속 암호를 입력해 주세요.</p>
            <form onSubmit={submit}>
              <input
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="암호"
                autoFocus
                className="w-full rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
              {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
              <button
                type="submit"
                disabled={busy || !password}
                className="mt-4 w-full rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
              >
                {busy ? '확인 중...' : '입장'}
              </button>
            </form>
          </>
        )}
      </div>
    </div>
  )
}
