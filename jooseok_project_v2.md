# jooseok_project

클로드(또는 다른 코딩 에이전트)에게 이 저장소를 통째로 이해시키고,
비슷한 새 프로젝트를 만들 때 붙여 넣는 **구조 설명서**다.

- 원본 프로젝트: `gov-writer` (로컬 폴더 `gov-writer_example`), v0.8.0
- 내가 만들 것: **말씀자료 1종 계열 · 유형 8개** (축사·기념사·신년사·격려사·환영사·개회사·이임사·서면축사)
- **＋ 사용자가 AI 모델까지 고를 수 있게 한다** (7장)
- 보도자료·설명자료는 만들지 않는다
- 페르소나 **저장소**(`/personas`)는 만들지 않는다. 폼의 `persona_block` 칸은 남긴다
- 한 줄 정의: **행사 정보를 넣으면 AI가 말씀자료를 써주고 한글파일로 받는 웹앱**
- 1차 완료: **`/write`에서 축사 한 편이 화면에 나오는 것** (그다음 8종·다운로드·이력)
- 목표: **31시간 / 하루 12시간이면 3일** (13장). 시간이 없으면 13장의 자르는 순서를 따른다
- **비밀(API 키, .env 값)은 이 파일에 넣지 말 것.**

### 이 키로 이미 확인한 모델 (2026-09-05)

| 회사 | 등급 | 모델 | 결과 |
|---|---|---|---|
| OpenAI | 경제형 | `gpt-4o-mini` | ✅ 동작. 같은 축사 **729자** (목표 1,500) |
| OpenAI | 최상위 | `gpt-5.6-sol` | ✅ 동작. 같은 축사 **1,459자**. `temperature` 보내면 400. `max_completion_tokens` 필요 |
| OpenAI | 표준형 | `gpt-5.6-terra` | ⬜ 미호출 (문서상 존재) |
| Anthropic | 전부 | — | ⬜ **키가 없어 하나도 호출 못 함** |

**검증 안 한 id는 목록에 넣지 않는다.** 그래서 이렇게 됐다.

- `gpt-6-astra` — 뺐다
- **Anthropic 최상위 — 자리를 비웠다.** 키가 생기면 `claude-opus-4-5`를 한 번 호출해 보고 추가한다
- 최종: **OpenAI 3등급 + Anthropic 2등급 = 5개**

### 표시 규칙

| 표시 | 뜻 |
|---|---|
| `[코드확인]` | 원본 코드를 직접 열어 확인함 (파일:줄 표기) |
| `[실측]` | 직접 돌려 보고 눈으로 확인함 |
| `[조사]` | 공급사 공식 문서를 확인함 (2026-09-05 기준) |
| (표시 없음) | 설계 판단·의견 |

> 이 구분이 중요한 이유: 원본 `README.md`를 그대로 옮긴 부분에서 오류가 났었다.
> **확인한 것과 옮긴 것을 섞지 않는다.**

---

## 0. 클로드에게 시키는 방법

이 파일을 새 대화에 통째로 넣고 이렇게 말한다.

```
아래 jooseok_project.md 는 내가 분석한 원본 앱의 구조다.
이 구조를 따라가되, 내 프로젝트는 [여기에 주제] 다.

문서는 말씀자료 1종 계열만 만든다. 유형은 8개(축사·기념사·신년사·격려사·
환영사·개회사·이임사·서면축사)이고, 6단 기틀 하나를 공유한다.
보도자료·설명자료·RAG·페르소나 저장소·단락 재생성은 만들지 않는다.
persona_block 은 SpeechInput 선택 칸으로 남긴다 (저장소만 없음).

SpeechInput 칸은 6.2표 전부를 화면에 만든다. 8장의 짧은 예시를 칸 목록의 전부로 보지 마라.

모델 최상위는 gpt-5.6-sol 이다. gpt-6-astra 는 넣지 마라.
Anthropic 표준은 원본이 쓰는 claude-sonnet-4-5-20250929 다.
Anthropic 최상위는 만들지 마라 (검증 못 함). Anthropic 은 2등급, OpenAI 는 3등급이다.
허용 목록은 7장의 catalog.py 를 글자 그대로 따른다.
목록에 없는 id 를 추측하지 마라. claude-opus-4-1 같은 id 를 지어내지 마라.

사용자가 AI 회사와 모델 등급을 고를 수 있어야 한다 (7장).
모델 허용 목록은 서버가 갖고, 화면은 그걸 받아서 그린다.

키는 브라우저 헤더로만 보내고 서버에 저장하지 마라.
1차 완료는 /write 에서 축사가 나오는 시점이다.
13장의 순서대로 진행하고, 각 단계의 '완료 확인'을 통과한 뒤 다음으로 넘어가라.
```

---

## 1. 만들 것

행사 정보를 폼에 넣으면 **AI가 부처 6단 기틀에 맞춰 말씀자료를 쓰고**, 마크다운·한글파일로 내려받는 웹앱.

### 문서 유형 8개 — 기틀은 하나

| 유형 | 화면 라벨 | 키 | 두껍게 할 단 |
|---|---|---|---|
| 1 | 축사 | `chuksa` | **4단** (기본) |
| 2 | 기념사 | `gyenyeomsa` | 2단 |
| 3 | 신년사 | `sinnyeonsa` | 5단 |
| 4 | 격려사 | `gyeoryeosa` | 5단 |
| 5 | 환영사 | `hwanyeongsa` | 1단 |
| 6 | 개회사 | `gaehoesa` | 2+3단 |
| 7 | 이임사 | `iimsa` | 3+5단 |
| 8 | 서면축사 | `seomyeonchuksa` | **4단 구조로 교체** |

> **8개가 거의 공짜인 이유**: 1~7번은 **같은 6단 기틀**을 쓰고 어느 단을 두껍게 할지만 다르다.
> L2에 표 한 개를 더 쓰고, 화면에 버튼 8개를 배열로 정의하면 끝난다.
> 서면축사만 4단이라 L2에 별도 문단이 필요하다.

### 화면 4개

```
/            홈 (시작 카드)
/write       작성 폼 + 결과
/history     작성 이력
/settings    AI 회사 · 모델 · 키 설정
```

### 안 만드는 것

| 안 만듦 | 이유 |
|---|---|
| 보도자료 · 설명자료 | 문서 계열을 늘리면 L1~L3를 통째로 새로 써야 함 (+5h) |
| RAG · 공공데이터 | **외부 서비스 2곳을 끌고 옴.** 승인 대기도 있음 |
| 페르소나 저장소 (`/personas`) | 없어도 글은 나옴. **폼의 `persona_block` 칸은 남긴다** |
| 단락 재생성 · 말투 조정 | 있으면 좋지만 없어도 됨 |

> 다만 **함수 이름은 `build_speech_prompt`로 둔다.** 나중에 보도자료를 붙일 때
> 옆에 `build_press_prompt`를 만들기만 하면 되고, 지금 추가 비용은 **0시간**이다.

---

## 2. 기술 스택

| 층 | 무엇 |
|---|---|
| 화면 | React + TypeScript + Vite + Tailwind + lucide-react + react-router-dom |
| 서버 | Python 3.10+, FastAPI, uvicorn |
| AI | **OpenAI 3등급 + Anthropic 2등급 = 5개 모델** (7장). Google Gemini는 쓰지 않는다 |
| DB | Supabase (PostgreSQL). 없어도 글 생성은 됨. 이력만 안 남음 |
| 파일 읽기 | pypdf, python-docx, hwpx(ZIP 파싱) |
| 파일 쓰기 | markdown, python-hwpx |
| 실행 (윈도우) | `run.ps1` — 백엔드 **8010**, 프론트 5173 |
| 배포 | Render. Vite가 `static/`에 빌드하면 FastAPI가 그 폴더와 `/api`를 같이 서빙 |

