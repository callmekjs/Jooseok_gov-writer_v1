import { useRef } from 'react'
import type { FieldSpec } from '../lib/speechFields'

type Props = {
  spec: FieldSpec
  value: string | string[]
  onChange: (v: string | string[]) => void
}

export default function Field({ spec, value, onChange }: Props) {
  // list 항목의 안정적인 key. key={i} 를 쓰면 중간 항목을 지웠을 때
  // React 가 뒤 항목의 DOM 을 재사용해 표시값이 한 칸씩 밀린다.
  const idsRef = useRef<string[]>([])

  const nextId = () =>
    typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
      ? crypto.randomUUID()
      : Math.random().toString(36).slice(2)

  const label = (
    <label className="mb-1 block text-sm font-medium">
      {spec.label}
      {spec.required && <span className="ml-1 text-red-600">*</span>}
    </label>
  )

  if (spec.type === 'textarea') {
    return (
      <div className="mb-4">
        {label}
        <textarea
          value={value as string}
          placeholder={spec.placeholder}
          onChange={(e) => onChange(e.target.value)}
          rows={3}
          className="w-full rounded border px-3 py-2"
        />
      </div>
    )
  }

  if (spec.type === 'select') {
    return (
      <div className="mb-4">
        {label}
        <select
          value={value as string}
          onChange={(e) => onChange(e.target.value)}
          className="w-full rounded border px-3 py-2"
        >
          {spec.options!.map((o) => (
            <option key={o.key} value={o.key}>{o.label}</option>
          ))}
        </select>
      </div>
    )
  }

  if (spec.type === 'multiselect') {
    const picked = value as string[]
    return (
      <div className="mb-4">
        {label}
        <div className="flex flex-wrap gap-2">
          {spec.options!.map((o) => {
            const on = picked.includes(o.key)
            return (
              <button
                key={o.key}
                type="button"
                onClick={() => onChange(on ? picked.filter((k) => k !== o.key) : [...picked, o.key])}
                className={`rounded-full border px-3 py-1 text-sm ${on ? 'border-black bg-black text-white' : ''}`}
              >
                {o.label}
              </button>
            )
          })}
        </div>
      </div>
    )
  }

  if (spec.type === 'list') {
    const items = value as string[]

    // 항목 수에 맞춰 id 목록을 늘리거나 줄인다
    while (idsRef.current.length < items.length) idsRef.current.push(nextId())
    if (idsRef.current.length > items.length) idsRef.current.length = items.length

    const removeAt = (i: number) => {
      idsRef.current.splice(i, 1)
      onChange(items.filter((_, j) => j !== i))
    }

    return (
      <div className="mb-4">
        {label}
        {items.map((item, i) => (
          <div key={idsRef.current[i]} className="mb-1 flex gap-2">
            <input
              value={item}
              onChange={(e) => onChange(items.map((x, j) => (j === i ? e.target.value : x)))}
              className="flex-1 rounded border px-3 py-2"
            />
            <button type="button" onClick={() => removeAt(i)} className="rounded border px-3">
              −
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={() => onChange([...items, ''])}
          className="rounded border px-3 py-1 text-sm"
        >
          + 추가
        </button>
      </div>
    )
  }

  return (
    <div className="mb-4">
      {label}
      <input
        value={value as string}
        placeholder={spec.placeholder}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded border px-3 py-2"
      />
    </div>
  )
}
