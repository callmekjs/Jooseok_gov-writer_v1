import { useState } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { ArrowLeft, Sparkles } from 'lucide-react'
import Field, { inputClass } from '../components/Field'
import { ApiError, callApi, postMultipart } from '../lib/api'
import { CUSTOM_CHARS_MAX, CUSTOM_CHARS_MIN, EVENT_TYPES } from '../lib/speech-data'
import { type FormState, initialForm, labelOf, speechFields, toApiPayload } from '../lib/speechFields'
import ResultPanel, { type DraftResult } from './ResultPanel'

// 업로드를 지원하는 확장자. 서버 extractors.files 가 다루는 것 + 안내가 나오는 것(.hwp 등)까지
// 열어 둔다 — 미지원 형식이라도 서버가 예외 없이 경고로 돌려준다.
const UPLOAD_ACCEPT = '.txt,.pdf,.docx,.hwpx,.hwp,.doc,.ppt,.pptx'

export default function WritePage() {
  const [searchParams] = useSearchParams()
  const typeParam = searchParams.get('type')
  // 목록에 없는 값(오타·구버전 링크)이면 무시하고 speechFields 의 기본값(첫 옵션)을 쓴다.
  const initialType = EVENT_TYPES.some((t) => t.key === typeParam) ? (typeParam as string) : undefined

  const [form, setForm] = useState<FormState>(() => {
    const f = initialForm()
    if (initialType) f.event_type = initialType
    return f
  })
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
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50 p-4 sm:p-6">
      <div className="mx-auto max-w-4xl">
        <header className="pt-6 pb-6 sm:pt-8 sm:pb-8">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-blue-600">
            <ArrowLeft className="h-4 w-4" /> 홈으로
          </Link>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">말씀자료 작성</h1>
        </header>

        <div className="relative mb-6 rounded-2xl border-2 border-dashed border-amber-300 bg-amber-50/40 p-5 sm:p-6">
          <span className="absolute -top-2.5 right-3 rounded-md border border-amber-200 bg-amber-50 px-2 py-0.5 text-[10px] font-medium text-amber-800 sm:text-xs">
            자동 작성
          </span>
          <h2 className="mb-2 flex items-center gap-1.5 font-semibold text-slate-900">
            <Sparkles className="h-4 w-4 text-amber-600" />
            행사계획서 파일로 자동 작성
          </h2>
          <p className="mb-3 text-sm text-slate-600">
            행사계획서 파일을 올리면 내용을 읽어 축사 초안을 바로 만듭니다. 아래 항목을 따로 채우지 않아도 됩니다.
          </p>
          <div className="flex flex-wrap items-center gap-2">
            <input
              type="file"
              accept={UPLOAD_ACCEPT}
              onChange={(e) => setPlanFile(e.target.files?.[0] ?? null)}
              className="text-sm text-slate-600"
            />
            <button
              onClick={submitAutoDraft}
              disabled={busy || !planFile}
              className="rounded-xl bg-blue-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
            >
              {busy ? '작성 중...' : '자동 작성'}
            </button>
          </div>
        </div>

        <div className="rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
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
                  className={`-mt-2 mb-4 w-40 ${inputClass}`}
                />
              )}
            </div>
          ))}

          <div className="mb-4">
            <label className="mb-1 block text-sm font-medium text-slate-700">참고자료 첨부 (선택)</label>
            <input
              type="file"
              multiple
              accept={UPLOAD_ACCEPT}
              onChange={(e) => setRefFiles(Array.from(e.target.files ?? []))}
              className="text-sm text-slate-600"
            />
          </div>

          <button
            onClick={submit}
            disabled={busy}
            className="rounded-xl bg-blue-600 px-6 py-3 font-medium text-white shadow-sm transition-colors hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {busy ? '작성 중... (최대 2분)' : '작성'}
          </button>

          {busy && (
            <p className="mt-2 text-sm text-slate-500">
              처음 요청은 서버가 깨어나느라 1분 가까이 걸릴 수 있습니다.
            </p>
          )}

          {error && (
            <div className="mt-4 rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-700">
              {error.message}
              {error.status === 401 && (
                <Link to="/settings" className="ml-2 underline">설정으로 가기</Link>
              )}
            </div>
          )}
        </div>

        {result && <ResultPanel result={result} title={resultTitle} />}

        <footer className="mt-12 text-center text-xs text-slate-400 sm:mt-16">
          말씀자료 작성기
        </footer>
      </div>
    </div>
  )
}
