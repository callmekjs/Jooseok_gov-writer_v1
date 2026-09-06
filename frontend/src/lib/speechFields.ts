import { AUDIENCES, CUSTOM_CHARS_MAX, CUSTOM_CHARS_MIN, EVENT_TYPES, LENGTHS, SPEAKER_ROLES } from './speech-data'

export type FieldType = 'text' | 'textarea' | 'select' | 'multiselect' | 'list'

export type FieldSpec = {
  key: string
  label: string
  type: FieldType
  required?: boolean
  options?: readonly { key: string; label: string }[]
  placeholder?: string
}

/** SpeechInput 14칸과 1:1. 이 배열이 화면의 전부다. */
export const speechFields: FieldSpec[] = [
  { key: 'event_name', label: '행사명', type: 'text', required: true, placeholder: '청년 주거지원 정책 설명회' },
  { key: 'event_type', label: '행사 유형', type: 'select', options: EVENT_TYPES },
  { key: 'event_date', label: '일시', type: 'text', placeholder: '2026년 9월 12일 14시' },
  { key: 'event_location', label: '장소', type: 'text', placeholder: '정부세종청사 대강당' },
  { key: 'speaker_name', label: '이름', type: 'text' },
  { key: 'speaker_role', label: '직급', type: 'select', options: SPEAKER_ROLES },
  { key: 'speaker_organization', label: '소속 기관', type: 'text' },
  { key: 'audience', label: '청중', type: 'multiselect', options: AUDIENCES },
  { key: 'target_chars', label: '분량', type: 'select', options: LENGTHS },
  { key: 'key_messages', label: '핵심 메시지', type: 'list' },
  { key: 'quotes_or_anecdotes', label: '인용할 통계·일화', type: 'list' },
  { key: 'avoid_phrases', label: '피할 표현', type: 'list' },
  { key: 'vip_list', label: '주요 참석자', type: 'list' },
  { key: 'persona_block', label: '페르소나(선택)', type: 'textarea', placeholder: '자주 쓰는 표현이나 말투를 적으세요' },
]

export type FormState = Record<string, string | string[]>

export function initialForm(): FormState {
  const s: FormState = {}
  for (const f of speechFields) {
    if (f.type === 'list' || f.type === 'multiselect') s[f.key] = []
    else if (f.type === 'select') s[f.key] = f.options![0].key
    else s[f.key] = ''
  }
  s.target_chars = 'standard'
  return s
}

/** 사용자 지정 분량을 허용 범위로 강제한다.
 *  제출이 form submit 이 아니라 onClick 이라 input 의 min/max 는 강제되지 않는다. */
export function clampCustomChars(n: number): number {
  if (!Number.isFinite(n)) return 1500
  return Math.min(CUSTOM_CHARS_MAX, Math.max(CUSTOM_CHARS_MIN, Math.round(n)))
}

/** ★ 화면은 키를 쓰고, API 로는 한글 라벨을 보낸다. */
export function toApiPayload(form: FormState, customChars: number) {
  const labelOf = (opts: readonly { key: string; label: string }[], key: string) =>
    opts.find((o) => o.key === key)?.label ?? key

  const cleanList = (v: unknown) => (v as string[]).map((s) => s.trim()).filter(Boolean)

  const lengthKey = form.target_chars as string
  const chars =
    lengthKey === 'custom'
      ? clampCustomChars(customChars)
      : LENGTHS.find((l) => l.key === lengthKey)!.chars

  return {
    event_name: form.event_name as string,
    event_type: labelOf(EVENT_TYPES, form.event_type as string),
    event_date: form.event_date as string,
    event_location: form.event_location as string,
    speaker_name: form.speaker_name as string,
    speaker_role: labelOf(SPEAKER_ROLES, form.speaker_role as string),
    speaker_organization: form.speaker_organization as string,
    audience: (form.audience as string[]).map((k) => labelOf(AUDIENCES, k)).join(', '),
    vip_list: cleanList(form.vip_list),
    target_chars: chars,
    key_messages: cleanList(form.key_messages),
    quotes_or_anecdotes: cleanList(form.quotes_or_anecdotes),
    avoid_phrases: cleanList(form.avoid_phrases),
    persona_block: form.persona_block as string,
  }
}
