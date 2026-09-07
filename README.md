# policy-writer

말씀자료 작성기 — 행사 정보를 넣으면 AI가 부처 6단 기틀에 맞춰 말씀자료를 쓰고, 한글파일(.hwpx)로 내려줍니다.

`gov-writer` v0.8.0에서 **말씀자료 계열만 떼어내 다시 만든 경량 버전**입니다.
문서 계열을 3종에서 1종으로 줄인 대신, 원본에 없던 기능을 하나 넣었습니다 —
**사용자가 AI 회사와 모델 등급까지 직접 고를 수 있고, 1건당 비용이 화면에 원 단위로 보입니다.**

**현재 버전**: v1.0.0

**배포 주소**: _(컨트롤러 확인 필요 — Render 서비스명이 `policy-writer`이므로 기본 주소는 `https://policy-writer.onrender.com`일 가능성이 높지만, 이 세션은 Render 대시보드에 접근할 수 없어 실제 주소를 확인하지 못했습니다. 확인 후 이 자리를 실제 링크로 바꿔 주세요.)_

---

## 원본과 무엇이 다른가

| 항목 | gov-writer v0.8.0 | **policy-writer** |
|---|---|---|
| 문서 계열 | 말씀자료 · 보도자료 · 설명자료 (3종) | **말씀자료 1종** |
| 문서 유형 | 축사·기념사 등 (기틀 미분리) | **8종 — 6단 기틀 하나를 공유** |
| **모델 선택** | 회사만 선택. 모델 id는 코드에 하드코딩 | **회사 + 등급 선택.** 허용목록을 서버가 검증 |
| **1건당 비용** | 안 보임 | **화면에 원 단위 표시** (약 2원 ~ 70원) |
| LLM 회사 | Anthropic · Gemini · OpenAI (3사) | **OpenAI · Anthropic (2사)** |
| API 엔드포인트 | 20개 이상 | **10개** |
| RAG · 공공데이터 | 있음 (pgvector + 정책브리핑) | 없음 |
| 페르소나 저장소 | 있음 (`/personas`) | 없음 — **폼의 `persona_block` 입력칸은 유지** |
| 공통 함수 | `_resolve_user_key` 3벌, JSON 파서 2벌 | **`common/`에 1벌씩** |
| 저장 실패 처리 | `except: pass` (사용자가 모름) | **`save_warning`으로 알림** |
| 백엔드 포트 | 8000 | **8011** (윈도우에서 8000이 자주 점유됨 — 8010·5173은 이 PC의 다른 프로젝트 전용이라 그보다 하나씩 올려 씀) |

---

## 주요 기능

### 📝 말씀자료 작성 — 유형 8종

행사 정보를 폼에 넣으면 AI가 부처 표준 **6단 기틀**에 맞춰 본문을 씁니다.

| 유형 | 두껍게 쓰는 단 | 유형 | 두껍게 쓰는 단 |
|---|---|---|---|
| 축사 | **4단** (기본형) | 환영사 | 1단 |
| 기념사 | 2단 | 개회사 | 2+3단 |
| 신년사 | 5단 | 이임사 | 3+5단 |
| 격려사 | 5단 | 서면축사 | **4단 구조로 교체** |

**6단 기틀** (구두용 7종 공통)

| 단 | 역할 | 분량 |
|---|---|---|
| 1 | 호명 · 인사 | 5~10% |
| 2 | 행사 의의 | 10~15% |
| 3 | 감사 · 예우 | 10~15% |
| 4 | **정책 · 사례** (첫째/둘째/셋째) | **50~60%** |
| 5 | 당부 | 5~10% |
| 6 | 마무리 | 5~10% |

- **서면축사만 4단**입니다 (인사 약식 → 의의 → 정부 의지 → 기대+서명). `안녕하십니까` 같은 구두 인사를 쓰지 않습니다.
- 직급별 톤 자동 적용 — 장관 `굳건히·흔들림 없이` / 차관 `차질없이·철저히` / 국장 `체계적으로·내실 있게` / 과장 `함께·꾸준히`
- 분량 6단계 (매우 짧게 600자 ~ 매우 길게 3,500자, 사용자 지정 300~5,000자)
- 청중 10종 · 발화자 페르소나 · 필수 메시지 · 인용할 통계 · 금지어를 각각 지정
- **입력에 없는 숫자·인명은 만들지 않습니다.**

### 🤖 AI 모델 선택 — 원본에 없는 기능