`[코드확인]` `pyproject.toml`은 `requires-python = ">=3.10"`. 개발 PC에 깔린 건 3.12지만 하한선은 3.10이다.

`[실측]` 이 PC는 8000번이 다른 프로그램에 잡혀 있어 **백엔드는 8010**이다. 원본 `README.md`의 8000은 옛 숫자다.

### 필요한 외부 서비스 — 4곳

| # | 서비스 | 언제 | 왜 |
|---|---|---|---|
| 1 | **AI 회사 1곳 이상** | 3단계 | 글을 쓰는 주체. 하나만 있어도 동작 |
| 2 | **GitHub** | 2단계 | 코드 보관 + 배포 연결 |
| 3 | **Render** | 2단계 | 인터넷에 띄우기 |
| 4 | **Supabase** | 10단계 | 작성 이력 저장 |

### 비밀키 — 4개

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

`[코드확인]` 원본에 있는 `SUPABASE_ANON_KEY`는 뺀다. **코드가 한 번도 읽지 않는다** (`config.py` 밖 참조 0회).

---

## 3. 폴더 구조

```
policy_writer/
├── run.ps1                      윈도우에서 서버+화면 같이 켜기
├── .env / .env.example
├── .gitignore                   ★ 첫 커밋 전에
├── pyproject.toml
├── README.md
├── jooseok_project.md           이 파일
├── frontend/
├── src/policy_writer/
├── supabase/migrations/
└── static/                      Vite 빌드 결과 (깃 무시)
```

### 서버

```
src/policy_writer/
├── server.py          앱 조립. uvicorn이 가리키는 곳
├── config.py          .env → Settings 상자 하나 (lru_cache)
│
├── prompts/           ★ 결과 품질을 정하는 곳
│   ├── l1_identity.py   L1_SPEECH        상수
│   ├── l2_domain.py     L2_SPEECH        상수 ★8종 표
│   ├── l3_rules.py      L3_SPEECH        상수
│   └── builder.py       SpeechInput + build_l4/l5 + build_speech_prompt
│
├── llm/
│   ├── catalog.py     ★ 모델 허용 목록 (7장) — 원본에 없는 파일
│   └── client.py      call_llm(provider, model, ...)
│
├── api/
│   ├── settings.py    키 검증 + 모델 목록
│   ├── speech.py      말씀자료 작성
│   ├── download.py    md · hwpx
│   └── drafts.py      작성 이력
│
├── common/            ★ 원본에 없는 폴더 (4.4)
│   ├── keys.py        resolve_user_key(), norm_provider()
│   ├── parsing.py     parse_json_response()
│   └── quality.py     check_output()
│
├── extractors/files.py
├── exporters/converters.py
└── db/drafts.py
```

원본에 있지만 **안 만드는 것**: `rag/`, `policy_api/`, `api/explain.py`, `api/refine.py`, `api/personas.py`, `db/personas.py`

### 화면

```
frontend/src/
├── main.tsx
├── App.tsx                  라우트 4개
├── routes/
│   ├── HubPage.tsx
│   ├── WritePage.tsx        폼 (300줄 넘기지 말 것)
│   ├── ResultPage.tsx
│   ├── HistoryPage.tsx
│   └── SettingsPage.tsx     회사 + 모델 + 키
├── components/
│   ├── Field.tsx            입력칸 1개
│   └── FormSection.tsx
├── hooks/useLLMSettings.ts  localStorage (회사 + 모델)
├── lib/api.ts               모든 요청의 창구
├── lib/speechFields.ts      ★ 폼 칸 정의를 데이터로 (8장)
└── lib/speech-data.ts       유형 8종·청중·분량·직급 상수
```

### `.gitignore` — 제일 먼저

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

> **`.env`를 먼저 막고 시작한다.** 키가 한 번 GitHub에 올라가면 지워도 기록에 남는다.

---

## 4. 서버 방 배치

### 4.1 `server.py`

- `app = FastAPI(...)`, `get_settings()`
- CORS(개발일 때 5173 허용)
- 라우터 4개를 `include_router`
- `GET /health`, `GET /api/info`
- 배포 시 `static/`의 React를 서빙

`[코드확인]` **SPA 폴백 라우트(`@app.get("/{full_path:path}")`)는 반드시 모든 `include_router` 뒤에 둔다.** 순서가 바뀌면 `/api/...` 요청이 전부 `index.html`을 받는다.

### 4.2 `config.py`

`[코드확인]` `get_settings()`는 `@lru_cache`라서 프로세스가 켜진 동안 **한 번만** 읽는다. **`.env`를 고치면 서버를 재시작해야 한다.**

`local_llm_keys` 프로퍼티: production이면 빈 dict. development면 값이 있는 키만. `GET /api/local-keys`가 이걸 브라우저에 준다. **운영에서 절대 켜지 말 것** (14장 함정 1번).

### 4.3 `api/__init__.py`

`[코드확인]` 새 API 파일을 추가하면 **`api/__init__.py`의 import/`__all__` + `server.py`의 `include_router`** 둘 다 고쳐야 한다. **한쪽만 하면 404.**

| export | 파일 | prefix |
|---|---|---|
| `speech_router` | `api/speech.py` | `/api/speech` |
| `download_router` | `api/download.py` | `/api/download` |
| `drafts_router` | `api/drafts.py` | `/api/drafts` |
| `settings_router` | `api/settings.py` | (주소마다 다름) |

원본은 9개다. 5개를 안 만든다.

### 4.4 `common/` — 원본에 없는 폴더 ★

`[코드확인]` 원본의 문제: **같은 코드가 여러 벌 있다.**

| 중복 | 원본 | 내 프로젝트 |
|---|---|---|
| `_resolve_user_key` | **3벌** (`speech.py`·`press.py`·`explain.py`) | `common/keys.py` **1벌** |
| JSON 파서 | **2벌** | `common/parsing.py` **1벌** |

문서 종류를 늘릴 때마다 복사가 늘어나는 구조다. **처음부터 한 곳에 모은다.**

---

## 5. 요청 하나의 일생

1. React가 폼을 `SpeechInput` 모양 JSON으로 만든다
2. 헤더에 키와 **모델**을 싣는다
   ```
   X-LLM-Provider: openai
   X-LLM-Model:    gpt-4o-mini      ← ★ 새 헤더 (7장)
   X-OpenAI-Key:   sk-...
   ```
3. `POST /api/speech/draft`
4. FastAPI가 JSON 검사. `event_name` 없으면 **400**
5. `resolve_user_key()`가 헤더에서 키를 꺼냄. 없으면 **401**
6. **`catalog.resolve(provider, model)`** — 허용 목록에 없는 모델이면 **400** ★
7. `build_speech_prompt(input, contexts)` → `(system_prompt, user_prompt)`
8. `call_llm(provider, model, api_key, system_prompt, user_prompt, ...)` → 글 한 덩어리
9. `check_output()` — 빈 응답·너무 짧음을 **경고로** 담음 (막지는 않음)
10. `create_draft(...)` 시도. **실패해도 글은 버리지 않는다**
11. 응답: `{ generated_text, char_count, draft_id, warnings, meta }`
    - `meta` = `{ provider, model, elapsed_ms, input_tokens, output_tokens, cost_usd }` ★

