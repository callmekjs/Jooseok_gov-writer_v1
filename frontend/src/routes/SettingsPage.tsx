import { useEffect, useState } from 'react'
import { KEY_PATTERN, type Provider, useLLMSettings } from '../hooks/useLLMSettings'
import { getJson } from '../lib/api'

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'anthropic', label: 'Anthropic' },
]

type ModelRow = { id: string; tier: string; won_per_doc: number }
type ModelCatalog = Record<string, ModelRow[]>

export default function SettingsPage() {
  const { provider, setProvider, setKey, setModel, keyOf, modelOf } = useLLMSettings()
  const [draft, setDraft] = useState(keyOf(provider))
  const [status, setStatus] = useState<string | null>(null)
  const [models, setModels] = useState<ModelCatalog>({})

  useEffect(() => {
    getJson<ModelCatalog>('/api/models').then(setModels).catch(() => setModels({}))
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
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">설정</h1>

      <section>
        <h2 className="mb-2 font-semibold">AI 회사</h2>
        <div className="flex gap-2">
          {PROVIDERS.map((p) => (
            <button
              key={p.id}
              onClick={() => { setProvider(p.id); setDraft(keyOf(p.id)); setStatus(null) }}
              className={`rounded border px-4 py-2 ${provider === p.id ? 'border-black bg-black text-white' : ''}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-semibold">모델 등급</h2>
        <div className="space-y-1">
          {(models[provider] ?? []).map((m) => (
            <label key={m.id} className="flex cursor-pointer items-center gap-3 rounded border px-3 py-2">
              <input
                type="radio"
                name="model"
                checked={modelOf(provider) === m.id}
                onChange={() => setModel(provider, m.id)}
              />
              <span className="w-16 font-medium">{m.tier}</span>
              <span className="flex-1 font-mono text-sm text-gray-600">{m.id}</span>
              <span className="text-sm">약 {m.won_per_doc}원</span>
            </label>
          ))}
        </div>
        <p className="mt-2 text-xs text-gray-500">
          말씀자료 1건당 예상 비용입니다. 회사별로 마지막에 고른 등급을 따로 기억합니다.
        </p>
      </section>

      <section>
        <h2 className="mb-2 font-semibold">API 키</h2>
        <div className="flex gap-2">
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
            className="flex-1 rounded border px-3 py-2"
          />
          <button onClick={test} className="rounded border px-4 py-2">연결 시험</button>
        </div>
        {status && <p className="mt-2 text-sm">{status}</p>}
        <p className="mt-2 text-xs text-gray-500">
          키는 이 브라우저에만 저장되며, 요청 시 헤더로만 전달됩니다.
        </p>
      </section>
    </div>
  )
}