- 회사 2사 × 등급을 화면에서 고릅니다. 회사별로 마지막에 고른 등급을 따로 기억합니다.
- **1건당 예상 비용이 원 단위로 보입니다.** 가장 싼 등급(OpenAI 인턴, 2원)과 가장 비싼 등급(Anthropic 선임비서, 70원)이 약 **35배** 차이입니다.
- 모델 허용목록은 **서버가** 갖고, 화면은 `GET /api/models`로 받아 그립니다.
  헤더로 임의의 모델 id를 실어 보내도 400으로 막힙니다.
- 결과 화면에 **어떤 모델로 몇 초 걸려 얼마 썼는지**가 표시되고, 작성 이력에도 같이 저장됩니다.

### 📂 파일 업로드 자동 작성

- 행사계획서(PDF · DOCX · HWPX · TXT)를 올리면 AI가 폼을 추정해 바로 작성합니다.
- 파일당 5,000자까지 읽습니다. `.hwp`는 지원하지 않습니다 (HWPX로 변환 안내).

### 🗂 공통 기능

- **작성 이력** (`/history`) — 다시 열기, 모델·비용 함께 표시
- **다운로드** — Markdown (.md) + 한컴오피스 (.hwpx). 한글 파일명이 깨지지 않습니다
- **API 키는 서버가 보관** — `.env`(로컬) / Render 환경변수(배포)로 설정하고 서버가 직접 호출에 씁니다. 요청 헤더로 개인 키를 대신 실어 보낼 수도 있으며, 어느 쪽이든 서버 디스크·DB·로그에는 남기지 않습니다

### 화면

<!-- 컨트롤러가 배포 주소에서 찍어 docs/screenshots/ 에 넣는다. 그 전까지는 깨진 링크다. -->

| 홈 | 작성 |
|---|---|
| ![홈 화면](docs/screenshots/hub.png) | ![작성 화면](docs/screenshots/write.png) |

| 결과 | 설정 |
|---|---|
| ![결과 화면](docs/screenshots/result.png) | ![설정 화면](docs/screenshots/settings.png) |

---

## 지원 모델

**6개 — OpenAI 3등급 + Anthropic 3등급.**

| 회사 | 등급 | 모델 | `temperature` | 1건당 | 검증 상태 |
|---|---|---|:---:|---:|---|
| OpenAI | 인턴 | `gpt-4o-mini` | ✅ 보냄 | **약 2원** | ✅ 실측 (200 확인) |
| OpenAI | 비서 | `gpt-5.6-terra` | ❌ 안 보냄 | 약 32원 | ✅ 실측 (200 확인) |
| OpenAI | 선임비서 | `gpt-5.6-sol` | ❌ 안 보냄 | **약 56원** | ✅ 실측 (200 확인) |
| Anthropic | 인턴 | `claude-haiku-4-5` | ✅ 보냄 | 약 14원 | ✅ 실측 (200 확인) |
| Anthropic | 비서 | `claude-sonnet-4-5-20250929` | ✅ 보냄 | 약 42원 | ✅ 실측 (200 확인) |
| Anthropic | 선임비서 | `claude-opus-4-5-20251101` | ✅ 보냄 | 약 70원 | ✅ 실측 (200 확인) |

> **6개 모델 전부 이번 실측(2026-09-07, 아래 「모델 비교 실측」)에서 실제로 호출해 200을 확인했습니다.**
> **검증하지 않은 모델 id는 목록에 넣지 않는다** — 이 프로젝트의 규칙입니다.
>
> 위 표의 "1건당"은 아래 비용 계산식(고정 상수 3,000 / 1,400토큰)으로 미리 뽑아 두는 **추정치**입니다.
> 아래 「모델 비교 실측」 표의 "1건당"은 이번 실측 호출에서 실제로 오간 토큰으로 계산한 **실측치**라서,
> 모델마다 실제 생성 길이가 달라 두 표의 값이 서로 다릅니다 — 어느 한쪽이 틀린 게 아닙니다.

**비용 계산식** — 입력 3,000토큰(프롬프트 L1~L5, 실측 1,985~3,143) + 출력 1,400토큰(실측 416~1,912의 대표값), 1달러 1,400원 기준

```
1건당 원화 = (3,000 × 입력단가/1M + 1,400 × 출력단가/1M) × 1,400
```

### ⚠️ 모델마다 요청 모양이 다릅니다

