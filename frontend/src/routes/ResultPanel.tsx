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

export default function ResultPanel({ result }: { result: DraftResult }) {
  const { meta } = result
  return (
    <div className="mt-8 rounded border">
      <div className="border-b bg-gray-50 px-4 py-2 text-sm text-gray-700">
        {result.char_count.toLocaleString()}자 · {meta.model} ·{' '}
        {(meta.elapsed_ms / 1000).toFixed(1)}초 · 약 {meta.cost_won}원
      </div>

      {result.warnings.map((w, i) => (
        <div key={i} className="border-b bg-yellow-50 px-4 py-2 text-sm">{w}</div>
      ))}
      {result.save_warning && (
        <div className="border-b bg-gray-100 px-4 py-2 text-sm">{result.save_warning}</div>
      )}

      <article className="whitespace-pre-wrap px-4 py-4 leading-relaxed">
        {result.generated_text}
      </article>
    </div>
  )
}
