import { getLLMSettings } from '../hooks/useLLMSettings'

export class ApiError extends Error {
  status: number
  constructor(status: number, message: string) {
    super(message)
    this.status = status
  }
}

const TIMEOUT_MS = 130_000   // 서버 타임아웃 120초보다 길게 — 504를 사용자가 받도록

/** 접속 암호 게이트(AuthGate.tsx)가 저장하는 localStorage 키. 한 곳에서만 적는다. */
export const APP_PASSWORD_STORAGE_KEY = 'gw_app_password'

function readAppPassword(): string {
  return localStorage.getItem(APP_PASSWORD_STORAGE_KEY) ?? ''
}

/** LLM 키 헤더 — 값이 있을 때만 붙인다. 비우면(서버 폴백) 서버 자신의 키를 쓴다. */
function llmKeyHeader(provider: string, key: string): Record<string, string> {
  return key ? { [provider === 'openai' ? 'X-OpenAI-Key' : 'X-Anthropic-Key']: key } : {}
}

async function fetchWithTimeout(path: string, init: RequestInit): Promise<Response> {
  const ac = new AbortController()
  const timer = setTimeout(() => ac.abort(), TIMEOUT_MS)
  try {
    return await fetch(path, { ...init, signal: ac.signal })
  } catch (e) {
    if ((e as Error).name === 'AbortError') {
      throw new ApiError(504, '시간이 초과되었습니다. 분량을 줄이거나 다시 시도해 주세요.')
    }
    throw new ApiError(0, '서버에 연결하지 못했습니다. 잠시 후 다시 시도해 주세요.')
  } finally {
    clearTimeout(timer)
  }
}

/** 모든 AI 요청의 단일 창구. provider·model·key·접속암호 헤더를 여기서만 붙인다. */
export async function callApi<T>(path: string, body: unknown): Promise<T> {
  const { provider, model, key } = getLLMSettings()

  const res = await fetchWithTimeout(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-LLM-Provider': provider,
      'X-LLM-Model': model,
      'X-App-Password': readAppPassword(),
      ...llmKeyHeader(provider, key),
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
  const res = await fetchWithTimeout(path, {
    headers: { 'X-App-Password': readAppPassword() },
  })
  if (!res.ok) throw new ApiError(res.status, '요청에 실패했습니다.')
  return res.json()
}

/** 파일 업로드 전용 창구. Content-Type 을 직접 지정하지 않는다 — FormData 를 넘기면
 *  브라우저가 boundary 까지 붙인 Content-Type 을 자동으로 설정한다. */
export async function postMultipart<T>(path: string, formData: FormData): Promise<T> {
  const { provider, model, key } = getLLMSettings()

  const res = await fetchWithTimeout(path, {
    method: 'POST',
    headers: {
      'X-LLM-Provider': provider,
      'X-LLM-Model': model,
      'X-App-Password': readAppPassword(),
      ...llmKeyHeader(provider, key),
    },
    body: formData,
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new ApiError(res.status, detail.detail ?? '요청에 실패했습니다.')
  }
  return res.json()
}