회사가 달라서가 아니라, **같은 회사 안에서도 모델마다 다릅니다.**

| 차이 | 내용 |
|---|---|
| `temperature` | 최신 추론 모델은 **보내면 HTTP 400**. 6개 중 2개가 거부합니다 |
| 출력 길이 필드 | OpenAI는 `max_completion_tokens`, Anthropic은 `max_tokens` |
| 시스템 프롬프트 위치 | Anthropic은 본문 최상위 `system`, OpenAI는 `messages[0]` |

`llm/catalog.py`의 `temperature` 플래그로 분기합니다. **확신이 없으면 안 보냅니다** —
안 보내면 모델 기본값으로 동작하지만(안전), 잘못 보내면 요청 자체가 실패하기 때문입니다.

---

## 모델 비교 실측

같은 축사를 모델별로 돌려 만든 표입니다. (행사: 청년 주거지원 정책 설명회 · 유형: 축사 · 목표 1,500자)
6개 모델 전부 같은 조건으로 새로 호출했습니다 (2026-09-07, `scripts/compare_models.py`).

**전체 표**: [`docs/model-comparison.md`](docs/model-comparison.md) — 회사·등급·모델·글자수·소요시간·1건당 비용·분량 준수율.

6단 구성(호명·인사 → 행사 의의 → 감사·예우 → 정책·사례 → 당부 → 마무리) 여부는 자동으로 잴 수 없는 항목이라
표에서 뺐습니다 — 여섯 모델의 결과물(`docs/samples/`)을 모두 사람이 읽고 확인했고, 전부 구조를 갖췄습니다 (수동 확인).

**인턴 등급은 목표를 올려도 분량이 늘지 않습니다.** 서로 다른 두 시험에서 확인했습니다.

| 시험 | 목표 | 실제 | 달성률 |
|---|---|---|---|
| ① gov-writer에서 | 2,400자 | 약 1,000자 | 42% |
| ② 위 표 (`gpt-4o-mini`) | 1,500자 | 813자 | 54% |

**700~1,000자에서 멈춥니다. 모델 한계이지 프롬프트 문제가 아닙니다.**
같은 프롬프트로 선임비서 등급(`gpt-5.6-sol`)은 1,513/1,500(101%)을 냈습니다.
그래서 **설정 화면의 초기 선택값을 선임비서 등급으로** 둡니다.

---

## 아키텍처

- **백엔드**: Python 3.10+ / FastAPI (단일 프로세스)
- **프론트엔드**: React SPA (Vite + TypeScript + Tailwind + lucide-react + react-router-dom)
- **DB**: Supabase (PostgreSQL) — 표 1개. **없어도 글 생성은 됩니다** (이력만 안 남음)
- **호스팅**: Render (단일 인스턴스, 정적 파일 통합 서빙)
- **LLM**: OpenAI / Anthropic — **서버가 키를 보관하고 직접 호출** (요청 헤더로 개인 키를 대신 실어 보낼 수도 있음)
- **문서 변환**: python-hwpx (HWPX 생성) / pypdf · python-docx · ZIP 파싱 (입력 추출)

### 요청 흐름

```
[브라우저 :5174]
  폼 14칸  →  키·라벨 변환  →  lib/api.ts 가 헤더 부착
                                 X-LLM-Provider · X-LLM-Model · X-App-Password (항상)
                                 X-{회사}-Key (localStorage 에 값이 있을 때만 — 지금은 이 값을 넣는 화면이 없다)
        │
        ▼  개발: Vite 프록시 → :8011   /   배포: 같은 도메인 /api/*
[서버 :8011]
  ① require_app_password()   틀리거나 없으면 401 (APP_PASSWORD 자체가 비었거나
                              공백·비-ASCII 로 깨졌으면 503 — 운영자 설정 오류)
  ② Pydantic 검증            없으면 400
  ③ resolve_user_key()       헤더에 키가 없으면 서버 키(.env/Render)로 대체.
                              헤더·서버 키 둘 다 없으면 401
  ④ catalog.resolve()        허용목록 밖이면 400
  ⑤ build_speech_prompt()    L1+L2+L3 (시스템) / L4 + persona + L5 (유저)
  ⑥ call_llm(model_meta)     회사별 본문 조립. temperature 는 플래그가 True 일 때만
  ⑦ check_output()           빈 응답·분량 미달을 경고로만 담음 (막지 않음)
  ⑧ create_draft()           실패해도 글은 버리지 않음 → save_warning
        │
        ▼
[Supabase]  drafts 표 1개 (llm_meta 에 모델·비용·소요시간 기록)
```

