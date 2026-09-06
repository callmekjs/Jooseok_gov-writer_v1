import { useState } from 'react'
import type { FieldSpec } from '../lib/speechFields'

type Props = {
  spec: FieldSpec
  value: string | string[]
  onChange: (v: string | string[]) => void
}

/** 텍스트류 입력 공통 클래스. WritePage 의 분량 직접입력 칸도 같은 스타일을 쓴다. */
export const inputClass =
  'rounded-xl border border-slate-200 px-3 py-2 text-sm text-slate-900 placeholder:text-slate-400 transition-colors focus:border-blue-400 focus:outline-none focus:ring-2 focus:ring-blue-500/40'

function nextId() {
  return typeof crypto !== 'undefined' && typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2)
}

export default function Field({ spec, value, onChange }: Props) {
  // list 항목의 안정적인 key. key={i} 를 쓰면 중간 항목을 지웠을 때
  // React 가 뒤 항목의 DOM 을 재사용해 표시값이 한 칸씩 밀린다.
  // id 목록은 "+ 추가"·"−" 두 이벤트 핸들러 안에서만 늘리고 줄인다 — 렌더 중에는
  // 절대 읽거나 쓰지 않는다 (렌더 중 ref 읽기/쓰기와 Math.random 호출은 impure 하다).
  const [ids, setIds] = useState<string[]>([])

  const label = (
    <label className="mb-1 block text-sm font-medium text-slate-700">
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
          className={`w-full ${inputClass}`}
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
          className={`w-full ${inputClass}`}
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
                className={`rounded-full border px-3 py-1 text-sm transition-colors ${
                  on
                    ? 'border-blue-500 bg-blue-50 text-blue-700'
                    : 'border-slate-200 text-slate-600 hover:border-slate-300'
                }`}
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

    const removeAt = (i: number) => {
      setIds((prev) => prev.filter((_, j) => j !== i))
      onChange(items.filter((_, j) => j !== i))
    }

    const add = () => {
      setIds((prev) => [...prev, nextId()])
      onChange([...items, ''])
    }

    return (
      <div className="mb-4">
        {label}
        {items.map((item, i) => (
          <div key={ids[i] ?? i} className="mb-1 flex gap-2">
            <input
              type="text"
              value={item}
              onChange={(e) => onChange(items.map((x, j) => (j === i ? e.target.value : x)))}
              className={`flex-1 ${inputClass}`}
            />
            <button
              type="button"
              onClick={() => removeAt(i)}
              className="rounded-xl border border-slate-200 px-3 text-slate-500 transition-colors hover:border-red-300 hover:text-red-600"
            >
              −
            </button>
          </div>
        ))}
        <button
          type="button"
          onClick={add}
          className="rounded-xl border border-slate-200 px-3 py-1.5 text-sm text-blue-600 transition-colors hover:border-blue-300 hover:bg-blue-50"
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
        type="text"
        value={value as string}
        placeholder={spec.placeholder}
        onChange={(e) => onChange(e.target.value)}
        className={`w-full ${inputClass}`}
      />
    </div>
  )
}
