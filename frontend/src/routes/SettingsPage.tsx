import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import { type Provider, useLLMSettings } from '../hooks/useLLMSettings'
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
  const { provider, setProvider, setModel, modelOf } = useLLMSettings()
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
                  onClick={() => setProvider(p.id)}
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
            <p className="text-sm text-slate-600">
              서버에 키가 설정돼 있어 직접 입력하지 않아도 됩니다.
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