### 프롬프트 5층 — 파일은 3개

L1~L3은 요청과 무관하게 항상 같은 글이라 **상수 파일**, L4~L5는 요청마다 달라지므로 **함수**입니다.

| 층 | 위치 | 내용 |
|---|---|---|
| L1 | `prompts/l1_identity.py` | 너는 누구다 |
| L2 | `prompts/l2_domain.py` | **6단 기틀 · 8종 표 · 정형구 사전 · 직급별 톤 · 분량 환산표** |
| L3 | `prompts/l3_rules.py` | 작성 절차 · 출력 형식 |
| L4 | `build_l4_speech()` | 업로드한 행사계획서 발췌 |
| — | `persona_block` | 폼에 적은 말투 (L4와 L5 **사이**에 삽입, 비어 있으면 생략) |
| L5 | `build_l5_speech()` | 이번 행사 정보 |

> 문서 템플릿은 **DB가 아니라 코드**(`l2_domain.py`)에 둡니다.
> git이 변경 이력을 기록해 주고, 관리 화면을 따로 만들 필요가 없습니다.

---

## API 엔드포인트

**총 12개.** AI 호출은 아래 헤더를 공통으로 받습니다.

```
X-LLM-Provider: openai | anthropic        (없으면 openai)
X-LLM-Model:    catalog 에 있는 id         (없으면 회사 기본값)
X-OpenAI-Key | X-Anthropic-Key            (없으면 서버 키로 대체. 서버 키도 없으면 401)
X-App-Password: 접속 암호                  (APP_PASSWORD 설정 시 필수 — AI 호출 +
                                            /api/drafts. 없거나 틀리면 401)
```

### 작성

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| POST | `/api/speech/draft` | 🔒 말씀자료 생성 (폼 입력) — `X-App-Password` 필요 |
| POST | `/api/speech/draft-with-docs` | 🔒 말씀자료 + 참고자료 첨부 (multipart) — `X-App-Password` 필요 |
| POST | `/api/speech/auto-draft` | 🔒 행사계획서 업로드 → 폼 추정 후 자동 생성 — `X-App-Password` 필요 |

### 다운로드

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| POST | `/api/download/speech/md` | Markdown |
| POST | `/api/download/speech/hwpx` | 한컴오피스 |

### 설정

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/api/models` | 회사별 모델 목록 + 등급 + 1건당 원화 |
| GET | `/api/local-keys` | `.env`의 로컬 키 (**development 전용**, production은 빈 응답) |
| GET | `/api/auth/required` | 접속 암호 필요 여부 (`misconfigured` 플래그로 서버 설정 오류도 알림) |
| POST | `/api/auth/check` | 입력한 접속 암호가 맞는지 확인 (AI 미호출) |

### 이력 · 관리

| 메서드 | 엔드포인트 | 설명 |
|---|---|---|
| GET | `/api/drafts` | 🔒 작성 이력 조회 (`?limit=20`) — `X-App-Password` 필요 |
| GET / DELETE | `/api/drafts/{id}` | 🔒 단건 조회 / 삭제 — `X-App-Password` 필요 |
| GET | `/health` · `/api/info` | 헬스체크 · 버전·환경 (암호 불필요) |

### 응답

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

### 상태코드

| 코드 | 언제 |
|---|---|
| 200 | 정상 (DB 저장 실패 포함 — `save_warning`으로 안내) |
| 400 | 필수값 누락 / 허용목록에 없는 모델 |
| 401 | 키 없음 / 키 틀림 / 접속 암호 틀림 |
| 502 · 504 | AI사 오류 / 120초 초과 |
| 503 | 서버 설정 문제 (접속 암호·API 키 형식이 서버에 잘못 설정됨) — 사용자 잘못이 아님 |

---

## 로컬 개발 셋업 (윈도우)

### 1. 최초 1회

```powershell
cd C:\policy_writer

py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"

cd frontend; npm install; cd ..

copy .env.example .env
# .env 에 키를 채웁니다
```

### 2. Supabase 초기화 (선택)

Supabase 대시보드 → SQL Editor → New query → `supabase/migrations/001_init.sql` 붙여넣기 → Run.

> 건너뛰어도 됩니다. 작성 이력만 저장되지 않고, 글 생성은 정상 동작합니다.

### 3. 실행

```powershell
.\run.ps1
```

| 주소 | 기대 결과 |
|---|---|
| `http://localhost:8011/health` | `{"status":"ok"}` |
| `http://localhost:5174` | 홈 화면 |
| `http://localhost:5174/settings` | 회사 · 모델 등급 설정 |

