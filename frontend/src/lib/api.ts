import { getLLMSettings } from '../hooks/useLLMSettings'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

/** 모든 AI 요청의 단일 창구. provider·model·key 세 헤더를 여기서만 붙인다. */
export async function callApi<T>(path: string, body: unknown): Promise<T> {
  const { provider, model, key } = getLLMSettings()
  if (!key) throw new ApiError(401, '설정에서 API 키를 먼저 입력해 주세요.')

  const res = await fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-LLM-Provider': provider,
      'X-LLM-Model': model,
      [provider === 'openai' ? 'X-OpenAI-Key' : 'X-Anthropic-Key']: key,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new ApiError(res.status, detail.detail ?? '요청에 실패했습니다.')
  }
  return res.json()
}

export async function getJson<T>(path: string): Promise<T> {
  const res = await fetch(path)
  if (!res.ok) throw new ApiError(res.status, '요청에 실패했습니다.')
  return res.json()
}