---

## 6. 프롬프트 5층 — 이 프로젝트의 머리 ★

**5층인데 파일은 3개다.** L1~L3은 안 변하는 글이라 파일에 저장하고, L4~L5는 요청마다 새로 만드니 함수다.

```
┌ 시스템 프롬프트 — 매번 똑같음 → 파일 ────────────┐
│ L1  l1_identity.py   너는 누구다                  │
│ L2  l2_domain.py     6단 기틀 · 8종 표 · 정형구   │  ★핵심
│ L3  l3_rules.py      작성 절차 · 출력 형식        │
└───────────────────────────────────────────────────┘
┌ 유저 프롬프트 — 요청마다 다름 → 함수 ────────────┐
│ L4  build_l4_speech()   업로드한 행사계획서       │
│ L5  build_l5_speech()   이번 행사 정보            │
└───────────────────────────────────────────────────┘
```

```python
def build_speech_prompt(input, *, contexts=None):
    system_prompt = "\n\n".join([L1_SPEECH, L2_SPEECH, L3_SPEECH])

    user_parts = []
    l4 = build_l4_speech(contexts)      # 참고자료가 있을 때만
    if l4:
        user_parts.append(l4)
    if input.persona_block.strip():     # 저장소 없이 폼 값만
        user_parts.append(input.persona_block.strip())
    user_parts.append(build_l5_speech(input))
    user_prompt = "\n\n---\n\n".join(user_parts)

    return system_prompt, user_prompt
```

`[코드확인]` 원본은 L4와 L5 **사이에** `persona_block`을 끼운다. **저장소는 없어도 이 조각은 그대로 둔다.** 값이 빈 문자열이면 끼우지 않는다.

> **★ 만든 함수는 그 자리에서 창구에 연결한다.**
> `[코드확인]` 원본은 `build_press_prompt`를 만들어놓고 **어떤 파일도 부르지 않는다.**
> `api/press.py` 전체를 검색해도 `builder`·`build_press_prompt`가 한 건도 안 나온다.

### 6.1 L2 — 6단 기틀

구두용 7종 공통:

| 단 | 역할 | 분량 |
|---|---|---|
| 1 | 호명·인사 | 5~10% |
| 2 | 행사 의의 | 10~15% |
| 3 | 감사·예우 | 10~15% |
| 4 | 정책·사례 (첫째/둘째/셋째) | 50~60% |
| 5 | 당부 | 5~10% |
| 6 | 마무리 | 5~10% |

**서면축사만 4단** (인사 약식 → 의의 → 정부 의지 → 기대+서명). `안녕하십니까` 같은 구두 인사를 쓰면 안 된다.

여기에 **1장의 8종 표**, **정형구 사전**, **직급별 톤**, **분량 환산표**를 넣는다.

```
1단 호명   "존경하는 [청중] 여러분, 반갑습니다"
2단 의의   "오늘 「[행사명]」을 맞이하여..."
3단 예우   "이 자리를 빛내 주신 [참석자]을 비롯한 모든 분께 감사드립니다"
6단 마무리 "다시 한번 [축하]를 드리며, [기원]합니다. 감사합니다"

직급별   장관 굳건히·흔들림 없이 / 차관 차질없이·철저히
        국장 체계적으로·내실 있게 / 과장 함께·꾸준히

분량     1분 280자 · 3분 850 · 5분 1,400 · 7분 2,000 · 10분 2,800
```

문체: 경어체 `~습니다 / ~겠습니다`. 한 문장 80자 안. 입력에 없는 숫자는 만들지 말 것.

### 6.2 `SpeechInput` 필드

`[코드확인]` 파일: `prompts/builder.py`

| 필드 | 타입 | 기본 | 뜻 |
|---|---|---|---|
| `event_name` | str | (필수) | 행사명. 비면 400 |
| `event_type` | str | `"축사"` | 8종 **한글 라벨** (키 아님) |
| `event_date` | str | `""` | 날짜 문자열 |
| `event_location` | str | `""` | 장소 |
| `speaker_name` | str | `""` | 이름 |
| `speaker_role` | str | `""` | `장관`/`차관`/`실장·국장`/`과장·팀장`/`기관장` |
| `speaker_organization` | str | `""` | 소속 |
| `audience` | str | `""` | 쉼표로 이은 한글 청중 |
| `vip_list` | list[str] | `[]` | 참석자. 직급 순 |
| `target_chars` | int | `1400` | 목표 글자수 (화면 표준은 1500) |
| `key_messages` | list[str] | `[]` | 반드시 본문에 넣을 메시지 |
| `quotes_or_anecdotes` | list[str] | `[]` | 쓸 수 있는 통계·일화 |
| `avoid_phrases` | list[str] | `[]` | 이번 건 금지어 |
| `persona_block` | str | `""` | 말투·자주 쓰는 표현. **저장소 없이 폼에만** |

`[실측]` 이 칸에 “현장에서 답을 찾겠습니다”를 넣으면 본문에 그대로 나온다. 빼면 빠진다.

`[코드확인]` 화면 분량 상수 (`speech-data.ts`):

| 키 | 라벨 | 글자수 |
|---|---|---|
| `very_short` | 매우 짧게 | 600 |
| `short` | 짧게 | 900 |
| `standard` | 표준 | 1500 |
| `long` | 길게 | 2400 |
| `very_long` | 매우 길게 | 3500 |
| `custom` | 사용자 지정 | 300~5000 |

`[코드확인]` 청중 키 10개: `public_servant`, `citizen`, `expert`, `student`, `honoree`, `foreign_guest`, `industry`, `media`, `internal_staff`, `local_resident`

**API로 보낼 때는 키가 아니라 한글 라벨**을 합친다. 예: `"유공자, 공무원"`. `event_type`도 `"기념사"`.

---

## 7. 모델 선택 ★ (원본에 없는 기능)

`[코드확인]` 원본은 **회사만** 고를 수 있다. 모델 id는 코드에 박혀 있다.

```
client.py:436   "model": "claude-sonnet-4-5-20250929"
client.py:684   "model": "gpt-5.6-sol"
frontend/src    grep -rli "model" → 결과 없음    ← 화면에 모델 개념 자체가 없음
```

> 원본은 Google Gemini도 지원한다 (`client.py:546`). **내 프로젝트는 Gemini를 빼고 2사만 쓴다.**
> 빼면서 같이 사라지는 것: `GEMINI_API_KEY`, `X-Gemini-Key` 헤더, `gw_llm_key_gemini`,
> 그리고 **함정 3개**(`thinkingBudget`, 3.x `thinkingLevel`, 모델 id가 URL 경로).

`[코드확인]` `SettingsPage.tsx:122`의 제목은 **"기본 사용 모델"**인데, 그 아래 버튼 3개는 실제로는 **회사**를 고른다. 이름과 동작이 어긋나 있다.

### 7.1 이 기능이 어려운 진짜 이유

**모델마다 요청 모양이 다르다.** 회사가 달라서가 아니라, **같은 회사 안에서도 모델마다 다르다.**

`[조사]` 2026-09-05 기준:

| 걸림돌 | 내용 |
|---|---|
| **`temperature`** | 최신 추론 모델은 **보내면 HTTP 400**. Claude 5 계열, OpenAI GPT-5/5.6/6 계열이 그렇다 |
| 출력 길이 필드 | OpenAI Chat Completions는 `max_completion_tokens` (`max_tokens`는 deprecated). Anthropic은 `max_tokens` |
| 시스템 프롬프트 위치 | Anthropic은 **본문 최상위 `system`**, OpenAI는 **`messages[0]`에 `role:"system"`** |