개발 시 Vite dev server(5174)가 `/api/*` 요청을 백엔드(**8011**)로 프록시합니다.

### 4. 회사·모델 등급 선택

브라우저에서 `/settings` 진입 → 회사(OpenAI / Anthropic) 선택 → 모델 등급 선택.
API 키는 `.env`(서버)에 이미 설정돼 있어 화면에는 키 관련 항목이 아예 없습니다 —
설정 화면은 "AI 회사" · "모델 등급" 두 섹션뿐입니다.
`APP_PASSWORD`를 설정했다면 접속 시 암호 입력 화면이 먼저 뜹니다.

> **⚠️ 커맨드라인으로 시험할 때**: PowerShell `ConvertTo-Json`은 한글을 깨뜨립니다.
> AI가 `???`를 받아 이상한 글을 씁니다. **Python 스크립트나 JSON 파일로 보내세요.**

---

## 환경변수

`.env.example` 참고. **비밀키는 5개**입니다.

```bash
ENVIRONMENT=development

# AI 키 — 서버가 이 키를 직접 들고 호출합니다. 최소 하나. 둘 다 넣으면 화면에서 골라 씁니다.
# ⚠️ 배포할 때도 값을 채우세요. 비우면 유료 라우트(말씀자료 생성 등)가 전부 401이 됩니다.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Supabase — 없어도 글 생성은 됩니다 (이력만 안 남음)
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=

# 접속 암호 — 서버 키 + 접속 암호 기능. 비워두면(로컬 개발 등) 암호 검사를 건너뜁니다.
# ⚠️ 배포할 때는 반드시 값을 채우세요. 비어 있으면 production에서 유료 라우트가 503으로 막힙니다.
# 영문·숫자·기호만 사용하세요. 한글 등은 HTTP 헤더로 전달할 수 없습니다.
APP_PASSWORD=
```

