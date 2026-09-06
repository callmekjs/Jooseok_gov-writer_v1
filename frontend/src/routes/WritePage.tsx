import { useState } from 'react'
import { Link } from 'react-router-dom'
import Field from '../components/Field'
import { ApiError, callApi, postMultipart } from '../lib/api'
import { CUSTOM_CHARS_MAX, CUSTOM_CHARS_MIN, EVENT_TYPES } from '../lib/speech-data'
import { type FormState, initialForm, labelOf, speechFields, toApiPayload } from '../lib/speechFields'
import ResultPanel, { type DraftResult } from './ResultPanel'

// 업로드를 지원하는 확장자. 서버 extractors.files 가 다루는 것 + 안내가 나오는 것(.hwp 등)까지
// 열어 둔다 — 미지원 형식이라도 서버가 예외 없이 경고로 돌려준다.
const UPLOAD_ACCEPT = '.txt,.pdf,.docx,.hwpx,.hwp,.doc,.ppt,.pptx'

export default function WritePage() {
  const [form, setForm] = useState<FormState>(initialForm)
  const [customChars, setCustomChars] = useState(1500)
  const [refFiles, setRefFiles] = useState<File[]>([])
  const [planFile, setPlanFile] = useState<File | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [result, setResult] = useState<DraftResult | null>(null)
  const [resultTitle, setResultTitle] = useState('')

  const set = (k: string) => (v: string | string[]) => setForm((f) => ({ ...f, [k]: v }))

  async function submitWithFiles(files: File[]) {
    const fd = new FormData()
    fd.append('input_json', JSON.stringify(toApiPayload(form, customChars)))
    files.forEach((f) => fd.append('reference_files', f))
    return postMultipart<DraftResult>('/api/speech/draft-with-docs', fd)
  }

  async function submit() {
    setError(null)
    setResult(null)
    if (!(form.event_name as string).trim()) {
      setError({ status: 400, message: '행사명은 필수입니다.' })
      return
    }
    setBusy(true)
    try {
      const data = refFiles.length > 0
        ? await submitWithFiles(refFiles)
        : await callApi<DraftResult>('/api/speech/draft', { input: toApiPayload(form, customChars) })
      setResultTitle(`${form.event_name}_${labelOf(EVENT_TYPES, form.event_type as string)}`)
      setResult(data)
    } catch (e) {
      const err = e as ApiError
      setError({ status: err.status, message: err.message })
    } finally {
      setBusy(false)
    }
  }

  async function submitAutoDraft() {
    if (!planFile) return
    setError(null)
    setResult(null)
    setBusy(true)
    try {
      const fd = new FormData()
      fd.append('plan_file', planFile)
      const data = await postMultipart<DraftResult>('/api/speech/auto-draft', fd)
      setResultTitle(`${planFile.name.replace(/\.[^/.]+$/, '')}_축사`)
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

      <div className="mb-8 rounded border border-dashed p-4">
        <h2 className="mb-2 font-semibold">행사계획서 파일로 자동 작성</h2>
        <p className="mb-3 text-sm text-gray-500">
          행사계획서 파일을 올리면 내용을 읽어 축사 초안을 바로 만듭니다. 아래 항목을 따로 채우지 않아도 됩니다.
        </p>
        <div className="flex items-center gap-2">
          <input
            type="file"
            accept={UPLOAD_ACCEPT}
            onChange={(e) => setPlanFile(e.target.files?.[0] ?? null)}
          />
          <button
            onClick={submitAutoDraft}
            disabled={busy || !planFile}
            className="rounded bg-black px-4 py-2 text-sm text-white disabled:opacity-50"
          >
            {busy ? '작성 중...' : '자동 작성'}
          </button>
        </div>
      </div>

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

      <div className="mb-4">
        <label className="mb-1 block text-sm font-medium">참고자료 첨부 (선택)</label>
        <input
          type="file"
          multiple
          accept={UPLOAD_ACCEPT}
          onChange={(e) => setRefFiles(Array.from(e.target.files ?? []))}
        />
      </div>

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

      {result && <ResultPanel result={result} title={resultTitle} />}
    </div>
  )
}
