import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { ArrowLeft, FileText, X } from 'lucide-react'
import { getJson } from '../lib/api'

type Row = {
  id: string
  event_type: string
  title: string
  llm_meta: { model?: string; cost_won?: number }
  created_at: string
}

type ListStatus = 'loading' | 'error' | 'empty' | 'ready'

const INFO_BOX = 'rounded-2xl border border-slate-200 bg-white p-6 text-sm'

export default function HistoryPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [status, setStatus] = useState<ListStatus>('loading')

  const [openId, setOpenId] = useState<string | null>(null)
  const [detail, setDetail] = useState<{ generated_text: string } | null>(null)
  const [detailError, setDetailError] = useState<string | null>(null)

  useEffect(() => {
    getJson<{ drafts: Row[] }>('/api/drafts?limit=20')
      .then((d) => {
        setRows(d.drafts)
        setStatus(d.drafts.length === 0 ? 'empty' : 'ready')
      })
      .catch(() => setStatus('error'))
  }, [])

  // 상세 조회는 실패해도 화면이 그대로 멈추지 않도록 반드시 .catch 로 사용자에게 알린다.
  function openDraft(id: string) {
    setOpenId(id)
    setDetail(null)
    setDetailError(null)
    getJson<{ generated_text: string }>(`/api/drafts/${id}`)
      .then(setDetail)
      .catch(() => setDetailError('이 문서를 불러오지 못했습니다. 잠시 후 다시 시도해 주세요.'))
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50 p-4 sm:p-6">
      <div className="mx-auto max-w-4xl">
        <header className="pt-6 pb-6 sm:pt-8 sm:pb-8">
          <Link to="/" className="inline-flex items-center gap-1 text-sm text-slate-500 transition-colors hover:text-blue-600">
            <ArrowLeft className="h-4 w-4" /> 홈으로
          </Link>
          <h1 className="mt-3 text-2xl font-bold text-slate-900">작성 이력</h1>
          <p className="mt-1 text-sm text-slate-600">최근 20건까지 보여줍니다.</p>
        </header>

        {status === 'loading' && <div className={`${INFO_BOX} text-slate-500`}>불러오는 중입니다...</div>}

        {status === 'error' && (
          <div className={`${INFO_BOX} text-red-600`}>
            이력을 불러오지 못했습니다. Supabase가 설정되지 않았을 수 있습니다.
          </div>
        )}

        {status === 'empty' && <div className={`${INFO_BOX} text-slate-500`}>아직 작성한 문서가 없습니다.</div>}

        {status === 'ready' && (
          <ul className="divide-y divide-slate-100 overflow-hidden rounded-2xl border border-slate-200 bg-white">
            {rows.map((r) => (
              <li key={r.id}>
                <button
                  type="button"
                  onClick={() => openDraft(r.id)}
                  className="flex w-full flex-col gap-1 px-4 py-3 text-left transition-colors hover:bg-blue-50/60 sm:flex-row sm:items-center sm:gap-3 sm:px-5"
                >
                  <span className="flex min-w-0 items-center gap-2">
                    <span className="shrink-0 rounded-lg bg-blue-50 p-1.5">
                      <FileText className="h-4 w-4 text-blue-600" />
                    </span>
                    <span className="w-14 shrink-0 text-xs text-slate-500 sm:w-20 sm:text-sm">{r.event_type}</span>
                    <span className="min-w-0 flex-1 truncate text-sm text-slate-900">{r.title}</span>
                  </span>
                  <span className="flex items-center justify-between gap-3 pl-9 text-xs text-slate-500 sm:justify-end sm:pl-0">
                    <span>{r.llm_meta?.model ?? '-'} · {r.llm_meta?.cost_won ?? 0}원</span>
                    <span className="text-slate-400">{new Date(r.created_at).toLocaleDateString('ko-KR')}</span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}

        {openId && (
          <article className="mt-6 rounded-2xl border border-slate-200 bg-white p-5 sm:p-6">
            <div className="mb-3 flex items-center justify-end">
              <button
                type="button"
                onClick={() => setOpenId(null)}
                className="flex items-center gap-1 text-xs text-slate-400 transition-colors hover:text-slate-600"
              >
                <X className="h-3.5 w-3.5" /> 닫기
              </button>
            </div>
            {detail && (
              <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-800">{detail.generated_text}</p>
            )}
            {!detail && !detailError && <p className="text-sm text-slate-500">불러오는 중입니다...</p>}
            {detailError && <p className="text-sm text-red-600">{detailError}</p>}
          </article>
        )}

        <footer className="mt-12 text-center text-xs text-slate-400 sm:mt-16">
          말씀자료 작성기
        </footer>
      </div>
    </div>
  )
}
