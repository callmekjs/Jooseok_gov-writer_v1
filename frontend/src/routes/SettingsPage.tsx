import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { KEY_PATTERN, type Provider, useLLMSettings } from '../hooks/useLLMSettings'
import { getJson } from '../lib/api'

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'anthropic', label: 'Anthropic' },
]

type ModelRow = { id: string; tier: string; won_per_doc: number }
type ModelCatalog = Record<string, ModelRow[]>
type ModelsStatus = 'loading' | 'error' | 'ready'

const CARD = 'rounded-2xl border border-slate-200 bg-white p-5 sm:p-6'

export default function SettingsPage() {
  const { provider, setProvider, setKey, setModel, keyOf, modelOf } = useLLMSettings()
  const [draft, setDraft] = useState(keyOf(provider))
  const [status, setStatus] = useState<string | null>(null)
  const [models, setModels] = useState<ModelCatalog>({})
  const [modelsStatus, setModelsStatus] = useState<ModelsStatus>('loading')

  useEffect(() => {
    getJson<ModelCatalog>('/api/models')
      .then((data) => {
        setModels(data)
        setModelsStatus('ready')
      })
      .catch(() => setModelsStatus('error'))
  }, [])

  async function test() {
    if (!KEY_PATTERN[provider].test(draft)) {
      setStatus(`키 형식이 올바르지 않습니다 (${provider} 키는 ${provider === 'openai' ? 'sk-' : 'sk-ant-'}로 시작합니다)`)
      return
    }
    setStatus('확인 중...')
    const res = await fetch('/api/validate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key: draft }),
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok) {
      setKey(provider, draft)
      setStatus('정상 연결되었습니다.')
    } else {
      setStatus(data.detail ?? '연결에 실패했습니다.')
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50 p-4 sm:p-6">
      <div className="mx-auto max-w-4xl">
        <header className="pt-6 pb-6 sm:pt-8 sm:pb-8">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-blue-600">
            <ArrowLeft className="h-4 w-4" /> 홈으로
          </Link>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">설정</h1>
        </header>

        <div className="space-y-4">
          <section className={CARD}>
            <h2 className="mb-3 font-semibold text-slate-900">AI 회사</h2>
            <div className="flex gap-2">
              {PROVIDERS.map((p) => (
                <button
                  key={p.id}
                  onClick={() => { setProvider(p.id); setDraft(keyOf(p.id)); setStatus(null) }}
                  className={`rounded-xl border px-4 py-2 text-sm transition-colors ${
                    provider === p.id
                      ? 'border-blue-500 bg-blue-50 text-blue-700'
                      : 'border-slate-200 text-slate-600 hover:border-slate-300'
                  }`}
                >
                  {p.label}
                </button>
              ))}
            </div>
          </section>

          <section className={CARD}>
            <h2 className="mb-3 font-semibold text-slate-900">모델 등급</h2>

            {modelsStatus === 'loading' && (
              <p className="rounded-xl border border-slate-200 bg-slate-50 px-3 py-2 text-sm text-slate-500">
                모델 목록을 불러오는 중입니다... 첫 접속 시 서버가 깨어나느라 최대 1분 정도 걸릴 수 있습니다.
              </p>
            )}

            {modelsStatus === 'error' && (
              <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                모델 목록을 불러오지 못했습니다. 새로고침해 주세요.
              </p>
            )}

            {modelsStatus === 'ready' && (
              <div className="space-y-1">
                {(models[provider] ?? []).map((m) => (
                  <label
                    key={m.id}
                    className="flex cursor-pointer items-center gap-3 rounded-xl border border-slate-200 px-3 py-2 transition-colors hover:border-blue-300"
                  >
                    <input
                      type="radio"
                      name="model"
                      checked={modelOf(provider) === m.id}
                      onChange={() => setModel(provider, m.id)}
                    />
                    <span className="w-16 font-medium text-slate-900">{m.tier}</span>
                    <span className="flex-1 truncate font-mono text-sm text-slate-500">{m.id}</span>
                    <span className="text-sm text-slate-700">약 {m.won_per_doc}원</span>
                  </label>
                ))}
              </div>
            )}

            <p className="mt-3 text-xs text-slate-500">
              말씀자료 1건당 예상 비용입니다. 회사별로 마지막에 고른 등급을 따로 기억합니다.
            </p>
          </section>

          <section className={CARD}>
            <h2 className="mb-3 font-semibold text-slate-900">API 키</h2>
            <div className="flex gap-2">
              <input
                type="password"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                placeholder={provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
                className="flex-1 rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
              <button
                onClick={test}
                className="rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 transition-colors hover:border-blue-300 hover:bg-blue-50"
              >
                연결 시험
              </button>
            </div>
            {status && <p className="mt-2 text-sm text-slate-700">{status}</p>}
            <p className="mt-2 text-xs text-slate-500">
              키는 이 브라우저에만 저장되며, 요청 시 헤더로만 전달됩니다.
            </p>
          </section>
        </div>

        <footer className="mt-12 text-center text-xs text-slate-400 sm:mt-16">
          말씀자료 작성기
        </footer>
      </div>
    </div>
  )
}
