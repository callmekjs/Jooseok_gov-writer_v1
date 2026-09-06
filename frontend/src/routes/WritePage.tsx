import { useState } from 'react'
import { Link } from 'react-router-dom'
import Field from '../components/Field'
import { ApiError, callApi } from '../lib/api'
import { CUSTOM_CHARS_MAX, CUSTOM_CHARS_MIN, EVENT_TYPES } from '../lib/speech-data'
import { type FormState, initialForm, labelOf, speechFields, toApiPayload } from '../lib/speechFields'
import ResultPanel, { type DraftResult } from './ResultPanel'

export default function WritePage() {
  const [form, setForm] = useState<FormState>(initialForm)
  const [customChars, setCustomChars] = useState(1500)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [result, setResult] = useState<DraftResult | null>(null)

  const set = (k: string) => (v: string | string[]) => setForm((f) => ({ ...f, [k]: v }))

  async function submit() {
    setError(null)
    setResult(null)
    if (!(form.event_name as string).trim()) {
      setError({ status: 400, message: '행사명은 필수입니다.' })
      return
    }
    setBusy(true)
    try {
      const data = await callApi<DraftResult>('/api/speech/draft', {
        input: toApiPayload(form, customChars),
      })
      setResult(data)
    } catch (e) {
      const err = e as ApiError
      setError({ status: err.status, message: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">말씀자료 작성</h1>

      {speechFields.map((spec) => (
        <div key={spec.key}>
          <Field spec={spec} value={form[spec.key]} onChange={set(spec.key)} />
          {spec.key === 'target_chars' && form.target_chars === 'custom' && (
            <input
              type="number"
              min={CUSTOM_CHARS_MIN}
              max={CUSTOM_CHARS_MAX}
              value={customChars}
              onChange={(e) => setCustomChars(Number(e.target.value))}
              className="-mt-2 mb-4 w-40 rounded border px-3 py-2"
            />
          )}
        </div>
      ))}

      <button
        onClick={submit}
        disabled={busy}
        className="rounded bg-black px-6 py-3 text-white disabled:opacity-50"
      >
        {busy ? '작성 중... (최대 2분)' : '작성'}
      </button>

      {busy && (
        <p className="mt-2 text-sm text-gray-500">
          처음 요청은 서버가 깨어나느라 1분 가까이 걸릴 수 있습니다.
        </p>
      )}

      {error && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm">
          {error.message}
          {error.status === 401 && (
            <Link to="/settings" className="ml-2 underline">설정으로 가기</Link>
          )}
        </div>
      )}

      {result && (
        <ResultPanel
          result={result}
          title={`${form.event_name}_${labelOf(EVENT_TYPES, form.event_type as string)}`}
        />
      )}
    </div>
  )
}