**6개 중 4개가 `temperature`를 거부한다.** Gemini를 뺐더니 이 비율이 더 높아졌다 — Gemini는 세 등급 모두 받았기 때문이다. **분기는 선택이 아니라 필수다.**

`[코드확인]` **원본은 이미 이 문제를 반쯤 겪었다.** `_call_openai`는 `temperature` 인자를 받지만 **본문에 넣지 않는다** (`client.py:654`). 모델을 `gpt-5.6-sol`로 올리면서 그 필드를 통째로 뺀 것이다.

### 7.2 해결 규칙 — 의심스러우면 안 보낸다

```
temperature 를 보낼지 말지 확신이 없으면 → 안 보낸다
  안 보내면  → 모델 기본값으로 동작 (항상 안전)
  잘못 보내면 → HTTP 400 (요청 실패)
```

**비대칭이다.** 안 보내서 생기는 손해는 "온도 조절을 못 함"이고, 보내서 생기는 손해는 "앱이 안 돌아감"이다.

### 7.3 허용 목록은 서버가 갖는다

```python
# src/policy_writer/llm/catalog.py

# 확인일: 2026-09-05. id·가격은 바뀐다. 목록에 없는 모델을 추측하지 말 것.
# OpenAI 경제/최상위는 이 키로 [실측]. 표준형 terra는 문서상 존재, 이 키로는 미호출.
# Anthropic은 키가 없어 전부 미호출. 원본 client.py 의 sonnet-4-5 를 표준으로 둔다.
# Anthropic 최상위는 비워 뒀다 — 이유는 아래 주석 참고.
MODELS = {
    "openai": [
        {"id": "gpt-4o-mini",     "tier": "경제형", "temperature": True,
         "in": 0.15, "out": 0.60},   # [실측] 동작. 축사 729/1500
        {"id": "gpt-5.6-terra",   "tier": "표준형", "temperature": False,
         "in": 2.00, "out": 12.00},  # [조사] 문서. 400이면 gpt-4o 로 바꿔도 됨
        {"id": "gpt-5.6-sol",     "tier": "최상위", "temperature": False,
         "in": 4.00, "out": 20.00},  # [실측] 동작. 축사 1459/1500
    ],
    "anthropic": [
        {"id": "claude-haiku-4-5",              "tier": "경제형", "temperature": True,
         "in": 1.00, "out": 5.00},
        {"id": "claude-sonnet-4-5-20250929",    "tier": "표준형", "temperature": True,
         "in": 3.00, "out": 15.00},  # 원본 client.py 와 같은 id. temperature 를 보내고 동작함
        # 최상위 없음 — Anthropic 키가 없어 검증 못 했다.
        # 키가 생기면 claude-opus-4-5 ($5/$25) 를 한 번 호출해 보고,
        # 200 이 오면 그때 이 줄을 추가한다. 검증 전에는 넣지 않는다.
    ],
}

DEFAULTS = {"openai":    "gpt-4o-mini",
            "anthropic": "claude-sonnet-4-5-20250929"}

DEFAULT_PROVIDER = "openai"   # ★ 원본 기본값은 "gemini"였다. 반드시 바꿀 것

def resolve(provider: str, model: str | None) -> dict:
    """허용 목록에서 찾는다. 없으면 400."""
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

> **왜 서버가 목록을 갖나?**
> 헤더는 사용자가 마음대로 바꿀 수 있다. 목록이 화면에만 있으면 아무 문자열이나 실어 보낼 수 있고,
> 그러면 **의도치 않게 비싼 모델**이 불리거나 없는 모델로 400이 난다.

> **★ 기본 회사를 반드시 바꿀 것.**
> `[코드확인]` 원본은 기본 회사가 **`gemini`** 다 — 서버(`speech.py:398` `Header("gemini")`)와 화면(`useLLMSettings.ts:33` `stored ?? 'gemini'`) 양쪽에 박혀 있다.
> Gemini를 빼면 **키가 없는 회사가 기본값**이 되어 첫 요청이 401로 죽는다. 두 곳 다 `openai`로 바꾼다.

`[조사]` 위 5개 모델의 가격은 **2026-09-05 공식 문서 기준**이다. **가격과 모델 id는 바뀐다.** `catalog.py` 맨 위에 확인 날짜를 주석으로 박아둘 것.

`[실측]` `gpt-5.6-sol`에 `temperature: 0.7`을 보내면 HTTP 400
(`Only the default (1) value is supported`). `max_tokens`도 거부하고
`max_completion_tokens`만 받는다. 같은 계열(`gpt-5.6-terra`)은 문서상 동일 취급.
**의심스러우면 안 보낸다** (7.2). `gpt-6-astra`는 이 문서의 필수 목록에서 뺐다.

### 7.4 `call_llm`에 `model`을 받는다

```python
async def call_llm(
    *,
    provider: str,
    model_meta: dict,          # ★ catalog.resolve()가 돌려준 것
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> tuple[str, dict]:         # (글, meta)
```

회사별 본문 조립:

```python
# ── Anthropic ──
body = {
    "model": model_meta["id"],
    "max_tokens": max_tokens,
    "system": system_prompt,
    "messages": [{"role": "user", "content": user_prompt}],
}
if model_meta["temperature"]:
    body["temperature"] = temperature
# 안 받는 모델(Claude 5 계열)은 필드를 아예 안 넣는다

# ── OpenAI ──  출력 길이 필드 이름이 다르다
body = {
    "model": model_meta["id"],
    "max_completion_tokens": max_tokens,       # ⚠️ max_tokens 아님
    "messages": [{"role": "system", ...}, {"role": "user", ...}],
}
if model_meta["temperature"]:
    body["temperature"] = temperature
```

### 7.5 `GET /api/models`

화면이 목록을 서버에서 받아 그린다. 목록이 두 벌이 되지 않게 한다.

```json
{
  "openai": [
    {"id": "gpt-4o-mini",   "tier": "경제형", "won_per_doc": 2},
    {"id": "gpt-5.6-terra", "tier": "표준형", "won_per_doc": 36},
    {"id": "gpt-5.6-sol",   "tier": "최상위", "won_per_doc": 64}
  ],
  "anthropic": [
    {"id": "claude-haiku-4-5",           "tier": "경제형", "won_per_doc": 16},
    {"id": "claude-sonnet-4-5-20250929", "tier": "표준형", "won_per_doc": 48}
  ]
}
```

`won_per_doc`은 **1건당 대략 얼마인지**를 서버가 계산해 내려준다 (아래 7.6). 사용자에게 `$0.000123` 같은 숫자는 의미가 없다.

### 7.6 1건당 비용 — 화면에 이렇게 보인다

말씀자료 1건 = 입력 약 4,000토큰(L1~L5) + 출력 약 1,500토큰(1,500자) 기준, 1달러 1,400원.

| 회사 | 등급 | 모델 | `temp` | 1건당 | 검증 |
|---|---|---|:---:|---:|---|
| OpenAI | 경제형 | `gpt-4o-mini` | ✅ | **약 2원** | **[실측]** 동작 |
| Anthropic | 경제형 | `claude-haiku-4-5` | ✅ | 약 16원 | `[조사]` 미호출 |
| OpenAI | 표준형 | `gpt-5.6-terra` | ❌ | 약 36원 | `[조사]` 미호출 |
| Anthropic | 표준형 | `claude-sonnet-4-5-20250929` | ✅ | 약 48원 | 원본 코드가 쓰는 id, 미호출 |
| OpenAI | 최상위 | `gpt-5.6-sol` | ❌ | **약 64원** | **[실측]** 동작 |

계산식: `입력 4,000 × in/1M + 출력 1,500 × out/1M`, 1달러 1,400원.
예) sonnet-4-5 = 4,000×$3/1M + 1,500×$15/1M = $0.0345 → **48원**

**가장 싼 것(mini 2원)과 이 키로 확인한 최상위(Sol 64원)는 약 32배.** 화면에 보여주는 것만으로도 쓸 만하다.

> **Anthropic 최상위는 목록에 없다.** 키가 없어 아무것도 호출해 보지 못했기 때문이다.
> Anthropic 3칸 중 2칸만 열고, 키가 생기면 `claude-opus-4-5`를 한 번 호출해 본 뒤 추가한다.
> **검증 안 한 id를 목록에 넣지 않는다** — 이 문서의 규칙이다.

### 7.7 화면

```
설정 화면
┌─────────────────────────────────────┐
│ AI 회사                             │
│  [OpenAI ✓]  [Anthropic]            │  ← 키가 있는 회사만 활성
│                                     │
│ 모델 등급                           │
│  ○ 경제형   gpt-4o-mini    약 2원   │
│  ● 표준형   gpt-5.6-terra  약 36원  │
│  ○ 최상위   gpt-5.6-sol    약 64원  │
└─────────────────────────────────────┘
```

localStorage 키 (원본 4개 + 신규 1개):

```
gw_llm_provider          "openai"                 [코드확인] 원본에 있음 (기본값만 바꿈)
gw_llm_key_openai        sk-...                   [코드확인]
gw_llm_key_anthropic     sk-ant-...               [코드확인]
gw_llm_model_openai      "gpt-5.6-sol"            ★ 신규 — 회사별로 따로 기억
gw_llm_model_anthropic   "claude-sonnet-4-5-20250929"  ★ 신규
```

`[코드확인]` 원본에 있는 `gw_llm_key_gemini`는 만들지 않는다. **이미 브라우저에 남아 있을 수 있으니** `clearAll()`에서 옛 키도 같이 지우는 게 안전하다.

**모델을 회사별로 따로 기억한다.** 회사를 바꿨다 돌아와도 고른 등급이 유지된다.

`[코드확인]` 원본 `lib/api.ts:37`의 `callApi`는 **키 헤더만** 붙이고 `X-LLM-Provider`는 안 붙인다. 각 화면 파일이 따로 붙이고 있다 (`SpeechWriter.tsx:184`). **내 프로젝트는 `callApi`가 provider·model·key 세 헤더를 모두 붙인다.**

---

## 8. 화면

`[코드확인]` 원본은 `WritePage.tsx`가 1,278줄, `SpeechWriter.tsx`가 1,423줄이다. 폼을 통째로 손으로 썼기 때문이다.

**내 프로젝트는 "어떤 칸이 있는지"를 목록으로 정의하고 화면이 그걸 읽어 그린다.**

```ts
// lib/speechFields.ts  — 6.2 SpeechInput 과 1:1. 이 목록이 화면의 전부다.
export const speechFields = [
  { key: 'event_name',            label: '행사명',        type: 'text',   required: true },
  { key: 'event_type',            label: '행사 유형',      type: 'select', options: EVENT_TYPES },
  { key: 'event_date',            label: '일시',          type: 'text' },
  { key: 'event_location',        label: '장소',          type: 'text' },
  { key: 'speaker_name',          label: '이름',          type: 'text' },
  { key: 'speaker_role',          label: '직급',          type: 'select', options: SPEAKER_ROLES },
  { key: 'speaker_organization',  label: '소속 기관',      type: 'text' },
  { key: 'audience',              label: '청중',          type: 'multiselect', options: AUDIENCES },
  { key: 'target_chars',          label: '분량',          type: 'select', options: LENGTHS },
  { key: 'key_messages',          label: '핵심 메시지',    type: 'list' },
  { key: 'quotes_or_anecdotes',   label: '인용할 통계·일화', type: 'list' },
  { key: 'avoid_phrases',         label: '피할 표현',      type: 'list' },
  { key: 'vip_list',              label: '주요 참석자',    type: 'list' },
  { key: 'persona_block',         label: '페르소나(선택)', type: 'textarea' },
]
```

`audience`는 화면에서 키를 고르고, API로 보낼 때 **한글 라벨을 쉼표로 합친다.**
`event_type`도 키(`chuksa`)가 아니라 라벨(`축사`)을 보낸다.

**목표: 화면 파일 하나가 300줄을 안 넘게.**

`[코드확인]` 키 형식 검사 (`useLLMSettings.ts:17-20`): openai `/^sk-/`, anthropic `/^sk-ant-/`

> ⚠️ **검사 순서에 주의.** Anthropic 키(`sk-ant-...`)도 `/^sk-/`를 통과한다. 회사별로 따로 검사하므로 원본 구조에서는 문제없지만, 하나의 정규식으로 합치지 말 것.

---

## 9. API 계약

공통 헤더:

```
X-LLM-Provider: openai | anthropic          (기본값 openai)
X-LLM-Model:    <catalog에 있는 id>          ★ 신규. 없으면 회사 기본값
X-OpenAI-Key | X-Anthropic-Key
```

| 메서드 | 주소 | 본문 | 단계 |
|---|---|---|---|
| POST | `/api/speech/draft` | `{ input: SpeechInput, reference_texts, max_tokens, temperature }` | 5 |
| POST | `/api/speech/draft-with-docs` | multipart: `input_json`, `plan_file`, `reference_files` | 9 |
| POST | `/api/speech/auto-draft` | 행사계획서 파일만으로 폼 추정 후 작성 | 9 |
| POST | `/api/download/speech/md` | `{ title, generated_text }` | 7 |
| POST | `/api/download/speech/hwpx` | 〃 | 7 |
| GET | `/api/models` | — | 4 |
| POST | `/api/validate-key` | `{ provider, api_key }` | 3 |
| GET | `/api/local-keys` | — (development만) | 3 |
| GET | `/api/drafts` | `?limit=20` | 10 |
| GET / DELETE | `/api/drafts/{id}` | — | 10 |
| GET | `/health` · `/api/info` | — | 1 |

**총 11개.** 원본은 20개가 넘는다.

응답:

```json
{
  "generated_text": "존경하는 ...",
  "char_count": 1459,
  "draft_id": "uuid 또는 null",
  "warnings": [],
  "meta": {
    "provider": "openai", "model": "gpt-5.6-sol",
    "elapsed_ms": 16300,
    "input_tokens": 3980, "output_tokens": 1500,
    "cost_won": 64
  }
}
```

`meta`를 결과 화면에 그대로 보여준다. **어떤 모델로 얼마 걸려 얼마 썼는지**가 보이는 것만으로 완성도가 달라진다.

> `[코드확인]` 원본 `README.md`는 `/api/refine/auto-extract`라고 적고 있는데 **그런 엔드포인트는 없다.**
> 실제 `refine.py`에 있는 건 `/regenerate-paragraph`, `/adjust-tone`, `/extract-event-info`, `/extract-persona` 4개다.
> **원본 README를 그대로 믿지 말 것.**

---

## 10. 파일 읽기 / 쓰기

### 읽기 (`extractors/files.py`)

`[코드확인]` **실제로 글자를 뽑는 건 4종뿐이다.**

| 형식 | 동작 |
|---|---|
| `txt` | ✅ utf-8 → cp949 → euc-kr 순서로 시도 |
| `pdf` | ✅ pypdf, 최대 20페이지 |
| `docx` | ✅ python-docx |
| `hwpx` | ✅ ZIP을 열어 `Contents/section*.xml`의 `<hp:t>` 노드 |
| **`hwp`** | ❌ `"HWPX로 변환 후 업로드 부탁드립니다"` 문자열만 반환 |
| **`doc` `ppt` `pptx`** | ❌ `"현재 텍스트 추출 미지원"` 문자열만 반환 |

> **실패해도 예외를 던지지 않고 안내 문자열을 돌려준다.** 이 문자열이 그대로 프롬프트에 실려 들어갈 수 있다. **창구에서 `(...미지원)`으로 시작하는지 확인할 것.**

파일당 최대 5,000자로 자른다.

### 쓰기 (`exporters/converters.py`)

`[코드확인]` python-hwpx는 단순한 것만 쓴다.

```python
from hwpx import HwpxDocument
doc = HwpxDocument.new()
doc.add_paragraph("...")        # 이것만
doc.save_to_path(임시파일경로)   # 이것만
```

표·이미지·도형은 시도하면 파일이 깨진다.

`[코드확인]` 한글 파일명 (안 하면 깨진다):

```python
from urllib.parse import quote
headers = {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}
```

`[코드확인]` 단락 분할: AI 출력은 빈 줄로 단락이 나뉜다. `re.split(r"\n\s*\n+", text.strip())`로 나누고, 단락 안의 단일 줄바꿈은 공백으로 합친다.

---

## 11. DB

없어도 서버는 뜬다. **저장만 실패한다.**

`[코드확인]` `db/drafts.py`는 httpx로 Supabase REST를 직접 친다. **`supabase` SDK를 설치하지 않는다.**

```
POST  {SUPABASE_URL}/rest/v1/drafts
GET   {SUPABASE_URL}/rest/v1/drafts?order=created_at.desc&limit=20
```

헤더: `apikey`, `Authorization: Bearer {service_role_key}`, `Prefer: return=representation`

`[코드확인]` `SUPABASE_URL` 끝에 `/rest/v1/`를 붙이면 안 된다. 코드가 붙인다.

### 표 — 1개

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.drafts (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type     TEXT NOT NULL,           -- 축사 · 기념사 · ...
  title          TEXT NOT NULL,
  form_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_text TEXT,
  llm_meta       JSONB DEFAULT '{}'::jsonb,   -- ★ provider·model·비용·소요시간
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON public.drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_event_type ON public.drafts(event_type);

ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;
```

**`llm_meta`를 남기는 게 포인트다.** 나중에 "어느 모델이 분량을 잘 지켰나"를 이력에서 뽑을 수 있다.

`[코드확인]` 마지막 줄이 중요하다. 정책을 하나도 안 만들고 잠그면 외부에서는 아무도 못 읽고 서버의 `service_role` 키만 통과한다.

### 문서 템플릿은 DB에 넣지 않는다

`[코드확인]` 원본도 그렇다. 6단 기틀·정형구 사전은 전부 `prompts/l2_domain.py`에 있다.

| 코드에 둘 때 | DB에 둘 때 |
|---|---|
| git이 변경 이력을 기록 | 따로 만들어야 함 |
| **관리 화면 불필요** | **관리 화면 필수** |

### 저장 실패를 숨기지 않는다

`[코드확인]` 원본은 `except Exception: pass`로 삼킨다. 사용자는 저장이 안 된 걸 모른다.

> **내 프로젝트는 응답에 `save_warning`을 담는다.**

---

## 12. 보안 규칙

1. LLM 키는 **요청 헤더**. 서버 디스크·DB·로그에 저장 금지
2. `ENVIRONMENT=production`이면 `/api/local-keys` **빈 응답** (14장 함정 1번)
3. **모델 id는 서버 허용 목록으로 검증.** 헤더 값을 그대로 믿지 말 것 ★
4. 인용·통계는 사용자가 준 것만. 없으면 비우거나 "자료에 없음"
5. `SUPABASE_SERVICE_ROLE_KEY`는 **브라우저로 내보내지 말 것**
6. `SUPABASE_URL` 끝에 `/rest/v1/`를 붙이지 말 것
7. `.gitignore`를 **첫 커밋 전에** 만들 것

---

## 13. 만드는 순서 · 시간 · 완료 확인

**총 31시간. 하루 12시간이면 3일이다.**

**1차 완료 기준:** 6단계 끝. `/write`에 6.2칸을 채우고 버튼을 누르면 **축사 본문이 화면에 보인다.**
그 전에는 8종·hwpx·이력·자동작성을 시작하지 않는다.

### 1일차 (11h) — 인터넷 주소에서 축사가 나온다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 1 | 준비 — 폴더·`.gitignore`·`pyproject`·`config.py`·`server.py` | 1h | `localhost:8010/health` → `{"status":"ok"}` |
| 2 | **화면 뼈대 + 배포** ★ | 3h | **남의 폰으로** Render 주소에 들어가 화면이 뜸<br/>`/api/info`에 `"environment": "production"` |
| 3 | AI 연결 (2사) + 키 검증 + 설정 화면 | 2.5h | 키 넣고 [연결 시험] → "정상"<br/>틀린 키 → **"인증 실패"라고 이유가 뜸** |
| 4 | **모델 카탈로그 + `GET /api/models` + 모델 드롭다운** ★ | 1.5h | 회사를 바꾸면 모델 목록이 바뀌고 1건당 비용이 보임 |
| 5 | 프롬프트 L1·L2·L3 + `builder.py` (**8종 표 + persona_block**) | 3h | Python으로 `/api/speech/draft` 호출 시 6단 축사가 나옴 (PowerShell JSON 금지) |

### 2일차 (12h) — 기능이 전부 동작한다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 6 | 작성 화면 (`speechFields.ts` 6.2 전부 → 화면) | 3h | **1차 완료:** 폼 채우고 버튼 → 축사가 화면에 나옴 |
| 7 | 다운로드 (md + hwpx) | 2h | 한글파일을 받아 **한글 프로그램에서 열림.** 파일명 안 깨짐 |
| 8 | **유형 8종 연결 + 유형별 검증** ★ | 2h | 8개 버튼이 다 동작하고, 유형마다 톤이 다름 |
| 9 | 파일 올려서 자동 작성 | 3h | PDF 하나 올리고 버튼 → 축사가 나옴<br/>**원본에 없는 날짜·인명이 없음** |
| 10 | Supabase + 작성 이력 (`llm_meta` 포함) | 2h | `/history`에 목록이 뜨고 다시 열림<br/>**Supabase를 꺼도 축사 생성은 됨** |

### 3일차 (8h) — 남에게 보여줄 수 있다

| # | 단계 | 시간 | 완료 확인 |
|---|---|---:|---|
| 11 | 품질검사 3줄 + 오류 화면 + 모바일 | 2h | 키 지우고 [작성] → **"설정에서 키를 넣어주세요"** |
| 12 | **모델 등급별 비교 실측** ★ | 1h | 같은 축사를 5개 모델로 돌려 표를 만듦 (아래 15장) |
| 13 | 글 품질 다듬기 (유형 4종 × L2 수정) | 3h | 만든 글을 보고 **"손보면 쓰겠다"** 는 생각이 듦 |
| 14 | 재배포 + README + 화면 사진 | 2h | 배포 주소에서 처음부터 끝까지 됨<br/>`/api/local-keys`가 빈 응답 ★ |

### 왜 2단계에서 배포하나

**배포는 처음에 반드시 막힌다.** 마지막 날로 미루면 "다 만들었는데 못 보여주는" 사태가 난다. 껍데기로 한 번 올려두면 이후에는 `git push`만 하면 갱신된다.

### 12단계가 포트폴리오의 핵심이다

같은 축사를 5개 모델로 돌리고 표를 만든다. **원본 gov-writer에 없는 데이터다.**

```
행사: 청년 주거지원 정책 설명회 · 유형: 축사 · 목표 1,500자
(이미 채운 칸 — 15장 [실측])

  모델              실제 글자수    소요     1건당
  gpt-4o-mini           729자     4초      2원
  gpt-5.6-sol         1,459자    16초     64원
```

`[실측]` mini는 목표 2,400자여도 1,000자 근처에서 끊긴다.
**같은 프롬프트로 Sol은 1,459/1,500(97%)을 맞췄다.** 12단계는 이 표를 5칸까지 채우는 일이다.
목록에 없는 `gpt-6-astra`·`claude-opus-4-1`을 넣으려 하지 말 것.

### 시간이 모자라면 자를 순서

| 순서 | 자를 것 | 자른 뒤에도 남는 것 |
|---|---|---|
| 1 | 11단계 모바일 대응 | 컴퓨터에서는 정상 |
| 2 | 9단계 자동 작성 | 폼으로 직접 쓰는 건 됨 |
| 3 | 10단계 이력 화면 | 저장은 됨, 화면만 없음 |
| 4 | 4단계 모델 선택 → **회사별 기본 모델 1개 고정** | 축사는 그대로 나옴 |
| 5 | 7단계 hwpx | md로 대체 |

**절대 자르면 안 되는 것 3가지**

| | | 왜 |
|---|---|---|
| ① | **2단계 배포** | 링크가 없으면 보여줄 수가 없다 |
| ② | **11단계 오류 화면** | 데모 도중 깨지면 그걸로 끝이다 |
| ③ | **13단계 글 품질 3시간** | 글이 별로면 만든 의미가 없다 |

---

## 14. 함정 목록

### 🔴 보안

**1. `ENVIRONMENT`가 빠지면 AI 키가 공개된다**

`[코드확인]` `GET /api/local-keys`는 **인증 없이** `.env`의 AI 키를 브라우저에 내려준다. 막는 장치는 `ENVIRONMENT=production` **하나뿐**이다.

- `render.yaml`로 배포 → 값이 고정돼 있어 안전
- Render 대시보드에서 **수동 생성** → 기본값이 `development` → **누구나 `curl https://내주소/api/local-keys`로 키를 가져간다**

**배포 후 반드시 그 주소를 직접 열어 `{"keys":{}}` 인지 확인할 것.**

**2. 모델 id를 헤더에서 그대로 믿지 말 것** ★

`X-LLM-Model`은 사용자가 바꿀 수 있다. `catalog.resolve()`를 반드시 거친다.

### 🟠 안 하면 반드시 막히는 것

| # | 함정 | 내용 |
|---|---|---|
| **3** | `temperature` 400 ★ | `[조사]` Claude 5 계열·OpenAI GPT-5/5.6/6 계열은 **보내면 400**. `catalog`의 `temperature` 플래그로 분기. **의심스러우면 안 보낸다** |
| **4** | OpenAI 출력 길이 | `[조사]` Chat Completions는 `max_completion_tokens`. `max_tokens`는 deprecated이고 추론 모델에서는 안 먹는다 |
| **5** | 기본 회사 ★ | `[코드확인]` 원본 기본값은 **`gemini`** (`speech.py:398`, `useLLMSettings.ts:33`). Gemini를 뺐으면 **두 곳 다 `openai`로** 바꿔야 한다. 안 그러면 첫 요청이 401 |
| **6** | SPA 라우트 순서 | `@app.get("/{full_path:path}")`가 `include_router`보다 먼저 오면 `/api` 요청이 전부 HTML을 받는다 |
| **7** | 한글 파일명 | `filename="..."`로 하면 깨진다. RFC 5987(`filename*=UTF-8''`)을 쓴다 |
| **8** | HWPX | `add_paragraph()`와 `save_to_path()`만. 표·이미지는 파일이 깨진다 |
| **9** | Vite 빌드 위치 | `build.outDir`을 `'../static'`으로. 기본값이면 FastAPI가 못 찾는다 |
| **10** | 포트 8000 | `[실측]` 윈도우에서 자주 잡혀 있다. **8010**을 쓰고 Vite 프록시도 8010으로 |
| **11** | `.env` 재시작 | `[코드확인]` `get_settings()`가 `@lru_cache`다. `.env`를 고치면 **서버를 껐다 켜야** 한다 |
| **12** | 한글 텍스트 파일 | `utf-8 → cp949 → euc-kr` 순서로 시도 |
| **13** | PowerShell 한글 | `[실측]` `ConvertTo-Json`으로 한글을 보내면 깨져서 AI가 `???`를 쓴다. **Python이나 파일로 보낼 것** |

> **Gemini를 빼서 사라진 함정 3개** — `thinkingBudget=0` 안 넣으면 빈 응답, 2.5/3.x `thinkingLevel` 섞으면 400, 모델 id가 URL 경로.
> 원본을 읽다가 `client.py`의 Gemini 부분(`546`, `555`, `582`)이 나오면 **그냥 넘어가면 된다.**

### 🟡 원본이 실제로 저지른 실수 — 따라 하지 말 것

| # | 실수 | 내 프로젝트에서는 |
|---|---|---|
| **14** | `[코드확인]` `build_press_prompt`를 만들어놓고 **아무도 안 부른다** | 만들면 **그 자리에서 연결** |
| **15** | `[코드확인]` `_resolve_user_key`가 **3벌**, JSON 파서가 **2벌** | `common/`에 1벌만 |
| **16** | `[코드확인]` `os.environ.get(...)`과 `get_settings()`를 **섞어 쓴다** — pydantic이 `.env`를 Settings에만 넣으면 프로세스 환경변수에 없어 "미설정"이 된다 | **`get_settings()`만** 쓴다 |
| **17** | `[코드확인]` 원본 `README.md`에 **없는 엔드포인트**(`/api/refine/auto-extract`)가 적혀 있다 | 문서에 쓰기 전에 **코드를 연다** |
| **18** | `[코드확인]` `SettingsPage.tsx:122` 제목은 "기본 사용 모델"인데 실제로는 **회사**를 고른다 | 이름과 동작을 맞춘다 |
| **19** | `[코드확인]` `callApi`는 키 헤더만 붙이고 `X-LLM-Provider`는 화면마다 따로 붙인다 | `callApi`가 **세 헤더를 다** 붙인다 |
| **20** | 저장 실패를 `except: pass`로 삼킨다 | `save_warning`으로 알려준다 |

### ⚫ 문서는 코드보다 빨리 낡는다

`[실측]` 2026-09-05, 백엔드 36개 파일에 **13,944줄이 추가**됐다 (설명 주석 위주). 코드 총량이 **5,618줄 → 19,355줄**로 늘었다.

같은 날 **모델 id도 바뀌어 있었다.**

| 위치 | 예전 | 지금 |
|---|---|---|
| `client.py:684` | `gpt-4o-mini` | **`gpt-5.6-sol`** |
| `client.py:686` | `max_tokens` | **`max_completion_tokens`** |
| `client.py:654` | temperature 전송 | **전송 안 함** |

**모델 id와 가격은 문서에서 가장 빨리 썩는 부분이다.** `catalog.py` 맨 위에 확인 날짜를 주석으로 박아둘 것.

---

## 15. 실측 기록

`[실측]` 같은 기틀을 써도 유형에 따라 톤이 달라진다.

| 유형 | 관찰 | 목표 → 실제 |
|---|---|---|
| 축사 | 가장 표준. 4단이 두꺼움 | — |
| 기념사 | 의의·유공자 감사 강조 | — |
| 신년사 | 새해·내부 직원 | — |
| **격려사** | 짧고 노고 인정 | **900 → 826 (제일 잘 맞음)** |
| **환영사** | 외빈 호명, 매우 짧게 | **600 → 667** |
| 개회사 | 행사 개시 + 협조 | — |
| 이임사 | 회고·당부. `만감이 교차` 금지어는 지킴 | — |
| 서면축사 | `안녕하십니까` 없이 시작. **끝 서명은 종종 빠짐** | — |

**`[실측]` 분량은 모델에 따라 갈린다.**

같은 축사(목표 1,500자, 고급 칸 전부, 2026-09-05):

| 모델 | 글자수 | 시간 | 자기소개 | 통계 40% | 금지어 |
|---|---|---|---|---|---|
| `gpt-4o-mini` | 729 | 4초 | 이름 없음 | 있음 | 지킴 |
| `gpt-5.6-sol` | **1,459** | 16초 | 장관 김민수 | 있음 | 지킴 |

mini는 6단을 짧게 훑고 끝난다. Sol은 숫자 뒤에 이유·신청 현장까지 이어서 목표에 가깝다.
**화면 기본 최상위는 Sol.** 경제형만 쓰면 분량 불만이 다시 난다.

> **`[실측]` mini의 분량 미달은 두 번 확인했다 — 서로 다른 시험이다.**
>
> | 시험 | 목표 | 실제 | 달성률 |
> |---|---|---|---|
> | ① 원본 gov-writer에서 | 2,400자 | 약 1,000자 | 42% |
> | ② 이 문서 15장 표 | 1,500자 | 729자 | 49% |
>
> **목표를 올려도 실제 글자수는 700~1,000자에서 멈춘다.** 모델 한계이지 프롬프트 문제가 아니다.
> 같은 프롬프트로 Sol은 1,459/1,500(97%)을 냈다.

> 대응 순서:
> 1. 작성에 Sol(또는 표준형 이상)을 쓴다
> 2. L2 분량 환산표를 강하게 쓴다
> 3. 그래도 모자라면 `max_completion_tokens`를 올리거나 단을 나눠 두 번 호출한다

`[실측]` 이력 `draft_id`는 Supabase 미설정이면 계속 `null`.

### 채울 표 — 12단계에서

```
| 회사      | 등급   | 모델                        | 글자수 | 소요 | 1건당 | 6단 | 분량준수 |
|-----------|--------|-----------------------------|--------|------|-------|-----|----------|
| OpenAI    | 경제형 | gpt-4o-mini                 |  729   |  4초 |   2원 |  ✅  |   49%    |
| OpenAI    | 표준형 | gpt-5.6-terra               |        |      |  36원 |     |          |
| OpenAI    | 최상위 | gpt-5.6-sol                 | 1,459  | 16초 |  64원 |  ✅  |   97%    |
| Anthropic | 경제형 | claude-haiku-4-5            |        |      |  16원 |     |          |
| Anthropic | 표준형 | claude-sonnet-4-5-20250929  |        |      |  48원 |     |          |
```

**5칸 중 2칸은 이미 찼다.** 12단계는 나머지 3칸을 채우는 일이다.
Anthropic 2칸은 키가 있어야 채울 수 있다. 없으면 OpenAI 3칸만 채우고 그대로 낸다.

---

## 16. 로컬에서 켜는 법 (윈도우)

```powershell
cd C:\내프로젝트
# 최초 1회
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
cd frontend; npm install; cd ..
copy .env.example .env
# .env에 키 채우기. Supabase SQL은 대시보드에서 001_init.sql 실행

.\run.ps1
```

확인:

- `http://localhost:8010/health` → `status: ok`
- `http://localhost:5173` → 홈
- `/settings`에서 회사·모델·키 설정

`[실측]` 축사 생성 시험 — **PowerShell `ConvertTo-Json`은 한글이 깨진다. Python으로 보낼 것.**

```
POST http://localhost:8010/api/speech/draft
Header: X-LLM-Provider: openai
        X-LLM-Model:    gpt-5.6-sol
        X-OpenAI-Key:   sk-...
Body:   { "input": { "event_name": "...", "event_type": "축사", ... } }
```

---

## 17. 원본을 읽을 때 추천 순서

1. `config.py`
2. `server.py` + `api/__init__.py`
3. `llm/client.py` — `call_llm`만 먼저. **모델 id가 어디에 박혀 있는지** 확인
4. `prompts/l1_identity.py` → `l2_domain.py` → `l3_rules.py` → `builder.py`의 `SpeechInput`
5. `api/speech.py` ← **정본**
6. `frontend/src/lib/speech-data.ts` + `routes/SpeechWriter.tsx`
7. `frontend/src/routes/SettingsPage.tsx` ← 모델 선택이 왜 없는지 확인
8. `extractors/files.py`, `exporters/converters.py`, `api/download.py`
9. `db/drafts.py`

**안 읽어도 되는 것**: `api/press.py`, `api/explain.py`, `api/refine.py`, `api/personas.py`, `rag/`, `policy_api/`

---

## 18. 한 장 요약

```
[브라우저 5173]
  홈 → 작성
  폼: 6.2 SpeechInput 전부 (발화자·청중·통계·참석자·persona_block 포함)
  설정: 회사 2사(OpenAI·Anthropic) + 등급 3단계 + 1건당 비용 표시   ★
  요청 헤더: X-LLM-Provider · X-LLM-Model · X-{회사}-Key

[서버 8010]
  server.py가 창구 4개를 꽂음 (원본은 9개)
  catalog.resolve(provider, model)  ← 허용 목록 검증. 없으면 400   ★
  build_speech_prompt(L1+L2+L3 / L4 + persona + L5) → call_llm(model_meta) → 글
  최상위 모델 id = gpt-5.6-sol (이 키로 검증). gpt-6-astra·claude-opus-4-1 금지
  Anthropic 은 경제형·표준형 2등급만 (최상위는 검증 못 해서 비움)
  temperature 는 model_meta["temperature"] 가 True 일 때만 보냄     ★
  common/ 에 키 꺼내기·JSON 파싱·품질검사를 1벌씩

[기틀]
  6단 (서면축사만 4단) · 유형 8종은 "어느 단을 두껍게" 표 하나로 처리
  템플릿은 DB가 아니라 prompts/l2_domain.py 에

[외부]
  AI 회사 1곳 이상 · GitHub · Render · Supabase   = 4곳
  비밀키 4개 · 모델 5개 (OpenAI 3등급 + Anthropic 2등급)

[포트폴리오 무기]
  같은 축사를 모델별로 돌린 비교표 (13장 12단계)
  이미 확인: mini 729자 / Sol 1,459자. 1건당 약 2원 ~ 64원
```

**클로드에게: 정본은 말씀자료 경로다. 유형 8종은 L2의 표 하나로 처리하고, 모델은 7장 catalog 만 써라.**
**1차 완료는 /write 에서 축사가 나오는 것. 원본 README 보다 이 문서와 실제 코드를 우선하라.**