| 주의 | 내용 |
|---|---|
| 🔴 `ENVIRONMENT` | `production`이 아니면 `/api/local-keys`가 **인증 없이 AI 키를 공개합니다.** 배포 시 반드시 설정 |
| 🔴 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY` | **서버가 직접 호출에 씁니다.** 배포 환경에도 값이 있어야 합니다 — 비우면 로그인 이후 모든 생성 요청이 401 |
| 🔴 `APP_PASSWORD` | 비어 있으면 production에서 유료 라우트가 503. 앞뒤 공백·개행·비-ASCII 문자가 섞여도 (틀린 암호가 아니라) 503 "서버 설정 오류"로 알려줍니다 |
| 🟠 `.env` 수정 후 | 설정은 프로세스당 **한 번만** 읽습니다 (`@lru_cache`). 고치면 **서버를 껐다 켜세요** |
| 🟠 `SUPABASE_URL` | 끝에 `/rest/v1/`를 **붙이지 마세요.** 코드가 붙입니다 |
| — | `SUPABASE_ANON_KEY`는 사용하지 않습니다 |

---

## 운영 배포 (Render)

1. GitHub push → Render 자동 빌드·배포
2. Build Command: `pip install -e .` + `npm install` + `npm run build`
3. Vite가 `static/` 폴더에 빌드 산출물 출력 (`build.outDir: '../static'`)
4. FastAPI가 `static/index.html` + `/api/*`를 **한 프로세스에서** 서빙

`static/`은 `.gitignore`에 있어 커밋되지 않습니다 — Render가 매번 새로 빌드합니다.
배포 환경에서는 화면과 API가 같은 도메인이므로 **CORS가 필요 없습니다** (개발 모드에서만 활성화).

### Render 환경변수

```
ENVIRONMENT=production        ← 🔴 반드시. 빠지면 AI 키가 공개됩니다
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENAI_API_KEY=...            ← 🔴 채웁니다. 서버가 이 키로 직접 호출합니다 (비우면 401)
ANTHROPIC_API_KEY=...         ← 🔴 채웁니다. 서버가 이 키로 직접 호출합니다 (비우면 401)
APP_PASSWORD=...              ← 🔴 채웁니다. 비면 503, 앞뒤 공백이 섞여도 503
```

### 배포 직후 확인 3가지

| 주소 | 기대 결과 |
|---|---|
| `/api/local-keys` | `{"keys":{}}` ← 🔴 **눈으로 직접 확인** |
| `/api/info` | `"environment": "production"` |
| `/write` 새로고침 | 404가 아니라 화면이 뜸 (SPA 폴백 정상) |

---

## 폴더 구조

```
policy_writer/
├── run.ps1                          # 윈도우에서 서버+화면 같이 켜기
├── pyproject.toml
├── render.yaml                      # Render 자동 빌드 설정
├── .env.example
├── .gitignore                       # ★ 첫 커밋 전에 반드시
├── README.md                        # 이 파일
├── BUILD_GUIDE.md                   # 파트별 구축 설계서
│
├── src/policy_writer/               # 백엔드 (Python)
│   ├── server.py                    # FastAPI 엔트리포인트
│   ├── config.py                    # .env → Settings (lru_cache)
│   │
│   ├── prompts/                     # ★ 결과 품질을 정하는 곳
│   │   ├── l1_identity.py           #   L1 정체성
│   │   ├── l2_domain.py             #   L2 6단 기틀 · 8종 표 · 정형구
│   │   ├── l3_rules.py              #   L3 작성 절차 · 출력 형식
│   │   └── builder.py               #   SpeechInput + L4/L5 + 프롬프트 조립
│   │
│   ├── llm/
│   │   ├── catalog.py               # ★ 모델 허용목록 (원본에 없는 파일)
│   │   └── client.py                #   call_llm — 회사별 요청 모양 분기
│   │
│   ├── api/                         # 라우터 4개 (원본은 9개)
│   │   ├── speech.py                #   말씀자료 작성
│   │   ├── download.py              #   MD · HWPX
│   │   ├── drafts.py                #   작성 이력
│   │   └── settings.py              #   키 검증 · 모델 목록
│   │
│   ├── common/                      # ★ 공통 함수를 1벌씩만 (원본에 없는 폴더)
│   │   ├── keys.py                  #   resolve_user_key · norm_provider
│   │   ├── parsing.py               #   parse_json_response
│   │   └── quality.py               #   check_output
│   │
│   ├── extractors/files.py          # PDF · DOCX · HWPX · TXT 추출
│   ├── exporters/converters.py      # MD · HWPX 변환
│   └── db/drafts.py                 # Supabase REST (SDK 미사용)
│
├── frontend/                        # 프론트엔드 (React)
│   ├── package.json
│   ├── vite.config.ts               # outDir: '../static' · proxy → :8011
│   └── src/
│       ├── App.tsx                  # 라우트 4개
│       ├── routes/
│       │   ├── HubPage.tsx          #   홈
│       │   ├── WritePage.tsx        #   작성 폼 (300줄 이내)
│       │   ├── ResultPage.tsx       #   결과 + meta 표시
│       │   ├── HistoryPage.tsx      #   작성 이력
│       │   └── SettingsPage.tsx     #   회사 · 모델 · 키
│       ├── components/
│       │   ├── Field.tsx            #   입력칸 1개를 그리는 범용 컴포넌트
│       │   └── FormSection.tsx
│       ├── hooks/useLLMSettings.ts  # localStorage (회사 + 모델 + 키)
│       └── lib/
│           ├── api.ts               # ★ 요청 헤더 부착을 한 곳에서 관리 (Provider·Model·App-Password·조건부 개인키)
│           ├── speechFields.ts      # ★ 폼 칸 정의를 데이터로
│           └── speech-data.ts       # 유형 8종 · 청중 · 분량 · 직급 상수
│
├── supabase/migrations/
│   └── 001_init.sql                 # drafts 표 1개
│
└── static/                          # Vite 빌드 산출물 (.gitignore)
```

### 폼을 손으로 쓰지 않습니다

원본은 작성 화면 하나가 1,278줄, 다른 하나가 1,423줄입니다. 폼을 통째로 손으로 썼기 때문입니다.
이 프로젝트는 **"어떤 칸이 있는지"를 배열로 정의하고 화면이 읽어 그립니다.**

```ts
// lib/speechFields.ts — SpeechInput 14칸과 1:1. 이 배열이 화면의 전부입니다.
export const speechFields = [
  { key: 'event_name',  label: '행사명',   type: 'text',   required: true },
  { key: 'event_type',  label: '행사 유형', type: 'select', options: EVENT_TYPES },
  { key: 'audience',    label: '청중',     type: 'multiselect', options: AUDIENCES },
  // ... 14개
] as const
```

`Field.tsx`가 `text` / `textarea` / `select` / `multiselect` / `list` 5가지만 그립니다.
**목표: 화면 파일 하나가 300줄을 넘지 않게.**

---

## 데이터베이스

표 **1개**입니다.

```sql
CREATE TABLE IF NOT EXISTS public.drafts (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type     TEXT NOT NULL,                        -- 축사 · 기념사 · ...
  title          TEXT NOT NULL,                        -- 행사명
  form_data      JSONB NOT NULL DEFAULT '{}'::jsonb,   -- SpeechInput 전부
  generated_text TEXT,
  llm_meta       JSONB DEFAULT '{}'::jsonb,            -- ★ 모델 · 비용 · 소요시간
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;
```

- **`llm_meta`를 남기는 게 포인트입니다.** "어느 모델이 분량을 잘 지켰나"를 이력에서 SQL로 뽑을 수 있습니다.
- RLS를 켜고 정책을 하나도 만들지 않으면, 외부에서는 아무도 못 읽고 서버의 `service_role` 키만 통과합니다.
- Supabase SDK를 설치하지 않고 **httpx로 REST를 직접** 호출합니다 (쓰는 기능이 3개뿐).

---

## 구축 단계

총 **31시간 / 하루 12시간이면 3일**.

> **1차 완료 기준은 6단계입니다** — `/write`에서 폼을 채우고 버튼을 누르면 축사가 화면에 나옵니다.
> 그 전에는 8종·hwpx·이력·자동작성을 시작하지 않습니다.

### 1일차 (11h) — 인터넷 주소에서 축사가 나온다

| # | 단계 | 시간 | 완료 확인 | 상태 |
|---|---|---:|---|:---:|
| 1 | 준비 — 폴더·`.gitignore`·`config.py`·`server.py` | 1h | `:8011/health` → `{"status":"ok"}` | ☑ |
| 2 | **화면 뼈대 + 배포** | 3h | **남의 폰으로** Render 주소 접속 성공 | ☐ |
| 3 | AI 연결(2사) + 키 검증 + 설정 화면 | 2.5h | 틀린 키 → "인증 실패"라고 **이유가** 뜸 | ☑ |
| 4 | **모델 카탈로그 + `/api/models` + 드롭다운** | 1.5h | 회사를 바꾸면 목록·비용이 바뀜 | ☑ |
| 5 | 프롬프트 L1·L2·L3 + `builder.py` | 3h | Python 호출로 6단 축사가 나옴 | ☑ |

### 2일차 (12h) — 기능이 전부 동작한다

| # | 단계 | 시간 | 완료 확인 | 상태 |
|---|---|---:|---|:---:|
| 6 | 작성 화면 (14칸 전부) | 3h | **★ 1차 완료** — 폼 → 버튼 → 축사 | ☑ |
| 7 | 다운로드 (md + hwpx) | 2h | 한글 프로그램에서 열림. 파일명 안 깨짐 | ☐ |
| 8 | **유형 8종 연결 + 유형별 검증** | 2h | 8개가 다 동작하고 톤이 다름 | ☑ |
| 9 | 파일 올려서 자동 작성 | 3h | **원본에 없는 날짜·인명이 없음** | ☑ |
| 10 | Supabase + 작성 이력 | 2h | **Supabase를 꺼도 축사 생성은 됨** | ☑ |

### 3일차 (8h) — 남에게 보여줄 수 있다

| # | 단계 | 시간 | 완료 확인 | 상태 |
|---|---|---:|---|:---:|
| 11 | 품질검사 + 오류 화면 + 모바일 | 2h | 접속 암호 지우고 [작성] → 오류 화면 + **다시 로그인** 버튼 | ☑ |
| 12 | **모델 등급별 비교 실측** | 1h | 위 비교표의 빈 칸을 채움 | ☑ |
| 13 | 글 품질 다듬기 (유형 4종 × L2 수정) | 3h | 결과물을 보고 **"손보면 쓰겠다"** | ☑ |
| 14 | 재배포 + README + 화면 사진 | 2h | `/api/local-keys`가 빈 응답 | ☐ (코드·문서는 이 커밋으로 끝. 화면 사진·배포 재확인은 컨트롤러 진행 중) |

### 절대 자르면 안 되는 것 3가지

| | 항목 | 왜 |
|---|---|---|
| ① | **2단계 배포** | 링크가 없으면 보여줄 수가 없습니다 |
| ② | **11단계 오류 화면** | 데모 도중 깨지면 그걸로 끝입니다 |
| ③ | **13단계 글 품질 3시간** | 글이 별로면 만든 의미가 없습니다 |

> **왜 2단계에서 미리 배포하나**: 배포는 처음에 반드시 한 번 막힙니다.
> 마지막 날로 미루면 "다 만들었는데 못 보여주는" 사태가 납니다.
> 껍데기로 한 번 올려두면 이후에는 `git push`만으로 갱신됩니다.

---

## AI · 보안 설계

### 1. 사용자 API 키 보호

- **서버가 `.env`(로컬) / Render 환경변수(배포)의 키를 직접 보관하고 호출에 씁니다.** 사용자가 원하면 요청 헤더(`X-OpenAI-Key`, `X-Anthropic-Key`)로 자신의 키를 대신 실어 보낼 수도 있습니다
- 어느 경로로 들어온 값이든 서버 디스크·DB·로그에 **저장하지 않습니다**
- `APP_PASSWORD` 접속 암호 게이트가 유료(AI 호출) 라우트와 `/api/drafts`(작성 이력 조회·삭제)를 막습니다 — 암호를 아는 사람만 서버가 든 키와 저장된 이력을 쓸 수 있습니다. `/api/download/*`는 요청 본문에 실려 온 텍스트를 변환해 돌려줄 뿐 저장된 데이터를 노출하지 않아 이 게이트 밖에 있습니다
- 🔴 **`GET /api/local-keys`는 `.env`의 AI 키를 인증 없이 그대로 브라우저에 내려줍니다.** 막는 장치는 `ENVIRONMENT=production` 하나뿐입니다. 배포 시 이 변수를 반드시 설정하고, 배포 후 해당 주소를 직접 열어 `{"keys":{}}`인지 확인하세요
- `.gitignore`를 **첫 커밋 전에** 만듭니다. 키가 한 번 GitHub에 올라가면 지워도 기록에 남습니다

### 2. 모델 허용목록 검증

- `X-LLM-Model` 헤더는 사용자가 마음대로 바꿀 수 있습니다
- 목록이 화면에만 있으면 임의의 문자열을 실어 보낼 수 있고, **의도치 않게 비싼 모델**이 불릴 수 있습니다
- 그래서 허용목록의 원본을 **서버**(`llm/catalog.py`)에 두고, 모든 요청이 `catalog.resolve()`를 거칩니다
- 검증하지 않은 모델 id는 목록에 넣지 않습니다. `catalog.py` 맨 위에 **확인 날짜**를 주석으로 박아 둡니다

### 3. 사실관계 보호

- 인용·통계는 **사용자가 준 것만** 씁니다. 없으면 비우거나 "자료에 없음"으로 둡니다
- 프롬프트에 "입력에 없는 숫자는 만들지 말 것"을 명시합니다
- 업로드 파일에서 추출이 실패하면 안내 문자열이 반환되는데, **이 문자열이 프롬프트에 실려 들어가지 않도록** 라우터에서 차단합니다

### 4. Supabase 키 보호

- `SUPABASE_SERVICE_ROLE_KEY`는 RLS를 통과하는 키입니다. **브라우저로 절대 내보내지 않습니다**
- 서버만 이 키로 REST를 호출합니다

### 5. 저장 실패를 숨기지 않습니다

- 원본은 `except Exception: pass`로 삼켜서 사용자가 저장 안 된 걸 모릅니다
- 이 프로젝트는 응답의 `save_warning`에 사유를 담아 화면에 표시합니다. **글 자체는 그대로 돌려줍니다**

---

## 문서

| 파일 | 내용 |
|---|---|
| `README.md` | 이 파일 — 무엇을 만들었고 어떻게 쓰나 |
| `BUILD_GUIDE.md` | 파트별 구축 설계서 — 프론트·백엔드·DB·네트워크·AI를 각각 "무엇을·왜·어떻게·완료 확인" 순으로 |
| `PLAN.md` | 구현 계획서 — Task 14개 / Step 117개. 코드와 테스트, 단계별 확인 방법 포함 |
| `jooseok_project_v2.md` | 원본 `gov-writer` 분석 + 설계 결정 기록 |

---

## 라이선스

MIT
