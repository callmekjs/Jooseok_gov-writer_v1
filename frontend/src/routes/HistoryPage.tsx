import { useEffect, useState } from 'react'
import { getJson } from '../lib/api'

type Row = {
  id: string
  event_type: string
  title: string
  llm_meta: { model?: string; cost_won?: number }
  created_at: string
}

export default function HistoryPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState<{ generated_text: string } | null>(null)

  useEffect(() => {
    getJson<{ drafts: Row[] }>('/api/drafts?limit=20')
      .then((d) => setRows(d.drafts))
      .catch(() => setError('이력을 불러오지 못했습니다. Supabase가 설정되지 않았을 수 있습니다.'))
  }, [])

  if (error) return <p className="text-sm text-gray-600">{error}</p>

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">작성 이력</h1>
      {rows.length === 0 && <p className="text-sm text-gray-600">아직 작성한 문서가 없습니다.</p>}
      <ul className="divide-y">
        {rows.map((r) => (
          <li key={r.id} className="flex cursor-pointer items-center gap-3 py-3"
              onClick={() => getJson<{ generated_text: string }>(`/api/drafts/${r.id}`).then(setOpen)}>
            <span className="w-20 shrink-0 text-sm text-gray-500">{r.event_type}</span>
            <span className="flex-1 truncate">{r.title}</span>
            <span className="shrink-0 text-xs text-gray-500">
              {r.llm_meta?.model} · {r.llm_meta?.cost_won}원
            </span>
            <span className="shrink-0 text-xs text-gray-400">
              {new Date(r.created_at).toLocaleDateString('ko-KR')}
            </span>
          </li>
        ))}
      </ul>
      {open && (
        <article className="mt-6 whitespace-pre-wrap rounded border p-4 leading-relaxed">
          {open.generated_text}
        </article>
      )}
    </div>
  )
}
