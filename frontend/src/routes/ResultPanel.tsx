export type DraftMeta = {
  provider: string
  model: string
  elapsed_ms: number
  input_tokens: number
  output_tokens: number
  cost_won: number
}

export type DraftResult = {
  generated_text: string
  char_count: number
  draft_id: string | null
  warnings: string[]
  save_warning: string | null
  meta: DraftMeta
}

async function download(kind: 'md' | 'hwpx', title: string, text: string) {
  const res = await fetch(`/api/download/speech/${kind}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, generated_text: text }),
  })
  if (!res.ok) { alert('다운로드에 실패했습니다.'); return }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}.${kind}`
  a.click()
  URL.revokeObjectURL(url)
}

const ACTION_BUTTON =
  'rounded-xl border border-slate-200 px-4 py-2 text-sm text-slate-700 transition-colors hover:border-blue-300 hover:bg-blue-50'

export default function ResultPanel({
  result,
  title,
}: {
  result: DraftResult
  title: string
}) {
  const { meta } = result
  return (
    <div className="mt-8 overflow-hidden rounded-2xl border border-slate-200 bg-white">
      <div className="border-b border-slate-200 bg-slate-50 px-4 py-2.5 text-sm text-slate-600">
        {result.char_count.toLocaleString()}자 · {meta.model} ·{' '}
        {(meta.elapsed_ms / 1000).toFixed(1)}초 · 약 {meta.cost_won}원
      </div>

      {result.warnings.map((w, i) => (
        <div key={i} className="border-b border-slate-200 bg-amber-50 px-4 py-2 text-sm text-amber-800">{w}</div>
      ))}
      {result.save_warning && (
        <div className="border-b border-slate-200 bg-slate-50 px-4 py-2 text-sm text-slate-600">{result.save_warning}</div>
      )}

      <article className="whitespace-pre-wrap px-4 py-4 leading-relaxed text-slate-800">
        {result.generated_text}
      </article>

      <div className="flex flex-wrap gap-2 border-t border-slate-200 px-4 py-3">
        <button onClick={() => download('md', title, result.generated_text)}
                className={ACTION_BUTTON}>마크다운 받기</button>
        <button onClick={() => download('hwpx', title, result.generated_text)}
                className={ACTION_BUTTON}>한글파일 받기</button>
        <button onClick={() => navigator.clipboard.writeText(result.generated_text)}
                className={ACTION_BUTTON}>복사</button>
      </div>
    </div>
  )
}
