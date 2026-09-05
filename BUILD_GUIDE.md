# 말씀자료 작성기 — 파트별 구축 설계서

> **한 줄 정의**
> 행사 정보를 폼에 넣으면 AI가 부처 6단 기틀에 맞춰 말씀자료를 쓰고, 마크다운·한글파일(hwpx)로 내려받는 웹앱.

이 문서는 `jooseok_project_v2.md`(원본 앱 분석 + 설계 결정)를 **실제로 만들 수 있는 순서와 코드 단위로 풀어 쓴 것**이다.
README를 쓸 때 이 문서의 목차와 표를 그대로 옮겨 쓸 수 있도록, 파트마다 같은 형식을 지켰다.

각 파트는 **① 이 파트가 하는 일 → ② 만들 파일 → ③ 어떻게 만드나 → ④ 완료 확인 → ⑤ 이 파트의 함정** 순서다.

---

## 목차

| # | 파트 | 한 줄 요약 |
|---|---|---|
| 0 | [한 장 요약](#0-한-장-요약) | 전체를 한 화면에 |
| 1 | [전체 구조](#1-전체-구조--다섯-덩어리가-어떻게-맞물리나) | 다섯 덩어리의 관계 |
| 2 | [요청 하나의 일생](#2-요청-하나의-일생) | 버튼을 누르면 무슨 일이 일어나나 |
| 3 | [**AI 파트**](#3-ai-파트--이-앱의-머리) | 모델 선택 + 프롬프트 5층 |
| 4 | [**백엔드 파트**](#4-백엔드-파트--fastapi) | FastAPI 방 배치 |
| 5 | [**프론트엔드 파트**](#5-프론트엔드-파트--react) | 화면 4개, 폼을 데이터로 |
| 6 | [**DB 파트**](#6-db-파트--supabase) | 표 1개, 없어도 동작 |
| 7 | [**네트워크 파트**](#7-네트워크-파트) | 포트·헤더·CORS·라우팅 |
| 8 | [파일 입출력 파트](#8-파일-입출력-파트) | 읽기 4종 / 쓰기 2종 |
| 9 | [보안 파트](#9-보안-파트) | 키를 절대 흘리지 않기 |
| 10 | [배포·운영 파트](#10-배포운영-파트) | Render에 올리기 |
| 11 | [만드는 순서](#11-만드는-순서--14단계--31시간) | 14단계 / 31시간 |
| 12 | [함정 20개](#12-함정-20개-요약표) | 안 보면 반드시 막히는 것 |
| 13 | [로컬 실행법](#13-로컬-실행법-윈도우) | 처음 켜는 법 |
| 14 | [완료 판정](#14-완료-판정-체크리스트) | 다 됐다고 말할 수 있는 기준 |

---

## 0. 한 장 요약

### 만드는 것

```
문서 계열 : 말씀자료 1종
문서 유형 : 8개 (축사·기념사·신년사·격려사·환영사·개회사·이임사·서면축사)
기틀      : 6단 (서면축사만 4단) — 유형 8개가 같은 기틀을 공유한다
화면      : 4개 (/ , /write , /history , /settings)
API       : 11개
모델      : 5개 (OpenAI 3등급 + Anthropic 2등급)
외부 서비스: 4곳 (AI 회사 · GitHub · Render · Supabase)
```

### 안 만드는 것 — 그리고 왜

| 안 만듦 | 이유 |
|---|---|
| 보도자료 · 설명자료 | 문서 계열을 늘리면 프롬프트 L1~L3을 통째로 새로 써야 한다 (+5시간) |
| RAG · 공공데이터 연동 | 외부 서비스 2곳이 추가로 붙는다. 승인 대기 시간도 예측 불가 |
| 페르소나 저장소 (`/personas`) | 없어도 글은 나온다. **단, 폼의 `persona_block` 입력칸은 남긴다** |
| 단락 재생성 · 말투 조정 | 있으면 좋지만 없어도 완결된 앱이다 |
| Google Gemini | 2사만 쓴다. 빼면 함정 3개가 같이 사라진다 (7.4절) |

> **확장 대비 한 가지만 해 둔다**: 프롬프트 조립 함수 이름을 `build_speech_prompt`로 둔다.
> 나중에 보도자료를 붙일 때 옆에 `build_press_prompt`를 만들기만 하면 된다. 지금 드는 추가 비용은 **0시간**.

### 기술 스택

| 층 | 무엇 | 왜 이걸 골랐나 |
|---|---|---|
| 화면 | React + TypeScript + Vite + Tailwind + lucide-react + react-router-dom | Vite는 빌드가 빠르고, 결과물을 FastAPI가 그대로 서빙할 수 있다 |
| 서버 | Python 3.10+ / FastAPI / uvicorn | 타입 검증(Pydantic)이 공짜로 따라온다. 400 응답을 직접 안 짜도 된다 |
| AI | OpenAI 3등급 + Anthropic 2등급 = 5개 모델 | 두 회사면 한쪽 장애 시 대체 가능. 등급은 비용 32배 차이를 보여주기 위함 |
| DB | Supabase (PostgreSQL) | 무료 티어 + REST API 제공. SDK 없이 httpx로 직접 친다 |
| 파일 읽기 | pypdf, python-docx, hwpx(ZIP 파싱) | 행사계획서가 이 세 형식으로 온다 |
| 파일 쓰기 | markdown, python-hwpx | 공무원이 최종적으로 원하는 건 한글파일이다 |
| 실행(윈도우) | `run.ps1` — 백엔드 **8010**, 프론트 5173 | 8000번은 이 PC에서 다른 프로그램이 잡고 있다 |
| 배포 | Render | GitHub 연결 후 push만 하면 갱신된다 |

---

## 1. 전체 구조 — 다섯 덩어리가 어떻게 맞물리나

```
┌─────────────────────────────────────────────────────────────────┐
│  ① 프론트엔드 (React, :5173)                                     │
│     홈 · 작성폼 · 결과 · 이력 · 설정                              │
│     localStorage 에 회사/모델/키를 기억                           │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ② 네트워크
                           │   헤더 3개: X-LLM-Provider / X-LLM-Model / X-{회사}-Key
                           │   개발: Vite 프록시 → :8010
                           │   배포: 같은 도메인 (/api/*)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  ③ 백엔드 (FastAPI, :8010)                                       │
│     server.py 가 라우터 4개를 꽂는다                              │
│     ┌───────────────────────────────────────────────────┐        │
│     │  ④ AI 파트                                         │        │
│     │    catalog.resolve()  ← 모델 허용목록 검증          │        │
│     │    build_speech_prompt()  ← 프롬프트 5층 조립       │        │
│     │    call_llm()  ← 회사별 요청 모양 분기              │────────┼──→ OpenAI
│     └───────────────────────────────────────────────────┘        │    Anthropic
│     common/ 에 공통 함수 1벌씩 (키/파싱/품질검사)                  │
└──────────────────────────┬──────────────────────────────────────┘
                           │ ⑤ DB (선택)
                           ▼
┌─────────────────────────────────────────────────────────────────┐
│  Supabase PostgreSQL — 표 1개 (drafts)                           │
│  없어도 글은 나온다. 이력만 안 남는다.                             │
└─────────────────────────────────────────────────────────────────┘
```

### 의존 방향 — 한쪽으로만 흐른다

```
프론트엔드 ──→ 백엔드 ──→ AI 회사
                 └──→ DB (실패해도 무시)
```

- **프론트엔드는 AI 회사를 직접 부르지 않는다.** 키가 브라우저 코드에 박히면 안 되기 때문이 아니라 (어차피 사용자 본인 키다), **모델 허용목록 검증을 서버가 해야** 하기 때문이다.
- **DB는 곁가지다.** 저장이 실패해도 글은 사용자에게 돌려준다. 대신 `save_warning`으로 알려준다.

### 폴더 전체

```
policy_writer/
├── run.ps1                      윈도우에서 서버+화면 같이 켜기
├── .env  /  .env.example
├── .gitignore                   ★ 첫 커밋 전에 반드시
├── pyproject.toml
├── README.md
├── BUILD_GUIDE.md               이 문서
├── frontend/                    ⑤ 프론트엔드 파트
├── src/policy_writer/           ③④ 백엔드 + AI 파트
├── supabase/migrations/         ⑥ DB 파트
└── static/                      Vite 빌드 결과 (깃 무시)
```

---

## 2. 요청 하나의 일생

**"작성" 버튼을 한 번 누르면 벌어지는 일 전부.** 이 13단계를 머리에 넣고 나면 나머지 파트는 각자 자기 자리를 찾는다.

| # | 어디서 | 무슨 일 | 실패하면 |
|---|---|---|---|
| 1 | 브라우저 | 폼 값을 `SpeechInput` 모양 JSON으로 만든다 | — |
| 2 | 브라우저 | `event_type`·`audience`를 **키 → 한글 라벨**로 변환 | — |
| 3 | 브라우저 | `lib/api.ts`가 헤더 3개를 붙인다 | 키 없으면 요청 전에 막고 안내 |
| 4 | 네트워크 | `POST /api/speech/draft` | — |
| 5 | FastAPI | Pydantic이 JSON 검증. `event_name` 비면 | **400** |
| 6 | `common/keys.py` | `resolve_user_key()`로 헤더에서 키 추출 | **401** "설정에서 키를 넣어주세요" |
| 7 | `llm/catalog.py` | `resolve(provider, model)` — 허용목록에 없으면 | **400** "지원하지 않는 모델" |
| 8 | `prompts/builder.py` | `build_speech_prompt()` → `(system_prompt, user_prompt)` | — |
| 9 | `llm/client.py` | `call_llm(...)` → 글 한 덩어리 + 토큰 수 | **502** / 타임아웃 120초 |
| 10 | `common/quality.py` | `check_output()` — 빈 응답·분량 미달을 **경고로만** 담는다 | 막지 않음 |
| 11 | `db/drafts.py` | `create_draft()` 시도 | **실패해도 글은 버리지 않는다** → `save_warning` |
| 12 | FastAPI | 응답 조립 | — |
| 13 | 브라우저 | 본문 + `meta`(모델·시간·비용)를 화면에 그린다 | — |

### 응답 모양

```json
{
  "generated_text": "존경하는 ...",
  "char_count": 1459,
  "draft_id": "uuid 또는 null",
  "warnings": [],
  "save_warning": null,
  "meta": {
    "provider": "openai",
    "model": "gpt-5.6-sol",
    "elapsed_ms": 16300,
    "input_tokens": 3980,
    "output_tokens": 1500,
    "cost_won": 64
  }
}
```

> **`meta`를 결과 화면에 그대로 보여준다.**
> 어떤 모델로 몇 초 걸려 얼마 썼는지가 보이는 것만으로 앱의 완성도가 달라진다.
> 이 값은 DB의 `llm_meta` 칸에도 같이 저장한다 → 나중에 "어느 모델이 분량을 잘 지켰나"를 이력에서 뽑을 수 있다.

---

## 3. AI 파트 — 이 앱의 머리

### ① 이 파트가 하는 일

**결과물의 품질을 100% 결정한다.** 화면이 예뻐도 글이 별로면 만든 의미가 없다.
크게 두 가지다.

1. **모델 선택** — 어떤 회사·어떤 등급 모델로 부를지 정하고, 회사별로 다른 요청 모양을 맞춘다
2. **프롬프트 조립** — 5개 층을 쌓아 시스템 프롬프트 + 유저 프롬프트를 만든다

### ② 만들 파일

```
src/policy_writer/
├── llm/
│   ├── catalog.py     ★ 모델 허용목록 (원본에 없는 파일)
│   └── client.py      call_llm(provider, model_meta, ...)
└── prompts/
    ├── l1_identity.py   L1_SPEECH  상수 — 너는 누구다
    ├── l2_domain.py     L2_SPEECH  상수 — ★ 6단 기틀 + 8종 표 + 정형구
    ├── l3_rules.py      L3_SPEECH  상수 — 작성 절차 · 출력 형식
    └── builder.py       SpeechInput + build_l4/l5 + build_speech_prompt
```

---

### ③-1 모델 카탈로그 — 허용목록은 **서버가** 갖는다

#### 왜 서버가 갖나

헤더 `X-LLM-Model`은 사용자가 마음대로 바꿀 수 있다.
목록이 화면(프론트엔드)에만 있으면:

- 아무 문자열이나 실어 보낼 수 있고 → 없는 모델로 400이 난다
- **의도치 않게 비싼 모델**이 불릴 수 있다 (2원짜리 대신 64원짜리)

그래서 목록의 원본은 서버에 두고, 화면은 `GET /api/models`로 **받아서 그린다**. 목록이 두 벌이 되지 않게 한다.

#### `src/policy_writer/llm/catalog.py`

```python
# ─────────────────────────────────────────────────────────────
# 확인일: 2026-09-05
# ⚠️ 모델 id 와 가격은 바뀐다. 이 파일이 문서에서 가장 빨리 썩는 곳이다.
#    수정할 때마다 위 날짜를 갱신할 것.
#
# 검증 상태:
#   OpenAI  경제형/최상위 → [실측] 이 키로 직접 호출해 200 확인
#   OpenAI  표준형        → [조사] 공식 문서상 존재, 이 키로는 미호출
#   Anthropic 전부        → 키가 없어 미호출. 원본 코드가 쓰던 id 를 표준으로 둠
#   Anthropic 최상위      → 비워 뒀다 (아래 주석 참고)
# ─────────────────────────────────────────────────────────────

from fastapi import HTTPException

MODELS = {
    "openai": [
        {"id": "gpt-4o-mini",   "tier": "경제형", "temperature": True,
         "in": 0.15, "out": 0.60},   # [실측] 동작. 축사 729자 / 목표 1500
        {"id": "gpt-5.6-terra", "tier": "표준형", "temperature": False,
         "in": 2.00, "out": 12.00},  # [조사] 문서상 존재. 400 나면 gpt-4o 로 교체 가능
        {"id": "gpt-5.6-sol",   "tier": "최상위", "temperature": False,
         "in": 4.00, "out": 20.00},  # [실측] 동작. 축사 1459자 / 목표 1500
    ],
    "anthropic": [
        {"id": "claude-haiku-4-5",           "tier": "경제형", "temperature": True,
         "in": 1.00, "out": 5.00},
        {"id": "claude-sonnet-4-5-20250929", "tier": "표준형", "temperature": True,
         "in": 3.00, "out": 15.00},
        # 최상위 없음 — Anthropic 키가 없어 검증을 못 했다.
        # 키가 생기면 claude-opus-4-5 ($5/$25) 를 한 번 호출해 보고,
        # 200 이 오면 그때 이 줄을 추가한다. 검증 전에는 넣지 않는다.
    ],
}

# ⚠️ 이 DEFAULTS 는 "헤더에 X-LLM-Model 이 아예 없을 때 서버가 쓰는 값"이다.
#    화면이 처음 보여주는 등급(localStorage 초기값)과는 다른 개념이다. 3-8 절 참고.
DEFAULTS = {
    "openai":    "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-5-20250929",
}

DEFAULT_PROVIDER = "openai"   # ★ 원본 기본값은 "gemini" 였다. 반드시 바꿀 것


def resolve(provider: str, model: str | None) -> dict:
    """허용목록에서 찾는다. 없으면 400."""
    table = MODELS.get(provider)
    if not table:
        raise HTTPException(400, f"지원하지 않는 회사: {provider}")
    if not model:
        model = DEFAULTS[provider]
    for m in table:
        if m["id"] == model:
            return m
    raise HTTPException(400, f"{provider}에서 지원하지 않는 모델: {model}")
```

#### 규칙 3개 — 어기면 앱이 안 돈다

| 규칙 | 내용 |
|---|---|
| **검증 안 한 id는 목록에 넣지 않는다** | `gpt-6-astra`, `claude-opus-4-1` 같은 id를 지어내지 말 것. 200 응답을 눈으로 본 것만 넣는다 |
| **기본 회사는 `openai`** | 원본 기본값은 `gemini`였다. 서버(`speech.py`의 `Header(...)`)와 화면(`useLLMSettings.ts`) **두 곳 다** 바꾼다. 안 그러면 첫 요청이 401로 죽는다 |
| **Anthropic은 2등급뿐** | 최상위 칸을 억지로 채우지 않는다. 3칸 중 2칸만 열어 두는 게 정직한 상태다 |

---

### ③-2 회사마다 요청 모양이 다르다 — 이게 이 파트의 진짜 난이도

회사가 달라서가 아니라 **같은 회사 안에서도 모델마다 다르다.**

| 걸림돌 | 내용 |
|---|---|
| **`temperature`** | 최신 추론 모델은 **보내면 HTTP 400**. Claude 5 계열, OpenAI GPT-5/5.6/6 계열이 그렇다. 5개 중 2개가 거부한다 |
| **출력 길이 필드 이름** | OpenAI Chat Completions는 `max_completion_tokens` (`max_tokens`는 deprecated). Anthropic은 `max_tokens` |
| **시스템 프롬프트 위치** | Anthropic은 **본문 최상위 `system`** 필드. OpenAI는 **`messages[0]`에 `role:"system"`** |

#### 해결 규칙 — "의심스러우면 안 보낸다"

```
temperature 를 보낼지 확신이 없으면  →  안 보낸다

  안 보내면   → 모델 기본값으로 동작 (항상 안전)
  잘못 보내면 → HTTP 400, 요청 자체가 실패
```

**손해가 비대칭이다.** 안 보내서 생기는 손해는 "온도 조절을 못 함"이고, 보내서 생기는 손해는 "앱이 안 돌아감"이다.
그래서 `catalog.py`의 `temperature` 플래그가 `True`일 때**만** 필드를 넣는다.

#### `src/policy_writer/llm/client.py`

```python
async def call_llm(
    *,
    provider: str,
    model_meta: dict,          # ★ catalog.resolve() 가 돌려준 것
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> tuple[str, dict]:         # (생성된 글, meta)
    ...
```

**Anthropic 본문 조립**

```python
url = "https://api.anthropic.com/v1/messages"
headers = {
    "x-api-key": api_key,
    "anthropic-version": "2023-06-01",
    "content-type": "application/json",
}
body = {
    "model": model_meta["id"],
    "max_tokens": max_tokens,              # ← Anthropic 은 max_tokens
    "system": system_prompt,               # ← 최상위 필드
    "messages": [{"role": "user", "content": user_prompt}],
}
if model_meta["temperature"]:              # ← 플래그가 True 일 때만
    body["temperature"] = temperature
```

**OpenAI 본문 조립**

```python
url = "https://api.openai.com/v1/chat/completions"
headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
body = {
    "model": model_meta["id"],
    "max_completion_tokens": max_tokens,   # ⚠️ max_tokens 아님
    "messages": [
        {"role": "system", "content": system_prompt},   # ← messages[0]
        {"role": "user",   "content": user_prompt},
    ],
}
if model_meta["temperature"]:
    body["temperature"] = temperature
```

**응답에서 뽑을 것**

| 회사 | 본문 | 입력 토큰 | 출력 토큰 |
|---|---|---|---|
| Anthropic | `content[0].text` | `usage.input_tokens` | `usage.output_tokens` |
| OpenAI | `choices[0].message.content` | `usage.prompt_tokens` | `usage.completion_tokens` |

두 회사의 이름이 다르므로 **`call_llm` 안에서 통일된 `meta` 딕셔너리로 바꿔서** 돌려준다.
바깥(라우터)은 회사를 몰라도 되게 만든다.

---

### ③-3 프롬프트 5층 — 파일은 3개

**5층인데 파일이 3개인 이유**: L1~L3은 요청과 무관하게 항상 똑같은 글이라 **파일에 상수로** 저장하고, L4~L5는 요청마다 달라지므로 **함수**다.

```
┌ 시스템 프롬프트 — 매번 똑같음 → 상수 파일 ──────────┐
│ L1  l1_identity.py   너는 누구다                     │
│ L2  l2_domain.py     6단 기틀 · 8종 표 · 정형구 사전  │  ★ 핵심
│ L3  l3_rules.py      작성 절차 · 출력 형식            │
└──────────────────────────────────────────────────────┘
┌ 유저 프롬프트 — 요청마다 다름 → 함수 ────────────────┐
│ L4  build_l4_speech()   업로드한 행사계획서 발췌      │
│     (persona_block)     폼에 적은 말투 — 사이에 낀다  │
│ L5  build_l5_speech()   이번 행사 정보                │
└──────────────────────────────────────────────────────┘
```

```python
# src/policy_writer/prompts/builder.py

def build_speech_prompt(input: SpeechInput, *, contexts=None) -> tuple[str, str]:
    system_prompt = "\n\n".join([L1_SPEECH, L2_SPEECH, L3_SPEECH])

    user_parts = []
    l4 = build_l4_speech(contexts)          # 참고자료가 있을 때만
    if l4:
        user_parts.append(l4)
    if input.persona_block.strip():         # 저장소 없이 폼 값만 사용
        user_parts.append(input.persona_block.strip())
    user_parts.append(build_l5_speech(input))
    user_prompt = "\n\n---\n\n".join(user_parts)

    return system_prompt, user_prompt
```

> **`persona_block`은 L4와 L5 사이에 낀다.** 페르소나 저장소는 안 만들지만 이 조각은 그대로 둔다.
> 값이 빈 문자열이면 아예 끼우지 않는다.
> `[실측]` 이 칸에 "현장에서 답을 찾겠습니다"를 넣으면 본문에 그대로 나오고, 빼면 빠진다.

> **★ 만든 함수는 그 자리에서 라우터에 연결한다.**
> 원본은 `build_press_prompt`를 만들어 놓고 **어떤 파일도 부르지 않는다.** `api/press.py` 전체를 검색해도 호출이 0건이다.
> 함수만 만들고 연결을 안 하면 "만든 줄 알았는데 안 돌아가는" 상태가 된다.

---

### ③-4 L2 — 6단 기틀이 이 앱의 정체성

구두용 7종이 공유하는 기틀:

| 단 | 역할 | 분량 비중 |
|---|---|---|
| 1 | 호명 · 인사 | 5~10% |
| 2 | 행사 의의 | 10~15% |
| 3 | 감사 · 예우 | 10~15% |
| 4 | **정책 · 사례** (첫째/둘째/셋째) | **50~60%** |
| 5 | 당부 | 5~10% |
| 6 | 마무리 | 5~10% |

**서면축사만 4단이다.** (인사 약식 → 의의 → 정부 의지 → 기대 + 서명)
`안녕하십니까` 같은 **구두 인사를 쓰면 안 된다**. 읽는 글이 아니라 종이에 실리는 글이기 때문이다.

#### 8종 표 — 유형이 거의 공짜인 이유

1~7번은 **같은 6단 기틀**을 쓰고, **어느 단을 두껍게 쓸지만** 다르다.
그래서 L2에 아래 표를 한 개 더 넣고 화면에 버튼 8개를 배열로 정의하면 끝난다.

| # | 유형 | 화면 라벨 | 키 | 두껍게 할 단 |
|---|---|---|---|---|
| 1 | 축사 | 축사 | `chuksa` | **4단** (기본형) |
| 2 | 기념사 | 기념사 | `gyenyeomsa` | 2단 |
| 3 | 신년사 | 신년사 | `sinnyeonsa` | 5단 |
| 4 | 격려사 | 격려사 | `gyeoryeosa` | 5단 |
| 5 | 환영사 | 환영사 | `hwanyeongsa` | 1단 |
| 6 | 개회사 | 개회사 | `gaehoesa` | 2+3단 |
| 7 | 이임사 | 이임사 | `iimsa` | 3+5단 |
| 8 | 서면축사 | 서면축사 | `seomyeonchuksa` | **4단 구조로 교체** |

#### 정형구 사전 · 직급별 톤 · 분량 환산표

```
1단 호명    "존경하는 [청중] 여러분, 반갑습니다"
2단 의의    "오늘 「[행사명]」을 맞이하여..."
3단 예우    "이 자리를 빛내 주신 [참석자]을 비롯한 모든 분께 감사드립니다"
6단 마무리  "다시 한번 [축하]를 드리며, [기원]합니다. 감사합니다"

직급별 톤
  장관        굳건히 · 흔들림 없이
  차관        차질없이 · 철저히
  실장·국장   체계적으로 · 내실 있게
  과장·팀장   함께 · 꾸준히

분량 환산
  1분 280자 · 3분 850자 · 5분 1,400자 · 7분 2,000자 · 10분 2,800자
```

**문체 규칙**: 경어체(`~습니다 / ~겠습니다`). 한 문장 80자 이내. **입력에 없는 숫자는 만들지 말 것.**

---

### ③-5 `SpeechInput` — 폼과 1:1로 맞춘 14개 칸

`prompts/builder.py`에 Pydantic 모델로 정의한다.

| 필드 | 타입 | 기본값 | 뜻 |
|---|---|---|---|
| `event_name` | `str` | **(필수)** | 행사명. 비면 400 |
| `event_type` | `str` | `"축사"` | 8종 **한글 라벨** (키 아님) |
| `event_date` | `str` | `""` | 날짜 문자열 |
| `event_location` | `str` | `""` | 장소 |
| `speaker_name` | `str` | `""` | 발화자 이름 |
| `speaker_role` | `str` | `""` | `장관`/`차관`/`실장·국장`/`과장·팀장`/`기관장` |
| `speaker_organization` | `str` | `""` | 소속 기관 |
| `audience` | `str` | `""` | 쉼표로 이은 한글 청중 |
| `vip_list` | `list[str]` | `[]` | 주요 참석자. 직급 순 |
| `target_chars` | `int` | `1400` | 목표 글자수 (화면 표준값은 1500) |
| `key_messages` | `list[str]` | `[]` | 반드시 본문에 넣을 메시지 |
| `quotes_or_anecdotes` | `list[str]` | `[]` | 쓸 수 있는 통계·일화 |
| `avoid_phrases` | `list[str]` | `[]` | 이번 건에서만 쓰지 말 표현 |
| `persona_block` | `str` | `""` | 말투·자주 쓰는 표현. **저장소 없이 폼에만** |

> **화면에는 이 14칸을 전부 만든다.** 일부만 만들고 "예시"로 끝내지 않는다.

---

### ③-6 비용을 원화로 보여준다

말씀자료 1건 = 입력 약 4,000토큰(L1~L5) + 출력 약 1,500토큰(1,500자), 1달러 1,400원 기준.

```
1건당 원화 = (입력 4,000 × in / 1,000,000  +  출력 1,500 × out / 1,000,000) × 1,400
```

| 회사 | 등급 | 모델 | `temp` | 1건당 | 검증 |
|---|---|---|:---:|---:|---|
| OpenAI | 경제형 | `gpt-4o-mini` | ✅ | **약 2원** | **[실측]** 동작 |
| Anthropic | 경제형 | `claude-haiku-4-5` | ✅ | 약 16원 | [조사] 미호출 |
| OpenAI | 표준형 | `gpt-5.6-terra` | ❌ | 약 36원 | [조사] 미호출 |
| Anthropic | 표준형 | `claude-sonnet-4-5-20250929` | ✅ | 약 48원 | 원본이 쓰는 id, 미호출 |
| OpenAI | 최상위 | `gpt-5.6-sol` | ❌ | **약 64원** | **[실측]** 동작 |

예) sonnet-4-5 = 4,000 × $3/1M + 1,500 × $15/1M = $0.0345 → **48원**

**가장 싼 것(2원)과 확인된 최상위(64원)가 약 32배 차이다.** 이 숫자를 설정 화면에 그대로 보여준다.
사용자에게 `$0.000123` 같은 숫자는 의미가 없다. **원 단위 정수**로 변환해서 내려준다.

---

### ③-7 품질 검사 — 막지 말고 알려만 준다

`common/quality.py`의 `check_output()`은 **경고만 담는다.**

```python
def check_output(text: str, target_chars: int) -> list[str]:
    warnings = []
    if not text.strip():
        warnings.append("응답이 비어 있습니다. 다시 시도해 주세요.")
    elif len(text) < target_chars * 0.6:
        warnings.append(f"목표({target_chars}자)보다 짧습니다. 현재 {len(text)}자.")
    return warnings
```

**왜 막지 않나**: 짧아도 사용자가 손보면 쓸 수 있다. 서버가 판단해서 버리면 사용자는 아무것도 못 받는다.

---

### ④ AI 파트 완료 확인

- [ ] `GET /api/models`가 5개 모델을 회사별로 내려준다 (`won_per_doc` 포함)
- [ ] 목록에 없는 모델 id를 헤더에 실어 보내면 **400**이 난다
- [ ] `X-LLM-Model`을 아예 안 보내면 회사 기본값으로 동작한다
- [ ] `gpt-5.6-sol`에 `temperature`를 안 보내서 200이 온다
- [ ] `gpt-4o-mini`에는 `temperature`가 실려 나간다
- [ ] Python 스크립트로 `/api/speech/draft`를 호출하면 **6단 축사**가 나온다
- [ ] 응답 `meta`에 `input_tokens`·`output_tokens`·`cost_won`이 채워져 있다

### ⑤ AI 파트의 함정

| 함정 | 증상 | 대응 |
|---|---|---|
| `temperature` 400 | `Only the default (1) value is supported` | `catalog`의 플래그로 분기. 의심스러우면 안 보낸다 |
| OpenAI 출력 길이 | 출력이 잘리거나 400 | `max_completion_tokens` 사용 (`max_tokens` 아님) |
| 기본 회사 `gemini` | 첫 요청이 401 | 서버·화면 두 곳 다 `openai`로 |
| 함수 만들고 연결 안 함 | "만든 줄 알았는데 안 돌아감" | 만든 즉시 라우터에 연결 |
| 모델 id·가격 노후화 | 어제 되던 게 오늘 400 | `catalog.py` 맨 위에 확인 날짜 주석 |

---

## 4. 백엔드 파트 — FastAPI

### ① 이 파트가 하는 일

**창구를 열고, 검증하고, AI 파트에 넘기고, 결과를 포장해서 돌려준다.**
비즈니스 로직(글을 어떻게 쓰나)은 AI 파트에 있고, 백엔드는 **배관**이다.

### ② 만들 파일

```
src/policy_writer/
├── server.py          앱 조립. uvicorn 이 가리키는 곳
├── config.py          .env → Settings 상자 하나 (lru_cache)
│
├── api/
│   ├── __init__.py    ★ 라우터 export — 여기와 server.py 둘 다 고쳐야 함
│   ├── settings.py    키 검증 + 모델 목록 + 로컬 키
│   ├── speech.py      말씀자료 작성 ← 정본
│   ├── download.py    md · hwpx
│   └── drafts.py      작성 이력
│
├── common/            ★ 원본에 없는 폴더
│   ├── keys.py        resolve_user_key(), norm_provider()
│   ├── parsing.py     parse_json_response()
│   └── quality.py     check_output()
│
├── extractors/files.py
├── exporters/converters.py
└── db/drafts.py
```

**원본에 있지만 안 만드는 것**: `rag/`, `policy_api/`, `api/explain.py`, `api/refine.py`, `api/personas.py`, `db/personas.py`

---

### ③-1 `server.py` — 조립 순서가 중요하다

```python
app = FastAPI(title="말씀자료 작성기", version="0.1.0")
settings = get_settings()

# 1) CORS — 개발일 때만 5173 허용
if settings.environment == "development":
    app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], ...)

# 2) 라우터 4개
app.include_router(speech_router,   prefix="/api/speech")
app.include_router(download_router, prefix="/api/download")
app.include_router(drafts_router,   prefix="/api/drafts")
app.include_router(settings_router)                      # 주소가 제각각이라 prefix 없음

# 3) 헬스체크 / 정보
@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/api/info")
def info(): return {"environment": settings.environment, "version": "0.1.0"}

# 4) ★ SPA 폴백 — 반드시 맨 마지막
@app.get("/{full_path:path}")
def spa(full_path: str):
    return FileResponse("static/index.html")
```

> **🔴 SPA 폴백은 반드시 모든 `include_router` 뒤에 둔다.**
> 순서가 바뀌면 `/api/...` 요청이 **전부 `index.html`을 받는다.** 화면에서는 "API가 이상한 응답을 준다"로 보인다.
> FastAPI는 라우트를 **등록 순서대로** 매칭하기 때문이다.

---

### ③-2 `config.py` — 상자 하나

```python
from functools import lru_cache
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    environment: str = "development"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    @property
    def local_llm_keys(self) -> dict:
        """개발 편의용. production 이면 무조건 빈 dict."""
        if self.environment == "production":
            return {}
        return {k: v for k, v in {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }.items() if v}

@lru_cache
def get_settings() -> Settings:
    return Settings(_env_file=".env")
```

> **🟠 `.env`를 고치면 서버를 껐다 켜야 한다.** `@lru_cache`라서 프로세스가 켜진 동안 **한 번만** 읽는다.
> "키를 넣었는데 왜 안 되지?"의 90%가 이것이다.

> **🟡 `os.environ.get()`과 `get_settings()`를 섞어 쓰지 말 것.**
> pydantic이 `.env`를 Settings에만 넣으면 프로세스 환경변수에는 없다.
> 원본은 이 둘을 섞어 써서 "분명히 `.env`에 있는데 미설정으로 뜨는" 버그가 있다. **`get_settings()`만** 쓴다.

> `.env`의 `SUPABASE_ANON_KEY`는 **넣지 않는다.** 원본에 있지만 코드가 한 번도 읽지 않는다.

---

### ③-3 `api/__init__.py` — 한쪽만 고치면 404

새 API 파일을 추가하면 **두 곳을 같이** 고쳐야 한다.

1. `api/__init__.py`의 `import` + `__all__`
2. `server.py`의 `include_router`

| export | 파일 | prefix |
|---|---|---|
| `speech_router` | `api/speech.py` | `/api/speech` |
| `download_router` | `api/download.py` | `/api/download` |
| `drafts_router` | `api/drafts.py` | `/api/drafts` |
| `settings_router` | `api/settings.py` | (주소마다 다름) |

**원본은 9개, 우리는 4개다.** 5개를 안 만든다.

---

### ③-4 `common/` — 같은 코드를 두 벌 만들지 않기

원본의 문제는 **같은 코드가 여러 벌 있다는 것**이다.

| 중복 | 원본 | 이 프로젝트 |
|---|---|---|
| `_resolve_user_key` | **3벌** (`speech.py` · `press.py` · `explain.py`) | `common/keys.py`에 **1벌** |
| JSON 응답 파서 | **2벌** | `common/parsing.py`에 **1벌** |

문서 종류를 늘릴 때마다 복사가 늘어나는 구조다. **처음부터 한 곳에 모은다.**

```python
# common/keys.py
HEADER_BY_PROVIDER = {"openai": "X-OpenAI-Key", "anthropic": "X-Anthropic-Key"}

def norm_provider(raw: str | None) -> str:
    p = (raw or "").strip().lower()
    return p if p in HEADER_BY_PROVIDER else DEFAULT_PROVIDER

def resolve_user_key(request: Request, provider: str) -> str:
    key = request.headers.get(HEADER_BY_PROVIDER[provider], "").strip()
    if not key:
        raise HTTPException(401, "설정에서 API 키를 먼저 입력해 주세요.")
    return key
```

---

### ③-5 엔드포인트 11개

| 메서드 | 주소 | 본문 | 만드는 단계 |
|---|---|---|---|
| `GET` | `/health` | — | 1 |
| `GET` | `/api/info` | — | 1 |
| `POST` | `/api/validate-key` | `{ provider, api_key }` | 3 |
| `GET` | `/api/local-keys` | — (development 전용) | 3 |
| `GET` | `/api/models` | — | 4 |
| `POST` | `/api/speech/draft` | `{ input, reference_texts, max_tokens, temperature }` | 5 |
| `POST` | `/api/download/speech/md` | `{ title, generated_text }` | 7 |
| `POST` | `/api/download/speech/hwpx` | 〃 | 7 |
| `POST` | `/api/speech/draft-with-docs` | multipart: `input_json`, `plan_file`, `reference_files` | 9 |
| `POST` | `/api/speech/auto-draft` | 행사계획서 파일만으로 폼 추정 후 작성 | 9 |
| `GET` `DELETE` | `/api/drafts` · `/api/drafts/{id}` | `?limit=20` | 10 |

**총 11개.** 원본은 20개가 넘는다.

---

### ③-6 에러 처리 정책

| 상황 | 코드 | 사용자에게 보이는 말 |
|---|---|---|
| `event_name` 없음 | 400 | "행사명은 필수입니다" |
| 키 헤더 없음 | 401 | "설정에서 API 키를 먼저 입력해 주세요" |
| 키가 틀림 (AI사가 401) | 401 | "**인증 실패** — 키를 다시 확인해 주세요" |
| 허용목록에 없는 모델 | 400 | "openai에서 지원하지 않는 모델: xxx" |
| AI사 장애·5xx | 502 | "AI 서버가 응답하지 않습니다. 잠시 후 다시 시도해 주세요" |
| 120초 초과 | 504 | "시간이 초과되었습니다. 분량을 줄이거나 다시 시도해 주세요" |
| DB 저장 실패 | **200** | 본문은 정상 반환 + `save_warning`에 사유 |

> **저장 실패를 숨기지 않는다.** 원본은 `except Exception: pass`로 삼켜서 사용자가 저장 안 된 걸 모른다.
> 우리는 `save_warning`에 담아 화면에 띄운다.

### ④ 백엔드 파트 완료 확인

- [ ] `localhost:8010/health` → `{"status":"ok"}`
- [ ] `localhost:8010/api/info` → `{"environment":"development", ...}`
- [ ] `/api/speech/draft`에 빈 `event_name`을 보내면 400
- [ ] 키 헤더 없이 보내면 401, 메시지가 한글로 나옴
- [ ] 배포 후 `/api/models`가 HTML이 아니라 JSON을 돌려준다 (SPA 폴백 순서 확인)

---

## 5. 프론트엔드 파트 — React

### ① 이 파트가 하는 일

**폼을 그리고, 키를 기억하고, 헤더를 붙여 보내고, 결과를 보여준다.**
로직은 최소로 둔다. 판단은 전부 서버가 한다.

### ② 만들 파일

```
frontend/src/
├── main.tsx
├── App.tsx                  라우트 4개
├── routes/
│   ├── HubPage.tsx          홈 — 시작 카드
│   ├── WritePage.tsx        작성 폼        ← 300줄 넘기지 말 것
│   ├── ResultPage.tsx       결과 + meta 표시
│   ├── HistoryPage.tsx      작성 이력
│   └── SettingsPage.tsx     회사 + 모델 + 키
├── components/
│   ├── Field.tsx            입력칸 1개를 그리는 범용 컴포넌트
│   └── FormSection.tsx      칸 묶음
├── hooks/
│   └── useLLMSettings.ts    localStorage (회사 + 모델 + 키)
└── lib/
    ├── api.ts               ★ 모든 요청의 단일 창구
    ├── speechFields.ts      ★ 폼 칸 정의를 "데이터"로
    └── speech-data.ts       유형 8종 · 청중 · 분량 · 직급 상수
```

---

### ③-1 폼을 손으로 쓰지 않는다 — 데이터로 정의한다

원본은 `WritePage.tsx`가 **1,278줄**, `SpeechWriter.tsx`가 **1,423줄**이다. 폼을 통째로 손으로 썼기 때문이다.

**우리는 "어떤 칸이 있는지"를 목록으로 정의하고 화면이 그걸 읽어 그린다.**

```ts
// lib/speechFields.ts — 3장의 SpeechInput 14칸과 1:1. 이 목록이 화면의 전부다.
export const speechFields = [
  { key: 'event_name',           label: '행사명',           type: 'text',        required: true },
  { key: 'event_type',           label: '행사 유형',         type: 'select',      options: EVENT_TYPES },
  { key: 'event_date',           label: '일시',             type: 'text' },
  { key: 'event_location',       label: '장소',             type: 'text' },
  { key: 'speaker_name',         label: '이름',             type: 'text' },
  { key: 'speaker_role',         label: '직급',             type: 'select',      options: SPEAKER_ROLES },
  { key: 'speaker_organization', label: '소속 기관',         type: 'text' },
  { key: 'audience',             label: '청중',             type: 'multiselect', options: AUDIENCES },
  { key: 'target_chars',         label: '분량',             type: 'select',      options: LENGTHS },
  { key: 'key_messages',         label: '핵심 메시지',       type: 'list' },
  { key: 'quotes_or_anecdotes',  label: '인용할 통계·일화',   type: 'list' },
  { key: 'avoid_phrases',        label: '피할 표현',         type: 'list' },
  { key: 'vip_list',             label: '주요 참석자',       type: 'list' },
  { key: 'persona_block',        label: '페르소나(선택)',    type: 'textarea' },
] as const
```

`Field.tsx`는 `type`에 따라 `text` / `textarea` / `select` / `multiselect` / `list` 5가지만 그린다.
`WritePage.tsx`는 이 배열을 `map`으로 돌리기만 한다.

**목표: 화면 파일 하나가 300줄을 안 넘게.**

---

### ③-2 상수 — `lib/speech-data.ts`

**분량 6단계**

| 키 | 라벨 | 글자수 |
|---|---|---|
| `very_short` | 매우 짧게 | 600 |
| `short` | 짧게 | 900 |
| `standard` | 표준 | **1500** |
| `long` | 길게 | 2400 |
| `very_long` | 매우 길게 | 3500 |
| `custom` | 사용자 지정 | 300~5000 |

**청중 10종 (키)**

```
public_servant · citizen · expert · student · honoree
foreign_guest · industry · media · internal_staff · local_resident
```

**직급 5종**: `장관` / `차관` / `실장·국장` / `과장·팀장` / `기관장`

---

### ③-3 키 ↔ 라벨 변환 규칙 — 놓치기 쉬운 곳

**화면에서는 키를 쓰고, API로 보낼 때는 한글 라벨로 바꾼다.**

| 필드 | 화면 내부 | API로 보낼 때 |
|---|---|---|
| `event_type` | `"gyenyeomsa"` | `"기념사"` |
| `audience` | `["honoree", "public_servant"]` | `"유공자, 공무원"` (쉼표+공백으로 join) |
| `target_chars` | `"standard"` | `1500` (숫자) |

**왜 라벨을 보내나**: 프롬프트에 그대로 들어가는 값이기 때문이다. 서버가 다시 한글로 번역하는 표를 또 만들 필요가 없다.

---

### ③-4 `useLLMSettings.ts` — localStorage 키 5개

```
gw_llm_provider          "openai"                       (원본에 있음, 기본값만 변경)
gw_llm_key_openai        sk-...
gw_llm_key_anthropic     sk-ant-...
gw_llm_model_openai      "gpt-5.6-sol"                  ★ 신규
gw_llm_model_anthropic   "claude-sonnet-4-5-20250929"   ★ 신규
```

**모델을 회사별로 따로 기억한다.** 회사를 바꿨다 돌아와도 고른 등급이 유지된다.

**키 형식 검사**

```ts
const KEY_PATTERN = {
  openai:    /^sk-/,
  anthropic: /^sk-ant-/,
}
```

> ⚠️ **검사 순서에 주의.** Anthropic 키(`sk-ant-...`)도 `/^sk-/`를 통과한다.
> 회사별로 **따로** 검사하면 문제없지만, 하나의 정규식으로 합치면 오검출이 난다.

> 원본의 `gw_llm_key_gemini`는 만들지 않는다. 다만 **이미 브라우저에 남아 있을 수 있으니** `clearAll()`에서 옛 키도 같이 지운다.

---

### ③-5 `lib/api.ts` — 헤더는 한 곳에서만 붙인다

원본의 `callApi`는 **키 헤더만** 붙이고, `X-LLM-Provider`는 화면 파일마다 따로 붙인다.
화면이 늘어날 때마다 빠뜨릴 위험이 생긴다.

**우리는 `callApi`가 세 헤더를 전부 붙인다.**

```ts
export async function callApi(path: string, body: unknown) {
  const { provider, model, key } = getLLMSettings()
  if (!key) throw new ApiError(401, '설정에서 API 키를 먼저 입력해 주세요.')

  const res = await fetch(path, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-LLM-Provider': provider,                                  // ★
      'X-LLM-Model': model,                                        // ★
      [provider === 'openai' ? 'X-OpenAI-Key' : 'X-Anthropic-Key']: key,
    },
    body: JSON.stringify(body),
  })
  if (!res.ok) throw new ApiError(res.status, (await res.json()).detail)
  return res.json()
}
```

---

### ③-6 설정 화면 — 이름과 동작을 맞춘다

원본 `SettingsPage.tsx`의 제목은 **"기본 사용 모델"**인데 그 아래 버튼은 실제로는 **회사**를 고른다. 이름과 동작이 어긋나 있다.

**우리는 두 개를 분리해서 둘 다 만든다.**

```
설정 화면
┌─────────────────────────────────────────┐
│ AI 회사                                  │
│   [OpenAI ✓]   [Anthropic]              │  ← 키가 있는 회사만 활성
│                                          │
│ 모델 등급                                │
│   ○ 경제형   gpt-4o-mini      약  2원    │
│   ○ 표준형   gpt-5.6-terra    약 36원    │
│   ● 최상위   gpt-5.6-sol      약 64원    │  ← 초기 선택값
│                                          │
│ API 키                                   │
│   [sk-••••••••••••]  [연결 시험]         │
└─────────────────────────────────────────┘
```

- 모델 목록은 `GET /api/models`로 **받아서** 그린다. 화면에 하드코딩하지 않는다
- 회사를 바꾸면 모델 목록과 비용이 같이 바뀐다
- Anthropic은 2칸만 나온다 (최상위 없음) — **이게 정상이다**

> **🟠 "기본값"이 두 개다. 헷갈리기 쉬우니 구분해서 기억한다.**
>
> | | 어디에 | 값 | 언제 쓰이나 |
> |---|---|---|---|
> | 서버 폴백 | `catalog.DEFAULTS` | `gpt-4o-mini` | 헤더 `X-LLM-Model`이 **아예 없을 때** |
> | 화면 초기값 | `useLLMSettings` localStorage 초기값 | **최상위** (`gpt-5.6-sol`) | 사용자가 처음 설정 화면을 열었을 때 |
>
> **화면 초기값을 최상위로 두는 이유**: 경제형(mini)은 목표를 올려도 700~1,000자에서 멈춘다 (11장 실측).
> 경제형을 기본으로 두면 "분량이 왜 이렇게 짧냐"는 불만이 첫 사용에서 바로 나온다.
> 서버 폴백을 굳이 mini로 두는 이유는 반대다 — 헤더가 없는 건 **비정상 요청**이므로 가장 싼 모델로 받는 게 안전하다.

### ③-7 결과 화면 — `meta`를 보여준다

```
┌──────────────────────────────────────────────┐
│ 축사 · 청년 주거지원 정책 설명회               │
│ 1,459자 · gpt-5.6-sol · 16.3초 · 약 64원      │  ← meta
├──────────────────────────────────────────────┤
│ 존경하는 ...                                  │
│                                               │
├──────────────────────────────────────────────┤
│  [마크다운 받기]  [한글파일 받기]  [복사]      │
└──────────────────────────────────────────────┘
```

`warnings`가 있으면 본문 위에 노란 띠로, `save_warning`이 있으면 회색 띠로 표시한다.

### ④ 프론트엔드 파트 완료 확인

- [ ] 화면 4개가 전부 라우팅된다
- [ ] `/write`의 폼에 **14칸이 전부** 있다
- [ ] 회사를 바꾸면 모델 목록과 1건당 비용이 바뀐다
- [ ] 회사를 바꿨다 돌아오면 고른 모델 등급이 유지된다
- [ ] 키를 지우고 [작성]을 누르면 **"설정에서 키를 넣어주세요"**가 뜬다 (앱이 깨지지 않는다)
- [ ] 결과 화면에 모델·시간·비용이 보인다
- [ ] 화면 파일 중 300줄을 넘는 것이 없다

---

## 6. DB 파트 — Supabase

### ① 이 파트가 하는 일

**작성 이력을 남긴다. 그게 전부다.**
없어도 서버는 뜨고 글도 나온다. **저장만 실패한다.**

### ② 만들 파일

```
supabase/migrations/001_init.sql
src/policy_writer/db/drafts.py
```

### ③-1 SDK를 쓰지 않는다 — httpx로 REST를 직접 친다

```
POST  {SUPABASE_URL}/rest/v1/drafts
GET   {SUPABASE_URL}/rest/v1/drafts?order=created_at.desc&limit=20
DELETE {SUPABASE_URL}/rest/v1/drafts?id=eq.{uuid}
```

**헤더**

```
apikey:        {SUPABASE_SERVICE_ROLE_KEY}
Authorization: Bearer {SUPABASE_SERVICE_ROLE_KEY}
Content-Type:  application/json
Prefer:        return=representation
```

**왜 SDK를 안 쓰나**: 의존성이 하나 줄고, 어차피 쓰는 기능이 3개뿐이다. httpx는 AI 호출에도 이미 쓴다.

> ⚠️ **`SUPABASE_URL` 끝에 `/rest/v1/`를 붙이지 말 것.** 코드가 붙인다. 두 번 붙으면 404가 난다.

---

### ③-2 표 1개

```sql
-- supabase/migrations/001_init.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.drafts (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type     TEXT NOT NULL,                  -- 축사 · 기념사 · ...
  title          TEXT NOT NULL,                  -- 행사명
  form_data      JSONB NOT NULL DEFAULT '{}'::jsonb,   -- SpeechInput 전부
  generated_text TEXT,
  llm_meta       JSONB DEFAULT '{}'::jsonb,      -- ★ provider·model·비용·소요시간
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON public.drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_event_type ON public.drafts(event_type);

ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;
```

**`llm_meta`를 남기는 게 포인트다.** 나중에 "어느 모델이 분량을 잘 지켰나"를 이력에서 SQL로 뽑을 수 있다.

**마지막 줄(RLS)이 중요하다.** 정책을 하나도 안 만들고 잠그면 외부에서는 아무도 못 읽고, 서버가 쓰는 `service_role` 키만 통과한다.

---

### ③-3 문서 템플릿은 DB에 넣지 않는다

6단 기틀·정형구 사전은 전부 `prompts/l2_domain.py`에 둔다.

| 코드에 둘 때 | DB에 둘 때 |
|---|---|
| git이 변경 이력을 자동 기록 | 이력 관리를 따로 만들어야 함 |
| **관리 화면 불필요** | **관리 화면 필수** (+시간) |
| 배포하면 바로 반영 | 마이그레이션 필요 |

### ③-4 저장 실패를 숨기지 않는다

```python
draft_id, save_warning = None, None
try:
    draft_id = await create_draft(...)
except Exception as e:
    save_warning = f"이력 저장에 실패했습니다: {e}"   # 글은 그대로 돌려준다
```

### ④ DB 파트 완료 확인

- [ ] `/history`에 목록이 뜨고, 항목을 누르면 다시 열린다
- [ ] **Supabase 설정을 지워도 축사 생성은 된다** (`draft_id`가 `null`로 옴)
- [ ] 이력에 모델명과 비용이 같이 보인다
- [ ] 저장 실패 시 화면에 `save_warning`이 뜬다

---

## 7. 네트워크 파트

### ① 이 파트가 하는 일

**화면과 서버, 서버와 AI 회사 사이를 잇는 규칙 전부.**
포트 · 프록시 · CORS · 헤더 · 상태코드 · 타임아웃 · 배포 라우팅.

---

### ③-1 그림이 두 개다 — 개발과 배포가 다르다

**개발 (로컬)**

```
브라우저
  │  http://localhost:5173/write        ← 화면
  │  http://localhost:5173/api/...      ← Vite 프록시가 가로챔
  ▼
Vite dev server (:5173)
  │  proxy: '/api' → http://localhost:8010
  ▼
FastAPI (:8010)
  ▼
api.openai.com / api.anthropic.com
```

**배포 (Render)**

```
브라우저
  │  https://내앱.onrender.com/write     ← SPA 폴백 → index.html
  │  https://내앱.onrender.com/api/...   ← 라우터가 먼저 잡음
  ▼
FastAPI 한 대 (static/ 서빙 + /api 처리)
  ▼
api.openai.com / api.anthropic.com
```

> **배포에서는 화면과 API가 같은 도메인이다.** 그래서 **CORS가 아예 필요 없다.**
> CORS 미들웨어는 `environment == "development"`일 때만 켠다.

---

### ③-2 포트 — 8010을 쓴다

| | 포트 | 비고 |
|---|---|---|
| 백엔드 | **8010** | 이 PC에서 8000번은 다른 프로그램이 잡고 있다 |
| 프론트 | 5173 | Vite 기본값 |

**8010을 세 곳에 똑같이 써야 한다.**

1. `run.ps1`의 `uvicorn --port 8010`
2. `frontend/vite.config.ts`의 프록시 대상
3. 문서·테스트 스크립트의 주소

---

### ③-3 `vite.config.ts` — 두 줄이 핵심

```ts
export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',      // ★ 기본값(dist)이면 FastAPI 가 못 찾는다
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8010', changeOrigin: true },   // ★
    },
  },
})
```

**프록시를 쓰는 이유**: 개발 중에도 프론트 코드가 `/api/speech/draft`라는 **상대 경로**를 쓰게 하기 위해서다.
그러면 배포할 때 코드를 한 글자도 안 고쳐도 된다.

---

### ③-4 CORS

```python
if settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],     # X-LLM-Provider 등 커스텀 헤더 통과에 필요
    )
```

> `allow_headers=["*"]`가 없으면 브라우저의 preflight(OPTIONS)에서 **커스텀 헤더 3개가 막힌다.**
> 증상: "요청은 갔는데 서버가 키가 없다고 한다."

---

### ③-5 SPA 폴백 순서 — 🔴 가장 흔한 사고

```python
# ✅ 올바른 순서
app.include_router(speech_router, prefix="/api/speech")
...
@app.get("/{full_path:path}")          # ← 맨 마지막
def spa(full_path: str): ...
```

```python
# ❌ 이렇게 하면 /api 요청이 전부 HTML 을 받는다
@app.get("/{full_path:path}")
def spa(full_path: str): ...
app.include_router(speech_router, prefix="/api/speech")
```

---

### ③-6 헤더 계약

**요청 헤더 — 모든 AI 호출에 공통**

| 헤더 | 값 | 없으면 |
|---|---|---|
| `X-LLM-Provider` | `openai` \| `anthropic` | 기본값 `openai` |
| `X-LLM-Model` | catalog에 있는 id | 회사 기본값으로 대체 |
| `X-OpenAI-Key` \| `X-Anthropic-Key` | 사용자 키 | **401** |

**응답 헤더 — 다운로드에만**

```python
from urllib.parse import quote
headers = {
    "Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"
}
```

> **한글 파일명은 RFC 5987 형식(`filename*=UTF-8''`)으로 보낸다.**
> `filename="축사.hwpx"`로 하면 브라우저에서 깨진다.

---

### ③-7 상태코드 표

| 코드 | 언제 | 화면 동작 |
|---|---|---|
| 200 | 정상 (DB 저장 실패 포함) | 결과 표시 + 경고 띠 |
| 400 | 필수값 누락 / 모델 허용목록 밖 | 해당 칸에 빨간 안내 |
| 401 | 키 없음 / 키 틀림 | "설정으로 가기" 버튼 제공 |
| 404 | 없는 이력 id | 목록으로 돌려보냄 |
| 502 | AI사 오류 | "잠시 후 다시 시도" |
| 504 | 120초 초과 | "분량을 줄여보세요" |

---

### ③-8 타임아웃

| 구간 | 값 | 이유 |
|---|---|---|
| 서버 → AI사 | **120초** | 최상위 모델이 1,500자를 쓰는 데 16초 걸린다. 여유를 크게 둔다 |
| 브라우저 → 서버 | 130초 | 서버 타임아웃보다 길게. 그래야 504를 사용자가 받는다 |

브라우저 쪽은 `AbortController`로 건다. 작성 중에는 버튼을 비활성화하고 진행 표시를 띄운다.

---

### ③-9 파일 업로드 경로

`/api/speech/draft-with-docs`와 `/api/speech/auto-draft`는 **multipart/form-data**다.

```
input_json:      SpeechInput 을 문자열로 담은 JSON  (Content-Type: application/json)
plan_file:       행사계획서 1개
reference_files: 참고자료 여러 개
```

> 이때는 `Content-Type`을 **직접 지정하지 않는다.** `FormData`를 넘기면 브라우저가 boundary까지 붙여 준다.
> 손으로 `multipart/form-data`를 넣으면 boundary가 빠져서 서버가 파싱에 실패한다.

### ④ 네트워크 파트 완료 확인

- [ ] 개발 중 `localhost:5173`에서 `/api/models`를 부르면 JSON이 온다 (프록시 동작)
- [ ] 배포 주소에서 `/api/models`를 부르면 JSON이 온다 (SPA 폴백 순서)
- [ ] 배포 주소에서 `/write`를 새로고침해도 404가 아니라 화면이 뜬다
- [ ] 한글 파일명 다운로드가 안 깨진다
- [ ] 키를 지우면 401, 잘못된 모델이면 400이 각각 다른 메시지로 뜬다

---

## 8. 파일 입출력 파트

### ① 이 파트가 하는 일

**읽기**: 행사계획서를 올리면 글자를 뽑아 프롬프트 L4에 넣는다.
**쓰기**: 결과를 마크다운·한글파일로 만들어 내려준다.

### ②-1 읽기 — `extractors/files.py`

**실제로 글자를 뽑는 건 4종뿐이다.**

| 형식 | 동작 | 방법 |
|---|---|---|
| `txt` | ✅ | `utf-8 → cp949 → euc-kr` 순서로 시도 |
| `pdf` | ✅ | pypdf, 최대 20페이지 |
| `docx` | ✅ | python-docx |
| `hwpx` | ✅ | ZIP을 열어 `Contents/section*.xml`의 `<hp:t>` 노드 |
| `hwp` | ❌ | `"HWPX로 변환 후 업로드 부탁드립니다"` 문자열 반환 |
| `doc` `ppt` `pptx` | ❌ | `"현재 텍스트 추출 미지원"` 문자열 반환 |

> 🔴 **실패해도 예외를 던지지 않고 안내 문자열을 돌려준다.**
> 이 문자열이 **그대로 프롬프트에 실려 들어갈 수 있다.**
> 라우터에서 `(...미지원)` 또는 `(...부탁드립니다)`로 시작하는지 확인하고, 그러면 L4에 넣지 말고 사용자에게 경고로 돌려준다.

파일당 최대 **5,000자**로 자른다. (프롬프트 폭주 방지)

### ②-2 쓰기 — `exporters/converters.py`

**python-hwpx는 단순한 것만 쓴다.**

```python
from hwpx import HwpxDocument

doc = HwpxDocument.new()
for para in paragraphs:
    doc.add_paragraph(para)     # 이것만
doc.save_to_path(임시파일경로)   # 이것만
```

> **표·이미지·도형은 시도하면 파일이 깨진다.** 한글 프로그램이 아예 못 연다.

**단락 분할 규칙**

```python
import re
paragraphs = re.split(r"\n\s*\n+", text.strip())
paragraphs = [re.sub(r"\s*\n\s*", " ", p).strip() for p in paragraphs]
```

AI 출력은 **빈 줄로 단락이 나뉜다.** 단락 안의 단일 줄바꿈은 공백으로 합친다.

### ④ 파일 파트 완료 확인

- [ ] PDF 하나를 올리고 [작성]을 누르면 축사가 나온다
- [ ] **원본에 없는 날짜·인명이 결과에 없다**
- [ ] `.hwp`를 올리면 "HWPX로 변환해 주세요" 안내가 뜬다 (프롬프트에 안 들어감)
- [ ] 받은 hwpx가 **한글 프로그램에서 열린다**
- [ ] 파일명이 `축사_청년주거_20260905.hwpx`처럼 한글로 안 깨지고 나온다

---

## 9. 보안 파트

### 규칙 7개

| # | 규칙 | 왜 |
|---|---|---|
| 1 | LLM 키는 **요청 헤더로만**. 서버 디스크·DB·로그에 저장 금지 | 저장하는 순간 유출 책임이 생긴다 |
| 2 | `ENVIRONMENT=production`이면 `/api/local-keys`는 **빈 응답** | 아래 🔴 참고 |
| 3 | **모델 id는 서버 허용목록으로 검증** | 헤더는 사용자가 바꿀 수 있다 |
| 4 | 인용·통계는 사용자가 준 것만. 없으면 비우거나 "자료에 없음" | AI가 숫자를 지어내면 공문서로 못 쓴다 |
| 5 | `SUPABASE_SERVICE_ROLE_KEY`는 **브라우저로 절대 안 나간다** | 이 키는 RLS를 통과한다 |
| 6 | `SUPABASE_URL` 끝에 `/rest/v1/` 붙이지 않기 | 코드가 붙인다 |
| 7 | **`.gitignore`를 첫 커밋 전에** 만들기 | 키가 한 번 올라가면 지워도 기록에 남는다 |

### 🔴 함정 1번 — `ENVIRONMENT`가 빠지면 AI 키가 공개된다

`GET /api/local-keys`는 **인증 없이** `.env`의 AI 키를 브라우저에 내려준다.
막는 장치는 `ENVIRONMENT=production` **하나뿐이다.**

| 배포 방식 | 결과 |
|---|---|
| `render.yaml`로 배포 | 값이 파일에 고정 → 안전 |
| Render 대시보드에서 **수동 생성** | 기본값이 `development` → **누구나 `curl https://내주소/api/local-keys`로 키를 가져간다** |

> **배포 후 반드시 그 주소를 직접 열어 `{"keys":{}}`인지 눈으로 확인할 것.**

### `.gitignore` — 제일 먼저 만든다

```gitignore
.env
.env.local
!.env.example
.venv/
__pycache__/
*.py[cod]
node_modules/
static/
dist/
*.tsbuildinfo
```

### `.env` — 비밀키 4개

```bash
ENVIRONMENT=development

# AI 키 (로컬 개발 전용, 최소 하나. 둘 다 넣으면 화면에서 골라 씀)
# ⚠️ 배포할 때는 반드시 비워두세요. 접속자 누구나 가져갈 수 있습니다.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Supabase (10단계부터)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

---

## 10. 배포·운영 파트

### 왜 2단계(맨 앞)에서 배포하나

**배포는 처음에 반드시 한 번 막힌다.** 마지막 날로 미루면 "다 만들었는데 못 보여주는" 사태가 난다.
껍데기 상태로 한 번 올려두면 이후에는 `git push`만으로 갱신된다.

### 필요한 외부 서비스 4곳

| # | 서비스 | 언제 붙이나 | 왜 |
|---|---|---|---|
| 1 | AI 회사 1곳 이상 | 3단계 | 글을 쓰는 주체. 하나만 있어도 동작 |
| 2 | GitHub | 2단계 | 코드 보관 + 배포 연결 |
| 3 | Render | 2단계 | 인터넷에 띄우기 |
| 4 | Supabase | 10단계 | 작성 이력 저장 |

### 빌드 파이프라인

```
1. npm run build           (frontend/)  →  static/ 에 결과물
2. pip install -e .        (루트)
3. uvicorn policy_writer.server:app --host 0.0.0.0 --port $PORT
```

FastAPI 한 대가 `static/`(화면)과 `/api`(서버)를 **같이** 서빙한다.

### Render 환경변수

```
ENVIRONMENT=production      ← 🔴 반드시. 빠지면 키가 공개된다
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENAI_API_KEY=             ← 비워둔다
ANTHROPIC_API_KEY=          ← 비워둔다
```

### ④ 배포 완료 확인

- [ ] **남의 폰으로** Render 주소에 들어가 화면이 뜬다
- [ ] `/api/info`에 `"environment": "production"`
- [ ] `/api/local-keys`가 `{"keys":{}}` — 🔴 이걸 눈으로 확인
- [ ] `/write`를 새로고침해도 화면이 뜬다

---

## 11. 만드는 순서 — 14단계 / 31시간

**하루 12시간이면 3일.**

> **1차 완료 기준: 6단계 끝.**
> `/write`에서 폼을 채우고 버튼을 누르면 **축사 본문이 화면에 보인다.**
> 그 전에는 8종·hwpx·이력·자동작성을 시작하지 않는다.

### 1일차 (11h) — 인터넷 주소에서 축사가 나온다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 1 | 준비 — 폴더 · `.gitignore` · `pyproject` · `config.py` · `server.py` | 1h | `localhost:8010/health` → `{"status":"ok"}` |
| 2 | **화면 뼈대 + 배포** ★ | 3h | **남의 폰으로** Render 주소 접속 성공<br>`/api/info`에 `"environment":"production"` |
| 3 | AI 연결(2사) + 키 검증 + 설정 화면 | 2.5h | 키 넣고 [연결 시험] → "정상"<br>틀린 키 → **"인증 실패"라고 이유가 뜬다** |
| 4 | **모델 카탈로그 + `GET /api/models` + 모델 드롭다운** ★ | 1.5h | 회사를 바꾸면 모델 목록·비용이 바뀐다 |
| 5 | 프롬프트 L1·L2·L3 + `builder.py` (**8종 표 + persona_block**) | 3h | Python으로 `/api/speech/draft` 호출 시 6단 축사가 나온다<br>(PowerShell JSON 금지 — 12장 함정 13) |

### 2일차 (12h) — 기능이 전부 동작한다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 6 | 작성 화면 (`speechFields.ts` 14칸 전부 → 화면) | 3h | **★ 1차 완료:** 폼 채우고 버튼 → 축사가 화면에 나온다 |
| 7 | 다운로드 (md + hwpx) | 2h | 한글파일을 받아 **한글 프로그램에서 열린다.** 파일명 안 깨짐 |
| 8 | **유형 8종 연결 + 유형별 검증** ★ | 2h | 8개 버튼이 다 동작하고, 유형마다 톤이 다르다 |
| 9 | 파일 올려서 자동 작성 | 3h | PDF 하나 올리고 버튼 → 축사가 나온다<br>**원본에 없는 날짜·인명이 없다** |
| 10 | Supabase + 작성 이력 (`llm_meta` 포함) | 2h | `/history`에 목록이 뜨고 다시 열린다<br>**Supabase를 꺼도 축사 생성은 된다** |

### 3일차 (8h) — 남에게 보여줄 수 있다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 11 | 품질검사 + 오류 화면 + 모바일 | 2h | 키 지우고 [작성] → **"설정에서 키를 넣어주세요"** |
| 12 | **모델 등급별 비교 실측** ★ | 1h | 같은 축사를 5개 모델로 돌려 표를 만든다 (아래) |
| 13 | 글 품질 다듬기 (유형 4종 × L2 수정) | 3h | 만든 글을 보고 **"손보면 쓰겠다"**는 생각이 든다 |
| 14 | 재배포 + README + 화면 사진 | 2h | 배포 주소에서 처음부터 끝까지 된다<br>`/api/local-keys`가 빈 응답 ★ |

---

### 12단계가 포트폴리오의 핵심이다

같은 축사를 5개 모델로 돌리고 표를 만든다. **원본 앱에 없는 데이터다.**

```
| 회사      | 등급   | 모델                        | 글자수 | 소요 | 1건당 | 6단 | 분량준수 |
|-----------|--------|-----------------------------|--------|------|-------|-----|----------|
| OpenAI    | 경제형 | gpt-4o-mini                 |   729  |  4초 |   2원 |  ✅ |   49%    |
| OpenAI    | 표준형 | gpt-5.6-terra               |        |      |  36원 |     |          |
| OpenAI    | 최상위 | gpt-5.6-sol                 | 1,459  | 16초 |  64원 |  ✅ |   97%    |
| Anthropic | 경제형 | claude-haiku-4-5            |        |      |  16원 |     |          |
| Anthropic | 표준형 | claude-sonnet-4-5-20250929  |        |      |  48원 |     |          |
```

**5칸 중 2칸은 이미 찼다.** 12단계는 나머지 3칸을 채우는 일이다.
Anthropic 2칸은 키가 있어야 채울 수 있다. 없으면 OpenAI 3칸만 채우고 그대로 낸다.

#### 이미 확인된 것 — `[실측]` 2026-09-05

같은 축사(목표 1,500자, 고급 칸 전부 채움):

| 모델 | 글자수 | 시간 | 자기소개 | 통계 40% | 금지어 |
|---|---|---|---|---|---|
| `gpt-4o-mini` | 729 | 4초 | 이름 없음 | 있음 | 지킴 |
| `gpt-5.6-sol` | **1,459** | 16초 | 장관 김민수 | 있음 | 지킴 |

**mini의 분량 미달은 서로 다른 시험에서 두 번 확인됐다.**

| 시험 | 목표 | 실제 | 달성률 |
|---|---|---|---|
| ① 원본 앱에서 | 2,400자 | 약 1,000자 | 42% |
| ② 이 표 | 1,500자 | 729자 | 49% |

**목표를 올려도 실제 글자수는 700~1,000자에서 멈춘다. 모델 한계이지 프롬프트 문제가 아니다.**
같은 프롬프트로 Sol은 1,459/1,500(97%)을 냈다.

**대응 순서**
1. 작성에 Sol(또는 표준형 이상)을 쓴다 → **화면 기본 등급을 최상위로**
2. L2 분량 환산표를 강하게 쓴다
3. 그래도 모자라면 `max_completion_tokens`를 올리거나 단을 나눠 두 번 호출한다

---

### 유형별 관찰 — `[실측]`

| 유형 | 관찰 | 목표 → 실제 |
|---|---|---|
| 축사 | 가장 표준. 4단이 두꺼움 | — |
| 기념사 | 의의·유공자 감사 강조 | — |
| 신년사 | 새해·내부 직원 대상 | — |
| **격려사** | 짧고 노고 인정 | **900 → 826 (제일 잘 맞음)** |
| **환영사** | 외빈 호명, 매우 짧게 | **600 → 667** |
| 개회사 | 행사 개시 + 협조 요청 | — |
| 이임사 | 회고·당부. `만감이 교차` 금지어는 지킴 | — |
| 서면축사 | `안녕하십니까` 없이 시작. **끝 서명은 종종 빠짐** | — |

---

### 시간이 모자라면 자를 순서

| 순서 | 자를 것 | 자른 뒤에도 남는 것 |
|---|---|---|
| 1 | 11단계 모바일 대응 | 컴퓨터에서는 정상 |
| 2 | 9단계 자동 작성 | 폼으로 직접 쓰는 건 됨 |
| 3 | 10단계 이력 화면 | 저장은 됨, 화면만 없음 |
| 4 | 4단계 모델 선택 → **회사별 기본 모델 1개 고정** | 축사는 그대로 나옴 |
| 5 | 7단계 hwpx | md로 대체 |

### 🔴 절대 자르면 안 되는 것 3가지

| | 항목 | 왜 |
|---|---|---|
| ① | **2단계 배포** | 링크가 없으면 보여줄 수가 없다 |
| ② | **11단계 오류 화면** | 데모 도중 깨지면 그걸로 끝이다 |
| ③ | **13단계 글 품질 3시간** | 글이 별로면 만든 의미가 없다 |

---

## 12. 함정 20개 요약표

### 🔴 보안 (2개)

| # | 함정 | 대응 |
|---|---|---|
| 1 | `ENVIRONMENT`가 빠지면 `/api/local-keys`가 AI 키를 공개한다 | 배포 후 그 주소를 직접 열어 `{"keys":{}}` 확인 |
| 2 | 모델 id를 헤더에서 그대로 믿으면 안 된다 | `catalog.resolve()`를 반드시 거친다 |

### 🟠 안 하면 반드시 막히는 것 (11개)

| # | 함정 | 내용 |
|---|---|---|
| 3 | `temperature` 400 | Claude 5 계열·OpenAI GPT-5/5.6/6 계열은 **보내면 400**. `catalog`의 플래그로 분기. **의심스러우면 안 보낸다** |
| 4 | OpenAI 출력 길이 | Chat Completions는 `max_completion_tokens`. `max_tokens`는 deprecated이고 추론 모델에서 안 먹는다 |
| 5 | 기본 회사 | 원본 기본값은 `gemini`. **서버·화면 두 곳 다** `openai`로 바꿔야 한다. 안 그러면 첫 요청이 401 |
| 6 | SPA 라우트 순서 | `@app.get("/{full_path:path}")`가 `include_router`보다 먼저 오면 `/api` 요청이 전부 HTML을 받는다 |
| 7 | 한글 파일명 | `filename="..."`이면 깨진다. RFC 5987 (`filename*=UTF-8''`)을 쓴다 |
| 8 | HWPX | `add_paragraph()`와 `save_to_path()`만. 표·이미지는 파일이 깨진다 |
| 9 | Vite 빌드 위치 | `build.outDir`을 `'../static'`으로. 기본값이면 FastAPI가 못 찾는다 |
| 10 | 포트 8000 | 윈도우에서 자주 잡혀 있다. **8010**을 쓰고 Vite 프록시도 8010으로 |
| 11 | `.env` 재시작 | `get_settings()`가 `@lru_cache`다. `.env`를 고치면 **서버를 껐다 켜야** 한다 |
| 12 | 한글 텍스트 파일 | `utf-8 → cp949 → euc-kr` 순서로 시도 |
| 13 | PowerShell 한글 | `ConvertTo-Json`으로 한글을 보내면 깨져서 AI가 `???`를 쓴다. **Python이나 파일로 보낼 것** |
| — | API 파일 추가 | `api/__init__.py`와 `server.py` **둘 다** 고쳐야 한다. 한쪽만 하면 404 |

> **Gemini를 빼서 사라진 함정 3개** — `thinkingBudget=0` 안 넣으면 빈 응답 / 2.5·3.x `thinkingLevel` 섞으면 400 / 모델 id가 URL 경로.
> 원본 코드를 읽다가 Gemini 부분이 나오면 **그냥 넘어가면 된다.**

### 🟡 원본이 실제로 저지른 실수 — 따라 하지 말 것 (7개)

| # | 원본의 실수 | 이 프로젝트에서는 |
|---|---|---|
| 14 | `build_press_prompt`를 만들어 놓고 **아무도 안 부른다** | 만들면 **그 자리에서 연결** |
| 15 | `_resolve_user_key`가 **3벌**, JSON 파서가 **2벌** | `common/`에 1벌씩만 |
| 16 | `os.environ.get()`과 `get_settings()`를 **섞어 쓴다** | **`get_settings()`만** 쓴다 |
| 17 | README에 **없는 엔드포인트**가 적혀 있다 | 문서에 쓰기 전에 **코드를 연다** |
| 18 | 설정 화면 제목은 "기본 사용 모델"인데 실제로는 **회사**를 고른다 | 이름과 동작을 맞춘다 (회사/모델을 분리) |
| 19 | `callApi`는 키 헤더만 붙이고 `X-LLM-Provider`는 화면마다 따로 붙인다 | `callApi`가 **세 헤더를 다** 붙인다 |
| 20 | 저장 실패를 `except: pass`로 삼킨다 | `save_warning`으로 알려준다 |

### ⚫ 문서는 코드보다 빨리 낡는다

`[실측]` 2026-09-05 하루 만에 원본 백엔드에 **13,944줄이 추가**됐고(주석 위주), 총량이 **5,618 → 19,355줄**이 됐다.
같은 날 **모델 id도 바뀌어 있었다.**

| 위치 | 예전 | 지금 |
|---|---|---|
| 기본 OpenAI 모델 | `gpt-4o-mini` | **`gpt-5.6-sol`** |
| 출력 길이 필드 | `max_tokens` | **`max_completion_tokens`** |
| temperature | 전송함 | **전송 안 함** |

**모델 id와 가격은 문서에서 가장 빨리 썩는 부분이다.** `catalog.py` 맨 위에 확인 날짜를 주석으로 박아둔다.

---

## 13. 로컬 실행법 (윈도우)

```powershell
cd C:\내프로젝트

# 최초 1회
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
cd frontend; npm install; cd ..
copy .env.example .env
# .env 에 키 채우기
# Supabase SQL 은 대시보드에서 001_init.sql 실행

# 매번
.\run.ps1
```

**확인**

- `http://localhost:8010/health` → `{"status":"ok"}`
- `http://localhost:5173` → 홈 화면
- `/settings`에서 회사 · 모델 · 키 설정

### 축사 생성 시험

> 🔴 **PowerShell `ConvertTo-Json`은 한글이 깨진다.** AI가 `???`를 받아서 이상한 글을 쓴다.
> **Python 스크립트나 JSON 파일로 보낼 것.**

```
POST http://localhost:8010/api/speech/draft

Header:
  X-LLM-Provider: openai
  X-LLM-Model:    gpt-5.6-sol
  X-OpenAI-Key:   sk-...

Body:
  { "input": { "event_name": "...", "event_type": "축사", ... } }
```

---

## 14. 완료 판정 체크리스트

### 1차 완료 (6단계 끝) — 여기까지가 최소 목표

- [ ] `/write`에서 14칸을 채우고 버튼을 누르면 **축사 본문이 화면에 나온다**
- [ ] 결과에 6단 구조가 보인다 (호명 → 의의 → 예우 → 정책 → 당부 → 마무리)
- [ ] 결과 화면에 모델·소요시간·비용이 표시된다

### 전체 완료 (14단계 끝)

**기능**

- [ ] 유형 8개가 다 동작하고, 유형마다 톤이 다르다
- [ ] 마크다운·한글파일 다운로드가 되고, hwpx가 한글 프로그램에서 열린다
- [ ] PDF를 올려 자동 작성이 된다
- [ ] `/history`에 이력이 남고 다시 열린다

**견고함**

- [ ] 키가 없어도 앱이 안 깨지고 안내가 뜬다
- [ ] Supabase를 꺼도 축사 생성은 된다
- [ ] 틀린 모델 id를 보내면 400, 틀린 키면 401이 각각 다른 메시지로 뜬다

**보안 🔴**

- [ ] 배포 주소의 `/api/local-keys`가 `{"keys":{}}`
- [ ] `/api/info`가 `"environment": "production"`
- [ ] git 이력에 `.env`가 없다

**포트폴리오**

- [ ] 모델 5개 비교표에 최소 3칸이 채워져 있다
- [ ] 남의 폰으로 배포 주소에 들어가 처음부터 끝까지 된다
- [ ] 만든 글을 보고 "손보면 쓰겠다"는 생각이 든다

---

## 부록 — 한 장 요약 (README 맨 위에 넣을 것)

```
[브라우저 :5173]
  홈 → 작성
  폼   : SpeechInput 14칸 전부 (발화자·청중·통계·참석자·persona_block 포함)
  설정 : 회사 2사(OpenAI·Anthropic) + 등급 + 1건당 원화 표시
  헤더 : X-LLM-Provider · X-LLM-Model · X-{회사}-Key

[서버 :8010]
  server.py 가 라우터 4개를 꽂는다 (원본은 9개)
  catalog.resolve(provider, model)          ← 허용목록 검증. 없으면 400
  build_speech_prompt(L1+L2+L3 / L4+persona+L5) → call_llm(model_meta) → 글
  temperature 는 model_meta["temperature"] 가 True 일 때만 보낸다
  common/ 에 키 꺼내기 · JSON 파싱 · 품질검사를 1벌씩

[기틀]
  6단 (서면축사만 4단)
  유형 8종은 "어느 단을 두껍게" 표 하나로 처리
  템플릿은 DB 가 아니라 prompts/l2_domain.py 에

[모델]
  OpenAI    경제형 gpt-4o-mini  / 표준형 gpt-5.6-terra / 최상위 gpt-5.6-sol
  Anthropic 경제형 claude-haiku-4-5 / 표준형 claude-sonnet-4-5-20250929
  Anthropic 최상위는 비워 둠 (검증 못 함)
  ⚠️ 목록에 없는 id 를 지어내지 말 것

[외부]
  AI 회사 1곳 이상 · GitHub · Render · Supabase = 4곳
  비밀키 4개 · 모델 5개 · API 11개 · 화면 4개 · 표 1개

[포트폴리오 무기]
  같은 축사를 모델별로 돌린 비교표
  확인된 것: mini 729자(4초, 2원) / Sol 1,459자(16초, 64원) — 약 32배 차이
```
