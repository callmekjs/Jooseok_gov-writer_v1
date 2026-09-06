import { useCallback, useState } from 'react'

export type Provider = 'openai' | 'anthropic'

const K = {
  provider: 'gw_llm_provider',
  key: (p: Provider) => `gw_llm_key_${p}`,
  model: (p: Provider) => `gw_llm_model_${p}`,
}

// 화면 초기 선택값 — 서버의 catalog.DEFAULTS 와는 다른 개념이다.
// 인턴 등급은 목표를 올려도 700~1,000자에서 멈추므로 선임비서를 기본으로 둔다.
const INITIAL_MODEL: Record<Provider, string> = {
  openai: 'gpt-5.6-sol',
  anthropic: 'claude-sonnet-4-5-20250929',
}

export const KEY_PATTERN: Record<Provider, RegExp> = {
  openai: /^sk-/,
  anthropic: /^sk-ant-/,     // ⚠️ 하나의 정규식으로 합치지 말 것
}

function read(k: string, fallback = '') {
  return localStorage.getItem(k) ?? fallback
}

export function useLLMSettings() {
  const [provider, setProviderState] = useState<Provider>(
    (read(K.provider, 'openai') as Provider) || 'openai',    // G4
  )
  const [, force] = useState(0)

  const setProvider = useCallback((p: Provider) => {
    localStorage.setItem(K.provider, p)
    setProviderState(p)
  }, [])

  const setKey = useCallback((p: Provider, v: string) => {
    localStorage.setItem(K.key(p), v)
    force((n) => n + 1)
  }, [])

  const setModel = useCallback((p: Provider, v: string) => {
    localStorage.setItem(K.model(p), v)
    force((n) => n + 1)
  }, [])

  const clearAll = useCallback(() => {
    ;['openai', 'anthropic'].forEach((p) => {
      localStorage.removeItem(K.key(p as Provider))
      localStorage.removeItem(K.model(p as Provider))
    })
    localStorage.removeItem(K.provider)
    localStorage.removeItem('gw_llm_key_gemini')   // 옛 키 청소
    force((n) => n + 1)
  }, [])

  return {
    provider,
    setProvider,
    setKey,
    setModel,
    clearAll,
    keyOf: (p: Provider) => read(K.key(p)),
    modelOf: (p: Provider) => read(K.model(p), INITIAL_MODEL[p]),
  }
}

/** 현재 설정 스냅샷 — 컴포넌트 밖(api.ts)에서 쓴다. */
export function getLLMSettings() {
  const provider = (read(K.provider, 'openai') as Provider) || 'openai'
  return {
    provider,
    model: read(K.model(provider), INITIAL_MODEL[provider]),
    key: read(K.key(provider)),
  }
}
