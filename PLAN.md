# policy-writer 구현 계획서

> **에이전트로 실행할 경우:** 이 계획은 `superpowers:subagent-driven-development`(권장) 또는 `superpowers:executing-plans`로 task 단위 실행하도록 작성됐습니다. 모든 단계는 체크박스(`- [ ]`)입니다.

**목표:** 행사 정보를 폼에 넣으면 AI가 부처 6단 기틀에 맞춰 말씀자료 8종을 쓰고, 마크다운·한글파일로 내려주는 웹앱을 3일 안에 배포 가능한 상태로 만든다.

**접근:** FastAPI 단일 프로세스가 `/api`와 React 빌드 산출물을 함께 서빙한다. 모델 허용목록은 서버가 갖고 화면은 받아서 그린다. 2단계에서 껍데기를 먼저 배포해 배포 리스크를 앞으로 당긴다. 6단계 끝이 1차 완료 기준이다.

**기술 스택:** Python 3.10+ / FastAPI / uvicorn / httpx / pydantic-settings · React + TypeScript + Vite + Tailwind · Supabase(PostgreSQL) · pytest

**참고 문서:** [README.md](README.md) · [BUILD_GUIDE.md](BUILD_GUIDE.md) · [jooseok_project_v2.md](jooseok_project_v2.md)

---

## 전역 제약 — 모든 task에 적용된다

아래는 **모든 task의 요구사항에 암묵적으로 포함**된다. task마다 반복하지 않는다.

| # | 제약 | 정확한 값 |
|---|---|---|
| G1 | Python 하한 | `requires-python = ">=3.10"` (개발 PC는 3.12) |
| G2 | 포트 | 백엔드 **8010**, 프론트 **5173**. 8000 금지 |
| G3 | 모델 허용목록 | Task 3의 `catalog.py` 5개가 전부. **목록에 없는 id를 지어내지 말 것** (`gpt-6-astra`, `claude-opus-4-1` 금지) |
| G4 | 기본 회사 | `DEFAULT_PROVIDER = "openai"`. 서버·화면 **양쪽 다**. `gemini` 금지 |
| G5 | `temperature` | `model_meta["temperature"]`가 `True`일 때만 본문에 넣는다. 확신 없으면 안 보낸다 |
| G6 | OpenAI 출력 길이 | `max_completion_tokens` 사용. `max_tokens` 금지 |
| G7 | 설정 읽기 | `get_settings()`만 사용. `os.environ.get()` **혼용 금지** |
| G8 | SPA 폴백 | `@app.get("/{full_path:path}")`는 **모든 `include_router` 뒤**에 |
| G9 | 공통 함수 | 키 추출·JSON 파싱·품질검사는 `common/`에 **1벌씩**. 복사 금지 |
| G10 | 연결 원칙 | 함수를 만들면 **그 자리에서** 라우터에 연결한다. 만들어놓고 안 부르는 함수 금지 |
| G11 | 화면 파일 크기 | 파일 하나가 **300줄**을 넘지 않게 |
| G12 | 키 보관 | LLM 키는 요청 헤더로만. 서버 디스크·DB·로그 저장 금지 |
| G13 | `.gitignore` | **첫 커밋 전에** 만든다 |
| G14 | 한글 테스트 | PowerShell `ConvertTo-Json` 금지 (한글 깨짐). **Python 스크립트로** 보낼 것 |
| G15 | 커밋 | task마다 최소 1회. 메시지는 `feat:` / `fix:` / `chore:` 접두 |

### 테스트 전략 — 어디에 pytest를 쓰고 어디에 안 쓰나

31시간 예산 안에서 모든 것을 TDD하면 UI가 안 끝난다. **판단이 들어가는 순수 함수에만 pytest를 쓰고, 나머지는 명시된 수동 확인으로 대체한다.**

| pytest로 검증 (TDD) | 수동 확인으로 검증 |
|---|---|
| `catalog.resolve()` — 허용목록 밖 400 | 화면 렌더링·레이아웃 |
| `keys.resolve_user_key()` — 없으면 401 | 배포 접속 |
| `builder.build_speech_prompt()` — 조립 순서 | AI 결과물의 문장 품질 |
| `quality.check_output()` — 경고 조건 | 한글파일이 한글 프로그램에서 열리는지 |
| `cost.won_per_doc()` — 비용 계산 | 모바일 반응형 |
| `converters.split_paragraphs()` — 단락 분리 | |
| `extractors.extract_text()` — 인코딩 폴백·미지원 가드 | |
| `config.local_llm_keys` — production이면 빈 dict | |

**실제 AI 호출은 테스트하지 않는다.** 돈이 들고 느리다. `respx`로 HTTP를 가로채 **본문 모양**만 검증한다 (`temperature`가 들어갔나/빠졌나 등).

### 실행 명령 모음 (윈도우)

```powershell
# 테스트
.\.venv\Scripts\python.exe -m pytest -v

# 백엔드만
.\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --reload --port 8010

# 프론트만
cd frontend; npm run dev

# 둘 다
.\run.ps1
```

---

## 파일 구조 — 무엇을 언제 만드나

| 파일 | 책임 | 만드는 task |
|---|---|---|
| `.gitignore` | 키 유출 차단 | **1 (제일 먼저)** |
| `pyproject.toml` | 의존성·패키지 정의 | 1 |
| `src/policy_writer/config.py` | `.env` → `Settings` 1개 | 1 |
| `src/policy_writer/server.py` | 앱 조립 · 라우터 등록 · SPA 폴백 | 1 (2·5·7·10에서 라우터 추가) |
| `run.ps1` | 서버+화면 동시 기동 | 1 |
| `frontend/` 전체 | 화면 | 2 (6·7·8·9·10에서 확장) |
| `render.yaml` | 배포 설정 | 2 |
| `src/policy_writer/common/keys.py` | 헤더에서 키 꺼내기 | 3 |
| `src/policy_writer/llm/catalog.py` | 모델 허용목록 + `resolve()` | **3** (← 스펙 4단계에서 당김) |
| `src/policy_writer/llm/client.py` | `call_llm` — 회사별 요청 분기 | 3 |
| `src/policy_writer/api/settings.py` | 키 검증 · 모델 목록 · 로컬 키 | 3 (4에서 `/api/models` 추가) |
| `src/policy_writer/llm/cost.py` | 1건당 원화 계산 | 4 |
| `src/policy_writer/prompts/l1_identity.py` | L1 정체성 | 5 |
| `src/policy_writer/prompts/l2_domain.py` | **L2 6단 기틀 · 8종 표 · 정형구** | 5 (8에서 8종 확장) |
| `src/policy_writer/prompts/l3_rules.py` | L3 작성 절차 | 5 |
| `src/policy_writer/prompts/builder.py` | `SpeechInput` + L4/L5 + 조립 | 5 |
| `src/policy_writer/common/quality.py` | `check_output` | 5 |
| `src/policy_writer/api/speech.py` | 말씀자료 작성 라우터 | 5 (9에서 업로드 추가) |
| `frontend/src/lib/speech-data.ts` | 유형·청중·분량·직급 상수 | 6 (8에서 8종 완성) |
| `frontend/src/lib/speechFields.ts` | 폼 칸 정의 배열 | 6 |
| `frontend/src/components/Field.tsx` | 입력칸 1개 렌더러 | 6 |
| `src/policy_writer/exporters/converters.py` | MD · HWPX 변환 | 7 |
| `src/policy_writer/api/download.py` | 다운로드 라우터 | 7 |
| `src/policy_writer/extractors/files.py` | 파일 텍스트 추출 | 9 |
| `supabase/migrations/001_init.sql` | `drafts` 표 | 10 |
| `src/policy_writer/db/drafts.py` | Supabase REST | 10 |
| `src/policy_writer/api/drafts.py` | 이력 라우터 | 10 |

### 스펙 대비 조정 2건

**1. `llm/catalog.py`를 스펙 4단계 → Task 3으로 당긴다.**
이유: `call_llm(model_meta=...)`이 카탈로그가 돌려준 dict를 인자로 받는다. 카탈로그 없이 3단계를 만들면 임시 dict를 하드코딩했다가 4단계에서 버려야 한다.
**Task 4는 그대로 남는다** — `/api/models` 엔드포인트 + 비용 계산 + 화면 드롭다운. README의 14단계 표는 그대로 유효하다.

**2. `common/parsing.py`(`parse_json_response`)를 만들지 않는다.**
스펙 3장 폴더 구조에는 있지만, **이 범위에서 부를 곳이 없다.**
원본에서 이 함수는 "AI에게 JSON을 뱉게 해서 폼을 채우는" 경로(`refine.py`의 `extract-event-info` 등)에 쓰인다.
우리 `auto-draft`는 파일 텍스트를 **그대로 L4 참고자료로 넣고** AI에게 본문만 쓰게 하므로 JSON 파싱이 필요 없다.

> **G10을 이 파일에도 적용한 것이다.** 원본의 `build_press_prompt`가 만들어놓고 아무도 안 부르는 함수였다.
> 나중에 "행사계획서에서 폼을 자동으로 채워 넣기"를 붙일 때 그때 만든다.
> **`common/`은 여전히 유효하다** — `keys.py`(Task 3)와 `quality.py`(Task 5)가 각각 1벌씩 들어간다.

---

# Day 1 — 인터넷 주소에서 축사가 나온다 (11시간)

---

## Task 1: 프로젝트 뼈대 + `/health` (1h)

**Files:**
- Create: `.gitignore`, `pyproject.toml`, `.env.example`, `.env`, `run.ps1`
- Create: `src/policy_writer/__init__.py`, `src/policy_writer/config.py`, `src/policy_writer/server.py`
- Create: `tests/__init__.py`, `tests/test_config.py`

**Interfaces:**
- Produces: `get_settings() -> Settings`, `Settings.environment: str`, `Settings.local_llm_keys: dict[str, str]`, `app` (FastAPI 인스턴스)

---

- [ ] **Step 1: `.gitignore`를 제일 먼저 만든다**

git init보다 먼저다. 키가 한 번 올라가면 지워도 기록에 남는다.

`.gitignore`:
```gitignore
.env
.env.local
!.env.example
.venv/
__pycache__/
*.py[cod]
.pytest_cache/
node_modules/
static/
dist/
*.tsbuildinfo
```

- [ ] **Step 2: git 저장소 초기화**

```bash
git init
git add .gitignore
git commit -m "chore: add .gitignore before anything else"
```

- [ ] **Step 3: `pyproject.toml` 작성**

```toml
[project]
name = "policy-writer"
version = "0.1.0"
description = "말씀자료 작성기"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "pydantic>=2.6",
    "pydantic-settings>=2.2",
    "httpx>=0.27",
    "python-multipart>=0.0.9",
    "pypdf>=4.0",
    "python-docx>=1.1",
    "python-hwpx>=0.1",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "respx>=0.21",
]

[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
```

- [ ] **Step 4: 가상환경 + 설치**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

`python-hwpx` 설치가 실패하면 그 줄만 빼고 설치한 뒤, Task 7 시작 전에 다시 시도한다. Task 1~6은 hwpx가 필요 없다.

- [ ] **Step 5: `.env.example`과 `.env` 작성**

`.env.example`:
```bash
ENVIRONMENT=development

# AI 키 — 로컬 개발 전용, 최소 하나
# ⚠️ 배포할 때는 반드시 비워두세요. 접속자 누구나 가져갈 수 있습니다.
OPENAI_API_KEY=
ANTHROPIC_API_KEY=

# Supabase — Task 10부터
SUPABASE_URL=
SUPABASE_SERVICE_ROLE_KEY=
```

```powershell
copy .env.example .env
```

`.env`의 `OPENAI_API_KEY=`에 실제 키를 채운다. **`.env.example`에는 절대 채우지 않는다.**

- [ ] **Step 6: 실패하는 테스트를 먼저 쓴다**

`tests/test_config.py`:
```python
from policy_writer.config import Settings


def test_local_llm_keys_returns_filled_keys_in_development():
    s = Settings(environment="development", openai_api_key="sk-test", anthropic_api_key="")
    assert s.local_llm_keys == {"openai": "sk-test"}


def test_local_llm_keys_is_empty_in_production():
    s = Settings(environment="production", openai_api_key="sk-test", anthropic_api_key="sk-ant-test")
    assert s.local_llm_keys == {}
```

두 번째 테스트가 **보안 함정 1번**을 막는 장치다.

- [ ] **Step 7: 테스트가 실패하는 것을 확인**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

기대: `ModuleNotFoundError: No module named 'policy_writer.config'`

- [ ] **Step 8: `config.py` 구현**

`src/policy_writer/__init__.py`는 빈 파일로 만든다.

`src/policy_writer/config.py`:
```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    environment: str = "development"
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    supabase_url: str = ""
    supabase_service_role_key: str = ""

    @property
    def local_llm_keys(self) -> dict[str, str]:
        """개발 편의용. production 이면 무조건 빈 dict."""
        if self.environment == "production":
            return {}
        candidates = {
            "openai": self.openai_api_key,
            "anthropic": self.anthropic_api_key,
        }
        return {k: v for k, v in candidates.items() if v}


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

> `@lru_cache` 때문에 `.env`를 고치면 **서버를 껐다 켜야** 한다. 앞으로 "키를 넣었는데 왜 안 되지?"가 나오면 제일 먼저 의심할 것.

- [ ] **Step 9: 테스트 통과 확인**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_config.py -v
```

기대: `2 passed`

- [ ] **Step 10: `server.py` 최소 버전 구현**

`src/policy_writer/server.py`:
```python
from fastapi import FastAPI

from policy_writer.config import get_settings

app = FastAPI(title="말씀자료 작성기", version="0.1.0")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info")
def info() -> dict:
    settings = get_settings()
    return {
        "name": "policy-writer",
        "version": "0.1.0",
        "environment": settings.environment,
    }
```

> **SPA 폴백은 아직 넣지 않는다.** Task 2에서 라우터를 다 등록한 **뒤에** 넣는다 (G8).

- [ ] **Step 11: `run.ps1` 작성**

```powershell
# run.ps1 — 백엔드(8010) + 프론트(5173) 동시 기동
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot

Start-Process powershell -ArgumentList @(
    "-NoExit", "-Command",
    "cd '$root'; .\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --reload --port 8010"
)

if (Test-Path "$root\frontend\package.json") {
    Start-Process powershell -ArgumentList @(
        "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"
    )
}

Write-Host "backend  http://localhost:8010/health"
Write-Host "frontend http://localhost:5173"
```

- [ ] **Step 12: 서버를 띄우고 눈으로 확인 — Task 1 완료 조건**

```powershell
.\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --reload --port 8010
```

브라우저에서 확인:

| 주소 | 기대 |
|---|---|
| `http://localhost:8010/health` | `{"status":"ok"}` |
| `http://localhost:8010/api/info` | `{"name":"policy-writer","version":"0.1.0","environment":"development"}` |

- [ ] **Step 13: 커밋**

```bash
git add .
git commit -m "feat: project skeleton with config and health endpoint"
```

`git status`로 **`.env`가 목록에 없는지** 확인한다. 있으면 `.gitignore`를 고치고 다시.

---

## Task 2: 화면 뼈대 + 배포 (3h)

배포를 여기서 하는 이유: **배포는 처음에 반드시 한 번 막힌다.** 마지막 날로 미루면 "다 만들었는데 못 보여주는" 사태가 난다.

**Files:**
- Create: `frontend/` 전체 (Vite 스캐폴드)
- Create: `frontend/vite.config.ts`, `frontend/src/App.tsx`, `frontend/src/routes/{HubPage,WritePage,HistoryPage,SettingsPage}.tsx`
- Create: `render.yaml`
- Modify: `src/policy_writer/server.py` (CORS + 정적 서빙 + SPA 폴백)

**Interfaces:**
- Produces: 라우트 4개 (`/`, `/write`, `/history`, `/settings`), `static/` 빌드 산출물, 배포 주소

---

- [ ] **Step 1: Vite 프로젝트 생성**

```powershell
npm create vite@latest frontend -- --template react-ts
cd frontend
npm install
npm install react-router-dom lucide-react
npm install -D tailwindcss @tailwindcss/postcss postcss autoprefixer
cd ..
```

- [ ] **Step 2: Tailwind 설정**

`frontend/postcss.config.js`:
```js
export default {
  plugins: { '@tailwindcss/postcss': {} },
}
```

`frontend/src/index.css` 맨 위에:
```css
@import "tailwindcss";
```

- [ ] **Step 3: `vite.config.ts` — 두 줄이 핵심**

```ts
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: '../static',      // ★ 기본값(dist)이면 FastAPI 가 못 찾는다
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8010', changeOrigin: true },   // ★ 8010
    },
  },
})
```

- [ ] **Step 4: 라우트 4개 뼈대**

`frontend/src/App.tsx`:
```tsx
import { BrowserRouter, Routes, Route, Link } from 'react-router-dom'
import HubPage from './routes/HubPage'
import WritePage from './routes/WritePage'
import HistoryPage from './routes/HistoryPage'
import SettingsPage from './routes/SettingsPage'

export default function App() {
  return (
    <BrowserRouter>
      <nav className="flex gap-4 border-b px-6 py-3 text-sm">
        <Link to="/" className="font-semibold">말씀자료 작성기</Link>
        <Link to="/write">작성</Link>
        <Link to="/history">이력</Link>
        <Link to="/settings">설정</Link>
      </nav>
      <main className="mx-auto max-w-3xl p-6">
        <Routes>
          <Route path="/" element={<HubPage />} />
          <Route path="/write" element={<WritePage />} />
          <Route path="/history" element={<HistoryPage />} />
          <Route path="/settings" element={<SettingsPage />} />
        </Routes>
      </main>
    </BrowserRouter>
  )
}
```

나머지 4개 파일은 각각 이 모양으로 만든다 (이름만 바꿔서):

`frontend/src/routes/HubPage.tsx`:
```tsx
export default function HubPage() {
  return <h1 className="text-2xl font-bold">홈</h1>
}
```

`WritePage.tsx` → `작성`, `HistoryPage.tsx` → `작성 이력`, `SettingsPage.tsx` → `설정`.

- [ ] **Step 5: 프론트 단독 확인**

```powershell
cd frontend; npm run dev
```

`http://localhost:5173`에서 4개 링크가 전부 눌리고 제목이 바뀌는지 확인.

- [ ] **Step 6: 빌드해서 `static/`이 생기는지 확인**

```powershell
cd frontend; npm run build; cd ..
```

`static/index.html`이 생겼는지 확인한다. `frontend/dist/`가 생겼다면 `outDir` 설정이 안 먹은 것이다.

- [ ] **Step 7: `server.py`에 CORS + 정적 서빙 + SPA 폴백 추가**

`src/policy_writer/server.py` 전체를 아래로 교체:
```python
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from policy_writer.config import get_settings

app = FastAPI(title="말씀자료 작성기", version="0.1.0")
settings = get_settings()

STATIC_DIR = Path(__file__).resolve().parents[2] / "static"

# ── 1) CORS — 개발일 때만 ────────────────────────────────
if settings.environment == "development":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:5173"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],     # X-LLM-Provider 등 커스텀 헤더 통과에 필요
    )

# ── 2) 라우터 — Task 3·5·7·10 에서 여기에 추가된다 ────────
# app.include_router(...)

# ── 3) 기본 엔드포인트 ───────────────────────────────────
@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.get("/api/info")
def info() -> dict:
    return {
        "name": "policy-writer",
        "version": "0.1.0",
        "environment": settings.environment,
    }


# ── 4) ★ SPA 폴백 — 반드시 맨 마지막 (G8) ────────────────
if STATIC_DIR.is_dir():
    app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")

    @app.get("/{full_path:path}")
    def spa(full_path: str) -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")
```

> 🔴 이 순서를 바꾸면 `/api/...` 요청이 **전부 `index.html`을 받는다.** 화면에서는 "API가 이상한 응답을 준다"로 보인다.

- [ ] **Step 8: 통합 확인 — 정적 서빙과 API가 공존하는지**

```powershell
.\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --port 8010
```

| 주소 | 기대 |
|---|---|
| `http://localhost:8010/` | React 홈 화면 (HTML) |
| `http://localhost:8010/write` | React 작성 화면 (404 아님) |
| `http://localhost:8010/api/info` | **JSON** (HTML이면 Step 7 순서가 틀린 것) |

- [ ] **Step 9: `render.yaml` 작성**

```yaml
services:
  - type: web
    name: policy-writer
    runtime: python
    region: singapore
    plan: free
    buildCommand: |
      pip install -e .
      cd frontend && npm install && npm run build
    startCommand: uvicorn policy_writer.server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: ENVIRONMENT
        value: production          # ★ 🔴 이 줄이 AI 키 공개를 막는 유일한 장치
      - key: PYTHON_VERSION
        value: "3.12"
      - key: OPENAI_API_KEY
        value: ""                  # 비워둔다
      - key: ANTHROPIC_API_KEY
        value: ""                  # 비워둔다
```

- [ ] **Step 10: GitHub에 올린다**

```bash
git add .
git commit -m "feat: frontend skeleton with 4 routes, static serving, render config"
```

GitHub에서 새 저장소를 만들고:
```bash
git remote add origin https://github.com/<사용자명>/policy-writer.git
git branch -M main
git push -u origin main
```

`git log --stat`으로 **`.env`가 커밋된 적 없는지** 확인한다.

- [ ] **Step 11: Render 배포**

Render 대시보드 → New → Blueprint → GitHub 저장소 선택 → `render.yaml` 자동 인식 → Apply.

빌드가 실패하면 로그를 읽는다. 흔한 원인:
- Node가 없음 → Render의 Python runtime은 Node를 포함한다. 안 되면 runtime을 `node`로 바꾸고 Python을 buildCommand에서 설치
- `npm run build`가 `static/`을 못 만듦 → `vite.config.ts`의 `outDir` 확인

- [ ] **Step 12: 배포 확인 3가지 — Task 2 완료 조건 🔴**

| 확인 | 방법 | 기대 |
|---|---|---|
| 화면이 뜬다 | **남의 폰으로** 배포 주소 접속 | 홈 화면 |
| 환경이 production | `https://<주소>/api/info` | `"environment": "production"` |
| SPA 폴백 정상 | `https://<주소>/write` 새로고침 | 404가 아니라 화면 |

- [ ] **Step 13: 커밋**

```bash
git add .
git commit -m "chore: deploy skeleton to Render"
git push
```

---

## Task 3: AI 연결 + 모델 카탈로그 + 키 검증 (2.5h)

**Files:**
- Create: `src/policy_writer/common/__init__.py`, `src/policy_writer/common/keys.py`
- Create: `src/policy_writer/llm/__init__.py`, `src/policy_writer/llm/catalog.py`, `src/policy_writer/llm/client.py`
- Create: `src/policy_writer/api/__init__.py`, `src/policy_writer/api/settings.py`
- Create: `tests/test_catalog.py`, `tests/test_keys.py`, `tests/test_client_body.py`
- Modify: `src/policy_writer/server.py` (라우터 등록)
- Modify: `frontend/src/routes/SettingsPage.tsx`, Create: `frontend/src/hooks/useLLMSettings.ts`, `frontend/src/lib/api.ts`

**Interfaces:**
- Produces:
  - `catalog.resolve(provider: str, model: str | None) -> dict` — 키 `id`, `tier`, `temperature`, `in`, `out`
  - `catalog.MODELS: dict[str, list[dict]]`, `catalog.DEFAULTS: dict[str, str]`, `catalog.DEFAULT_PROVIDER: str`
  - `keys.norm_provider(raw: str | None) -> str`
  - `keys.resolve_user_key(request: Request, provider: str) -> str`
  - `client.call_llm(*, provider, model_meta, api_key, system_prompt, user_prompt, max_tokens=4000, temperature=0.7, timeout=120.0) -> tuple[str, dict]`
  - `settings_router` (`POST /api/validate-key`, `GET /api/local-keys`)

---

- [ ] **Step 1: catalog 테스트를 먼저 쓴다**

`tests/test_catalog.py`:
```python
import pytest
from fastapi import HTTPException

from policy_writer.llm import catalog


def test_resolve_returns_model_meta():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert m["id"] == "gpt-4o-mini"
    assert m["tier"] == "경제형"
    assert m["temperature"] is True


def test_resolve_uses_default_when_model_missing():
    m = catalog.resolve("openai", None)
    assert m["id"] == catalog.DEFAULTS["openai"]


def test_resolve_rejects_unknown_model():
    with pytest.raises(HTTPException) as e:
        catalog.resolve("openai", "gpt-6-astra")
    assert e.value.status_code == 400


def test_resolve_rejects_unknown_provider():
    with pytest.raises(HTTPException) as e:
        catalog.resolve("gemini", None)
    assert e.value.status_code == 400


def test_default_provider_is_openai():
    assert catalog.DEFAULT_PROVIDER == "openai"


def test_top_tier_models_do_not_accept_temperature():
    assert catalog.resolve("openai", "gpt-5.6-sol")["temperature"] is False
    assert catalog.resolve("openai", "gpt-5.6-terra")["temperature"] is False


def test_anthropic_has_exactly_two_tiers():
    assert len(catalog.MODELS["anthropic"]) == 2
```

마지막 두 테스트가 **함정 3번(temperature 400)**과 **"검증 안 한 id 금지" 규칙**을 코드로 고정한다.

- [ ] **Step 2: 실패 확인**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_catalog.py -v
```

기대: `ModuleNotFoundError: No module named 'policy_writer.llm'`

- [ ] **Step 3: `catalog.py` 구현**

`src/policy_writer/llm/__init__.py`는 빈 파일.

`src/policy_writer/llm/catalog.py`:
```python
# ─────────────────────────────────────────────────────────────
# 확인일: 2026-09-05
# ⚠️ 모델 id 와 가격은 바뀐다. 이 파일이 가장 빨리 낡는 곳이다.
#    수정할 때마다 위 날짜를 갱신할 것.
#
# 검증 상태:
#   OpenAI  경제형/최상위 → [실측] 직접 호출해 200 확인
#   OpenAI  표준형        → [조사] 문서상 존재, 미호출
#   Anthropic 전부        → 키가 없어 미호출
#   Anthropic 최상위      → 비워 뒀다 (아래 주석 참고)
# ─────────────────────────────────────────────────────────────
from fastapi import HTTPException

MODELS: dict[str, list[dict]] = {
    "openai": [
        {"id": "gpt-4o-mini",   "tier": "경제형", "temperature": True,
         "in": 0.15, "out": 0.60},
        {"id": "gpt-5.6-terra", "tier": "표준형", "temperature": False,
         "in": 2.00, "out": 12.00},
        {"id": "gpt-5.6-sol",   "tier": "최상위", "temperature": False,
         "in": 4.00, "out": 20.00},
    ],
    "anthropic": [
        {"id": "claude-haiku-4-5",           "tier": "경제형", "temperature": True,
         "in": 1.00, "out": 5.00},
        {"id": "claude-sonnet-4-5-20250929", "tier": "표준형", "temperature": True,
         "in": 3.00, "out": 15.00},
        # 최상위 없음 — Anthropic 키가 없어 검증 못 했다.
        # 키가 생기면 후보를 한 번 호출해 200 을 확인한 뒤 이 줄을 추가한다.
    ],
}

# ⚠️ 이 DEFAULTS 는 "헤더에 X-LLM-Model 이 아예 없을 때 서버가 쓰는 값"이다.
#    화면이 처음 보여주는 등급(localStorage 초기값)과는 다른 개념이다.
DEFAULTS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-sonnet-4-5-20250929",
}

DEFAULT_PROVIDER = "openai"   # ★ 원본 기본값은 "gemini" 였다 (G4)


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

- [ ] **Step 4: 통과 확인**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_catalog.py -v
```

기대: `7 passed`

- [ ] **Step 5: keys 테스트를 쓴다**

`tests/test_keys.py`:
```python
import pytest
from fastapi import HTTPException
from starlette.datastructures import Headers
from starlette.requests import Request

from policy_writer.common import keys


def _req(headers: dict) -> Request:
    raw = [(k.lower().encode(), v.encode()) for k, v in headers.items()]
    return Request({"type": "http", "headers": raw})


def test_norm_provider_accepts_known():
    assert keys.norm_provider("anthropic") == "anthropic"
    assert keys.norm_provider("  OpenAI ") == "openai"


def test_norm_provider_falls_back_to_openai():
    assert keys.norm_provider(None) == "openai"
    assert keys.norm_provider("gemini") == "openai"


def test_resolve_user_key_reads_correct_header():
    r = _req({"X-OpenAI-Key": "sk-abc", "X-Anthropic-Key": "sk-ant-xyz"})
    assert keys.resolve_user_key(r, "openai") == "sk-abc"
    assert keys.resolve_user_key(r, "anthropic") == "sk-ant-xyz"


def test_resolve_user_key_raises_401_when_missing():
    with pytest.raises(HTTPException) as e:
        keys.resolve_user_key(_req({}), "openai")
    assert e.value.status_code == 401
    assert "키" in e.value.detail
```

- [ ] **Step 6: 실패 확인 후 `keys.py` 구현**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_keys.py -v
```

`src/policy_writer/common/__init__.py`는 빈 파일.

`src/policy_writer/common/keys.py`:
```python
from fastapi import HTTPException, Request

from policy_writer.llm.catalog import DEFAULT_PROVIDER

HEADER_BY_PROVIDER = {
    "openai": "X-OpenAI-Key",
    "anthropic": "X-Anthropic-Key",
}


def norm_provider(raw: str | None) -> str:
    p = (raw or "").strip().lower()
    return p if p in HEADER_BY_PROVIDER else DEFAULT_PROVIDER


def resolve_user_key(request: Request, provider: str) -> str:
    header = HEADER_BY_PROVIDER[provider]
    key = (request.headers.get(header) or "").strip()
    if not key:
        raise HTTPException(401, "설정에서 API 키를 먼저 입력해 주세요.")
    return key
```

> 이 함수는 **딱 1벌만 존재한다** (G9). 원본은 3벌이었다.

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_keys.py -v
```

기대: `4 passed`

- [ ] **Step 7: `call_llm` 본문 조립 테스트를 쓴다 — 함정 3·4번을 고정한다**

`tests/test_client_body.py`:
```python
import httpx
import pytest
import respx

from policy_writer.llm import catalog
from policy_writer.llm.client import call_llm

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"

OPENAI_OK = {
    "choices": [{"message": {"content": "본문"}}],
    "usage": {"prompt_tokens": 10, "completion_tokens": 5},
}
ANTHROPIC_OK = {
    "content": [{"text": "본문"}],
    "usage": {"input_tokens": 10, "output_tokens": 5},
}


@respx.mock
async def test_openai_omits_temperature_for_top_tier():
    route = respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-5.6-sol"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    body = route.calls[0].request.content.decode()
    assert "temperature" not in body
    assert "max_completion_tokens" in body   # 함정 4번
    assert "max_tokens" not in body


@respx.mock
async def test_openai_includes_temperature_for_economy_tier():
    route = respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-4o-mini"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    assert "temperature" in route.calls[0].request.content.decode()


@respx.mock
async def test_anthropic_puts_system_at_top_level():
    route = respx.post(ANTHROPIC_URL).mock(return_value=httpx.Response(200, json=ANTHROPIC_OK))
    await call_llm(
        provider="anthropic",
        model_meta=catalog.resolve("anthropic", "claude-haiku-4-5"),
        api_key="sk-ant-x", system_prompt="SYSTEM_MARK", user_prompt="U",
    )
    payload = route.calls[0].request.content.decode()
    assert '"system"' in payload
    assert '"max_tokens"' in payload


@respx.mock
async def test_returns_text_and_normalized_meta():
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(200, json=OPENAI_OK))
    text, meta = await call_llm(
        provider="openai",
        model_meta=catalog.resolve("openai", "gpt-4o-mini"),
        api_key="sk-x", system_prompt="S", user_prompt="U",
    )
    assert text == "본문"
    assert meta["input_tokens"] == 10
    assert meta["output_tokens"] == 5
    assert meta["model"] == "gpt-4o-mini"
    assert meta["elapsed_ms"] >= 0


@respx.mock
async def test_upstream_401_becomes_401_with_korean_message():
    from fastapi import HTTPException
    respx.post(OPENAI_URL).mock(return_value=httpx.Response(401, json={"error": {"message": "bad key"}}))
    with pytest.raises(HTTPException) as e:
        await call_llm(
            provider="openai",
            model_meta=catalog.resolve("openai", "gpt-4o-mini"),
            api_key="sk-bad", system_prompt="S", user_prompt="U",
        )
    assert e.value.status_code == 401
    assert "인증 실패" in e.value.detail
```

- [ ] **Step 8: 실패 확인 후 `client.py` 구현**

`src/policy_writer/llm/client.py`:
```python
import time

import httpx
from fastapi import HTTPException

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"


def _build_openai(model_meta: dict, api_key: str, system_prompt: str,
                  user_prompt: str, max_tokens: int, temperature: float):
    body = {
        "model": model_meta["id"],
        "max_completion_tokens": max_tokens,          # ⚠️ max_tokens 아님 (G6)
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }
    if model_meta["temperature"]:                      # G5
        body["temperature"] = temperature
    headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
    return OPENAI_URL, headers, body


def _build_anthropic(model_meta: dict, api_key: str, system_prompt: str,
                     user_prompt: str, max_tokens: int, temperature: float):
    body = {
        "model": model_meta["id"],
        "max_tokens": max_tokens,                      # Anthropic 은 max_tokens
        "system": system_prompt,                       # 최상위 필드
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if model_meta["temperature"]:
        body["temperature"] = temperature
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
    }
    return ANTHROPIC_URL, headers, body


BUILDERS = {"openai": _build_openai, "anthropic": _build_anthropic}


def _extract(provider: str, data: dict) -> tuple[str, int, int]:
    if provider == "openai":
        text = data["choices"][0]["message"]["content"]
        u = data.get("usage", {})
        return text, u.get("prompt_tokens", 0), u.get("completion_tokens", 0)
    text = "".join(b.get("text", "") for b in data.get("content", []))
    u = data.get("usage", {})
    return text, u.get("input_tokens", 0), u.get("output_tokens", 0)


async def call_llm(
    *,
    provider: str,
    model_meta: dict,
    api_key: str,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 4000,
    temperature: float = 0.7,
    timeout: float = 120.0,
) -> tuple[str, dict]:
    url, headers, body = BUILDERS[provider](
        model_meta, api_key, system_prompt, user_prompt, max_tokens, temperature
    )

    started = time.monotonic()
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            res = await client.post(url, headers=headers, json=body)
    except httpx.TimeoutException:
        raise HTTPException(504, "시간이 초과되었습니다. 분량을 줄이거나 다시 시도해 주세요.")
    elapsed_ms = int((time.monotonic() - started) * 1000)

    if res.status_code in (401, 403):
        raise HTTPException(401, "인증 실패 — API 키를 다시 확인해 주세요.")
    if res.status_code >= 400:
        raise HTTPException(502, f"AI 서버 오류 ({res.status_code}). 잠시 후 다시 시도해 주세요.")

    text, in_tok, out_tok = _extract(provider, res.json())
    meta = {
        "provider": provider,
        "model": model_meta["id"],
        "elapsed_ms": elapsed_ms,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
    }
    return text, meta
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_client_body.py -v
```

기대: `5 passed`

- [ ] **Step 9: `api/settings.py` — 키 검증 + 로컬 키**

`src/policy_writer/api/settings.py`:
```python
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from policy_writer.config import get_settings
from policy_writer.llm import catalog
from policy_writer.llm.client import call_llm

router = APIRouter()


class ValidateKeyIn(BaseModel):
    provider: str
    api_key: str


@router.post("/api/validate-key")
async def validate_key(payload: ValidateKeyIn) -> dict:
    """가장 싼 모델로 1토큰만 불러서 키가 살아 있는지 본다."""
    if payload.provider not in catalog.MODELS:
        raise HTTPException(400, f"지원하지 않는 회사: {payload.provider}")
    cheapest = catalog.MODELS[payload.provider][0]
    await call_llm(
        provider=payload.provider,
        model_meta=cheapest,
        api_key=payload.api_key,
        system_prompt="ping",
        user_prompt="ping",
        max_tokens=16,
        timeout=30.0,
    )
    return {"ok": True, "message": "정상 연결되었습니다."}


@router.get("/api/local-keys")
def local_keys() -> dict:
    """🔴 development 에서만 값이 나온다. production 이면 빈 dict."""
    return {"keys": get_settings().local_llm_keys}
```

- [ ] **Step 10: `api/__init__.py`와 `server.py`를 **둘 다** 고친다**

한쪽만 고치면 404다.

`src/policy_writer/api/__init__.py`:
```python
from policy_writer.api.settings import router as settings_router

__all__ = ["settings_router"]
```

`server.py`의 `# ── 2) 라우터` 자리에:
```python
from policy_writer.api import settings_router

app.include_router(settings_router)
```

- [ ] **Step 11: 프론트 — `useLLMSettings.ts`**

`frontend/src/hooks/useLLMSettings.ts`:
```ts
import { useCallback, useState } from 'react'

export type Provider = 'openai' | 'anthropic'

const K = {
  provider: 'gw_llm_provider',
  key: (p: Provider) => `gw_llm_key_${p}`,
  model: (p: Provider) => `gw_llm_model_${p}`,
}

// 화면 초기 선택값 — 서버의 catalog.DEFAULTS 와는 다른 개념이다.
// 경제형은 목표를 올려도 700~1,000자에서 멈추므로 최상위를 기본으로 둔다.
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
```

- [ ] **Step 12: 프론트 — `lib/api.ts` (헤더 3개를 한 곳에서)**

`frontend/src/lib/api.ts`:
```ts
import { getLLMSettings } from '../hooks/useLLMSettings'

export class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message)
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
```

- [ ] **Step 13: 프론트 — `SettingsPage.tsx` (회사 + 키 + 연결 시험)**

모델 드롭다운은 Task 4에서 추가한다. 지금은 회사와 키만.

```tsx
import { useState } from 'react'
import { KEY_PATTERN, Provider, useLLMSettings } from '../hooks/useLLMSettings'

const PROVIDERS: { id: Provider; label: string }[] = [
  { id: 'openai', label: 'OpenAI' },
  { id: 'anthropic', label: 'Anthropic' },
]

export default function SettingsPage() {
  const { provider, setProvider, setKey, keyOf } = useLLMSettings()
  const [draft, setDraft] = useState(keyOf(provider))
  const [status, setStatus] = useState<string | null>(null)

  async function test() {
    if (!KEY_PATTERN[provider].test(draft)) {
      setStatus(`키 형식이 올바르지 않습니다 (${provider} 키는 ${provider === 'openai' ? 'sk-' : 'sk-ant-'}로 시작합니다)`)
      return
    }
    setStatus('확인 중...')
    const res = await fetch('/api/validate-key', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ provider, api_key: draft }),
    })
    const data = await res.json().catch(() => ({}))
    if (res.ok) {
      setKey(provider, draft)
      setStatus('정상 연결되었습니다.')
    } else {
      setStatus(data.detail ?? '연결에 실패했습니다.')
    }
  }

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">설정</h1>

      <section>
        <h2 className="mb-2 font-semibold">AI 회사</h2>
        <div className="flex gap-2">
          {PROVIDERS.map((p) => (
            <button
              key={p.id}
              onClick={() => { setProvider(p.id); setDraft(keyOf(p.id)); setStatus(null) }}
              className={`rounded border px-4 py-2 ${provider === p.id ? 'border-black bg-black text-white' : ''}`}
            >
              {p.label}
            </button>
          ))}
        </div>
      </section>

      <section>
        <h2 className="mb-2 font-semibold">API 키</h2>
        <div className="flex gap-2">
          <input
            type="password"
            value={draft}
            onChange={(e) => setDraft(e.target.value)}
            placeholder={provider === 'openai' ? 'sk-...' : 'sk-ant-...'}
            className="flex-1 rounded border px-3 py-2"
          />
          <button onClick={test} className="rounded border px-4 py-2">연결 시험</button>
        </div>
        {status && <p className="mt-2 text-sm">{status}</p>}
        <p className="mt-2 text-xs text-gray-500">
          키는 이 브라우저에만 저장되며, 요청 시 헤더로만 전달됩니다.
        </p>
      </section>
    </div>
  )
}
```

- [ ] **Step 14: 수동 확인 — Task 3 완료 조건**

`.\run.ps1` 실행 후 `http://localhost:5173/settings`에서:

| 시나리오 | 기대 |
|---|---|
| 올바른 OpenAI 키 → [연결 시험] | **"정상 연결되었습니다."** |
| 아무 문자열(`abc`) → [연결 시험] | "키 형식이 올바르지 않습니다..." |
| `sk-` 로 시작하는 **틀린** 키 → [연결 시험] | **"인증 실패 — API 키를 다시 확인해 주세요."** (막연한 오류 아님) |
| `http://localhost:8010/api/local-keys` | `.env`에 넣은 키가 보임 (development라서 정상) |

- [ ] **Step 15: 전체 테스트 + 커밋**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
기대: `18 passed`

```bash
git add .
git commit -m "feat: model catalog, llm client with per-model body branching, key validation"
git push
```

---

## Task 4: `GET /api/models` + 비용 계산 + 모델 드롭다운 (1.5h)

**Files:**
- Create: `src/policy_writer/llm/cost.py`, `tests/test_cost.py`
- Modify: `src/policy_writer/api/settings.py` (`/api/models` 추가)
- Modify: `frontend/src/routes/SettingsPage.tsx` (모델 등급 섹션 추가)

**Interfaces:**
- Consumes: `catalog.MODELS`, `useLLMSettings().setModel/modelOf`
- Produces:
  - `cost.won_per_doc(model_meta: dict) -> int`
  - `cost.won_for_usage(model_meta: dict, input_tokens: int, output_tokens: int) -> int`
  - `GET /api/models` → `{ "<provider>": [{ id, tier, won_per_doc }] }`

---

- [ ] **Step 1: 비용 계산 테스트를 쓴다**

`tests/test_cost.py`:
```python
from policy_writer.llm import catalog, cost


def test_won_per_doc_for_sonnet():
    # 4,000 x $3/1M + 1,500 x $15/1M = $0.0345 → 48원
    m = catalog.resolve("anthropic", "claude-sonnet-4-5-20250929")
    assert cost.won_per_doc(m) == 48


def test_won_per_doc_for_mini_is_cheapest():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_per_doc(m) == 2


def test_won_per_doc_for_sol():
    m = catalog.resolve("openai", "gpt-5.6-sol")
    assert cost.won_per_doc(m) == 64


def test_won_for_usage_uses_actual_tokens():
    m = catalog.resolve("openai", "gpt-4o-mini")
    assert cost.won_for_usage(m, 0, 0) == 0
    assert cost.won_for_usage(m, 4000, 1500) == cost.won_per_doc(m)
```

- [ ] **Step 2: 실패 확인 후 `cost.py` 구현**

`src/policy_writer/llm/cost.py`:
```python
USD_TO_KRW = 1400
TYPICAL_INPUT_TOKENS = 4000      # 프롬프트 L1~L5
TYPICAL_OUTPUT_TOKENS = 1500     # 1,500자


def won_for_usage(model_meta: dict, input_tokens: int, output_tokens: int) -> int:
    usd = (
        input_tokens * model_meta["in"] / 1_000_000
        + output_tokens * model_meta["out"] / 1_000_000
    )
    return round(usd * USD_TO_KRW)


def won_per_doc(model_meta: dict) -> int:
    """말씀자료 1건당 대략 얼마인지. 사용자에게 $0.000123 은 의미가 없다."""
    return won_for_usage(model_meta, TYPICAL_INPUT_TOKENS, TYPICAL_OUTPUT_TOKENS)
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_cost.py -v
```
기대: `4 passed`

- [ ] **Step 3: `/api/models` 추가**

`api/settings.py` 맨 아래에:
```python
from policy_writer.llm import cost


@router.get("/api/models")
def list_models() -> dict:
    """화면이 이걸 받아 그린다. 목록이 두 벌이 되지 않게 한다."""
    return {
        provider: [
            {"id": m["id"], "tier": m["tier"], "won_per_doc": cost.won_per_doc(m)}
            for m in models
        ]
        for provider, models in catalog.MODELS.items()
    }
```

- [ ] **Step 4: 엔드포인트 확인**

```powershell
.\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --port 8010
```

브라우저에서 `http://localhost:8010/api/models`:
```json
{
  "openai": [
    {"id": "gpt-4o-mini", "tier": "경제형", "won_per_doc": 2},
    {"id": "gpt-5.6-terra", "tier": "표준형", "won_per_doc": 36},
    {"id": "gpt-5.6-sol", "tier": "최상위", "won_per_doc": 64}
  ],
  "anthropic": [
    {"id": "claude-haiku-4-5", "tier": "경제형", "won_per_doc": 16},
    {"id": "claude-sonnet-4-5-20250929", "tier": "표준형", "won_per_doc": 48}
  ]
}
```

**Anthropic이 2개인 것이 정상이다.**

- [ ] **Step 5: `SettingsPage.tsx`에 모델 등급 섹션 추가**

`SettingsPage.tsx`의 import에 추가:
```tsx
import { useEffect, useState } from 'react'
import { getJson } from '../lib/api'

type ModelRow = { id: string; tier: string; won_per_doc: number }
type ModelCatalog = Record<string, ModelRow[]>
```

컴포넌트 안에 추가:
```tsx
  const { provider, setProvider, setKey, setModel, keyOf, modelOf } = useLLMSettings()
  const [models, setModels] = useState<ModelCatalog>({})

  useEffect(() => {
    getJson<ModelCatalog>('/api/models').then(setModels).catch(() => setModels({}))
  }, [])
```

"AI 회사" 섹션 **아래**에 삽입:
```tsx
      <section>
        <h2 className="mb-2 font-semibold">모델 등급</h2>
        <div className="space-y-1">
          {(models[provider] ?? []).map((m) => (
            <label key={m.id} className="flex cursor-pointer items-center gap-3 rounded border px-3 py-2">
              <input
                type="radio"
                name="model"
                checked={modelOf(provider) === m.id}
                onChange={() => setModel(provider, m.id)}
              />
              <span className="w-16 font-medium">{m.tier}</span>
              <span className="flex-1 font-mono text-sm text-gray-600">{m.id}</span>
              <span className="text-sm">약 {m.won_per_doc}원</span>
            </label>
          ))}
        </div>
        <p className="mt-2 text-xs text-gray-500">
          말씀자료 1건당 예상 비용입니다. 회사별로 마지막에 고른 등급을 따로 기억합니다.
        </p>
      </section>
```

- [ ] **Step 6: 수동 확인 — Task 4 완료 조건**

`http://localhost:5173/settings`에서:

| 시나리오 | 기대 |
|---|---|
| OpenAI 선택 | 등급 **3개** + 각각 약 2/36/64원 |
| Anthropic으로 전환 | 등급 **2개**로 바뀜 + 약 16/48원 |
| Anthropic에서 표준형 선택 → OpenAI로 갔다가 → Anthropic 복귀 | **표준형이 그대로 선택돼 있음** |
| 처음 방문 시 OpenAI 초기 선택 | **최상위** (`gpt-5.6-sol`) |

- [ ] **Step 7: 커밋**

```bash
git add .
git commit -m "feat: /api/models with per-document cost, model tier selector"
git push
```

---

## Task 5: 프롬프트 L1·L2·L3 + builder + `/api/speech/draft` (3h)

**이 task가 결과물 품질의 전부를 결정한다.**

**Files:**
- Create: `src/policy_writer/prompts/__init__.py`, `l1_identity.py`, `l2_domain.py`, `l3_rules.py`, `builder.py`
- Create: `src/policy_writer/common/quality.py`
- Create: `src/policy_writer/api/speech.py`
- Create: `tests/test_builder.py`, `tests/test_quality.py`
- Create: `scripts/try_draft.py` (한글 안전 시험용 — G14)
- Modify: `api/__init__.py`, `server.py`

**Interfaces:**
- Produces:
  - `SpeechInput` (pydantic) — 14필드. `event_name: str` 필수, 나머지 기본값 있음
  - `build_l4_speech(contexts: list[str] | None) -> str`
  - `build_l5_speech(input: SpeechInput) -> str`
  - `build_speech_prompt(input: SpeechInput, *, contexts=None) -> tuple[str, str]`
  - `quality.check_output(text: str, target_chars: int) -> list[str]`
  - `speech_router` (`POST /api/speech/draft`)

---

- [ ] **Step 1: builder 테스트를 먼저 쓴다**

`tests/test_builder.py`:
```python
import pytest
from pydantic import ValidationError

from policy_writer.prompts.builder import SpeechInput, build_speech_prompt


def _base(**kw) -> SpeechInput:
    return SpeechInput(event_name="청년 주거지원 정책 설명회", **kw)


def test_event_name_is_required():
    with pytest.raises(ValidationError):
        SpeechInput()


def test_defaults_match_spec():
    s = _base()
    assert s.event_type == "축사"
    assert s.target_chars == 1400
    assert s.vip_list == []
    assert s.persona_block == ""


def test_system_prompt_contains_all_three_layers():
    system, _ = build_speech_prompt(_base())
    assert "6단" in system            # L2
    assert "경어체" in system          # L3


def test_user_prompt_contains_event_facts():
    _, user = build_speech_prompt(_base(event_location="세종청사", speaker_role="장관"))
    assert "청년 주거지원 정책 설명회" in user
    assert "세종청사" in user
    assert "장관" in user


def test_persona_block_is_inserted_between_l4_and_l5():
    _, user = build_speech_prompt(
        _base(persona_block="현장에서 답을 찾겠습니다"),
        contexts=["행사계획서 발췌 내용"],
    )
    i_l4 = user.index("행사계획서 발췌 내용")
    i_persona = user.index("현장에서 답을 찾겠습니다")
    i_l5 = user.index("청년 주거지원 정책 설명회")
    assert i_l4 < i_persona < i_l5


def test_empty_persona_block_is_omitted():
    _, user = build_speech_prompt(_base(persona_block="   "))
    assert user.count("---") == 0     # L5 하나뿐이라 구분선이 없다


def test_l4_omitted_when_no_contexts():
    _, user = build_speech_prompt(_base())
    assert "참고자료" not in user


def test_seomyeon_chuksa_switches_to_four_part_structure():
    system, _ = build_speech_prompt(_base(event_type="서면축사"))
    assert "서면축사" in system
    assert "4단" in system
```

- [ ] **Step 2: 실패 확인**

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_builder.py -v
```

- [ ] **Step 3: `l1_identity.py` 작성**

```python
L1_SPEECH = """당신은 대한민국 중앙부처에서 20년간 기관장 말씀자료를 써 온 공보 담당 서기관입니다.

당신이 쓰는 글은 장·차관이 행사장에서 그대로 읽는 원고입니다.
문장이 입에 붙어야 하고, 청중이 한 번 들어 이해할 수 있어야 하며,
사실관계에 한 치의 오류도 있어서는 안 됩니다.

당신은 다음을 절대 하지 않습니다.
- 입력에 없는 통계·수치·연도·인명·기관명을 만들어 내는 것
- 확인되지 않은 정책 성과를 단정적으로 말하는 것
- 특정 정당·정치인을 지지하거나 비판하는 것
"""
```

- [ ] **Step 4: `l2_domain.py` 작성 — 이 파일이 핵심이다**

```python
L2_SPEECH = """# 말씀자료 6단 기틀

구두로 낭독하는 말씀자료는 아래 6단 구조를 따릅니다.
각 단의 괄호 안 숫자는 전체 분량 대비 비중입니다.

1단 호명·인사   (5~10%)   청중을 부르고 인사한다
2단 행사 의의   (10~15%)  이 행사가 왜 중요한지 말한다
3단 감사·예우   (10~15%)  참석자와 관계자에게 감사를 표한다
4단 정책·사례   (50~60%)  ★ 본론. "첫째/둘째/셋째"로 나눠 구체적으로
5단 당부        (5~10%)   청중에게 바라는 바를 말한다
6단 마무리      (5~10%)   축원하고 끝맺는다

## 문서 유형별 강조점

유형이 달라도 위 6단 기틀은 같습니다. **어느 단을 더 두껍게 쓸지만 다릅니다.**

| 유형 | 두껍게 쓸 단 | 성격 |
|---|---|---|
| 축사 | 4단 | 가장 표준적인 형태 |
| 기념사 | 2단 | 행사의 역사적 의의와 유공자에 대한 감사를 강조 |
| 신년사 | 5단 | 새해 각오와 내부 직원에 대한 당부 중심 |
| 격려사 | 5단 | 짧게. 노고를 인정하고 힘을 북돋는 데 집중 |
| 환영사 | 1단 | 외빈·귀빈 호명에 공을 들이고 전체는 매우 짧게 |
| 개회사 | 2단 + 3단 | 행사 개시를 알리고 협조를 구함 |
| 이임사 | 3단 + 5단 | 재임 기간 회고와 후임·동료에 대한 당부 |

## 서면축사는 4단입니다 (예외)

서면축사는 낭독하지 않고 인쇄물에 실립니다. 6단이 아니라 아래 4단을 씁니다.

1단 인사 (약식)   "안녕하십니까" 같은 구두 인사를 쓰지 않습니다.
                  「행사명」 개최를 축하하는 문장으로 바로 시작합니다.
2단 행사 의의
3단 정부 의지
4단 기대 + 서명   마지막 줄에 반드시 소속·직급·이름을 남깁니다.
                  예) 2026년 9월 5일  ○○부 장관 홍길동

## 정형구 사전

1단 호명   "존경하는 [청중] 여러분, 반갑습니다"
2단 의의   "오늘 「[행사명]」을 맞이하여..."
3단 예우   "이 자리를 빛내 주신 [참석자]을 비롯한 모든 분께 감사드립니다"
6단 마무리 "다시 한번 [축하]를 드리며, [기원]합니다. 감사합니다"

## 직급별 어휘

장관       굳건히 · 흔들림 없이
차관       차질없이 · 철저히
실장·국장  체계적으로 · 내실 있게
과장·팀장  함께 · 꾸준히

## 분량 환산

낭독 1분 ≈ 280자
  1분 280자 · 3분 850자 · 5분 1,400자 · 7분 2,000자 · 10분 2,800자

목표 글자수는 반드시 지킵니다. 목표의 90% 미만이면 4단의 사례를 더 씁니다.
"""
```

- [ ] **Step 5: `l3_rules.py` 작성**

```python
L3_SPEECH = """# 작성 절차

1. 행사 정보에서 유형을 확인하고, 해당 유형이 두껍게 쓸 단을 정한다
2. 6단(서면축사는 4단) 각각의 목표 글자수를 분량 비중에 따라 배분한다
3. 4단에는 사용자가 준 핵심 메시지를 "첫째/둘째/셋째"로 나눠 배치한다
4. 다 쓴 뒤 글자수를 세고, 목표의 90%에 못 미치면 4단을 늘린다

# 문체

- 경어체를 씁니다. 종결어미는 `~습니다` / `~겠습니다` 입니다
- 한 문장은 80자를 넘기지 않습니다. 낭독해야 하기 때문입니다
- 어려운 한자어보다 쉬운 우리말을 씁니다

# 금지

- 입력에 없는 숫자를 만들지 않습니다. 통계가 필요한데 주어지지 않았다면 그 문장을 쓰지 않습니다
- 입력에 없는 인명·기관명을 만들지 않습니다
- "피할 표현"으로 지정된 문구는 어떤 형태로도 쓰지 않습니다

# 출력 형식

- 본문만 출력합니다. 제목·머리말·해설·마크다운 표제(`#`)를 붙이지 않습니다
- 단은 **빈 줄 하나**로 구분합니다. 단 번호나 소제목을 쓰지 않습니다
- 코드블록으로 감싸지 않습니다
"""
```

- [ ] **Step 6: `builder.py` 구현**

```python
from pydantic import BaseModel, Field

from policy_writer.prompts.l1_identity import L1_SPEECH
from policy_writer.prompts.l2_domain import L2_SPEECH
from policy_writer.prompts.l3_rules import L3_SPEECH


class SpeechInput(BaseModel):
    event_name: str = Field(..., min_length=1, description="행사명. 비면 400")
    event_type: str = "축사"
    event_date: str = ""
    event_location: str = ""
    speaker_name: str = ""
    speaker_role: str = ""
    speaker_organization: str = ""
    audience: str = ""
    vip_list: list[str] = Field(default_factory=list)
    target_chars: int = 1400
    key_messages: list[str] = Field(default_factory=list)
    quotes_or_anecdotes: list[str] = Field(default_factory=list)
    avoid_phrases: list[str] = Field(default_factory=list)
    persona_block: str = ""


def build_l4_speech(contexts: list[str] | None) -> str:
    """업로드한 행사계획서 발췌. 없으면 빈 문자열."""
    usable = [c.strip() for c in (contexts or []) if c and c.strip()]
    if not usable:
        return ""
    body = "\n\n".join(f"[자료 {i}]\n{c}" for i, c in enumerate(usable, 1))
    return f"# 참고자료\n\n아래는 이번 행사의 참고자료입니다. 사실관계는 이 자료를 따릅니다.\n\n{body}"


def _line(label: str, value: str) -> str:
    return f"- {label}: {value}" if value else ""


def _list_block(label: str, items: list[str]) -> str:
    if not items:
        return ""
    body = "\n".join(f"  - {i}" for i in items)
    return f"- {label}:\n{body}"


def build_l5_speech(input: SpeechInput) -> str:
    rows = [
        _line("행사명", input.event_name),
        _line("문서 유형", input.event_type),
        _line("일시", input.event_date),
        _line("장소", input.event_location),
        _line("발화자", " ".join(x for x in [input.speaker_organization, input.speaker_role, input.speaker_name] if x)),
        _line("청중", input.audience),
        _list_block("주요 참석자 (직급 순)", input.vip_list),
        _line("목표 글자수", f"{input.target_chars}자"),
        _list_block("반드시 넣을 핵심 메시지", input.key_messages),
        _list_block("쓸 수 있는 통계·일화", input.quotes_or_anecdotes),
        _list_block("피할 표현 (어떤 형태로도 쓰지 말 것)", input.avoid_phrases),
    ]
    facts = "\n".join(r for r in rows if r)
    return (
        f"# 이번 행사 정보\n\n{facts}\n\n"
        f"위 정보로 「{input.event_name}」 {input.event_type}를 "
        f"{input.target_chars}자 내외로 작성하십시오."
    )


def build_speech_prompt(input: SpeechInput, *, contexts: list[str] | None = None) -> tuple[str, str]:
    system_prompt = "\n\n".join([L1_SPEECH, L2_SPEECH, L3_SPEECH])

    user_parts: list[str] = []
    l4 = build_l4_speech(contexts)
    if l4:
        user_parts.append(l4)
    if input.persona_block.strip():          # 저장소 없이 폼 값만
        user_parts.append(input.persona_block.strip())
    user_parts.append(build_l5_speech(input))

    return system_prompt, "\n\n---\n\n".join(user_parts)
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_builder.py -v
```
기대: `8 passed`

- [ ] **Step 7: quality 테스트 + 구현**

`tests/test_quality.py`:
```python
from policy_writer.common.quality import check_output


def test_no_warning_when_length_is_fine():
    assert check_output("가" * 1400, 1500) == []


def test_warns_when_empty():
    w = check_output("   ", 1500)
    assert len(w) == 1
    assert "비어" in w[0]


def test_warns_when_too_short():
    w = check_output("가" * 700, 1500)
    assert len(w) == 1
    assert "700" in w[0]
```

`src/policy_writer/common/quality.py`:
```python
def check_output(text: str, target_chars: int) -> list[str]:
    """경고만 담는다. 절대 막지 않는다 — 짧아도 사용자가 손보면 쓸 수 있다."""
    warnings: list[str] = []
    stripped = text.strip()
    if not stripped:
        warnings.append("응답이 비어 있습니다. 다시 시도해 주세요.")
        return warnings
    if len(stripped) < target_chars * 0.6:
        warnings.append(
            f"목표({target_chars}자)보다 짧습니다. 현재 {len(stripped)}자. "
            f"더 높은 등급의 모델을 쓰면 분량이 늘어납니다."
        )
    return warnings
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_quality.py -v
```
기대: `3 passed`

- [ ] **Step 8: `api/speech.py` 구현 — 만든 함수를 그 자리에서 연결한다 (G10)**

```python
from fastapi import APIRouter, Header, Request
from pydantic import BaseModel

from policy_writer.common.keys import norm_provider, resolve_user_key
from policy_writer.common.quality import check_output
from policy_writer.llm import catalog, cost
from policy_writer.llm.client import call_llm
from policy_writer.prompts.builder import SpeechInput, build_speech_prompt

router = APIRouter()


class DraftIn(BaseModel):
    input: SpeechInput
    reference_texts: list[str] = []
    max_tokens: int = 4000
    temperature: float = 0.7


@router.post("/draft")
async def draft(
    payload: DraftIn,
    request: Request,
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),   # G4
    x_llm_model: str | None = Header(default=None),
) -> dict:
    provider = norm_provider(x_llm_provider)
    api_key = resolve_user_key(request, provider)          # 없으면 401
    model_meta = catalog.resolve(provider, x_llm_model)    # 허용목록 밖이면 400

    system_prompt, user_prompt = build_speech_prompt(
        payload.input, contexts=payload.reference_texts
    )
    text, meta = await call_llm(
        provider=provider,
        model_meta=model_meta,
        api_key=api_key,
        system_prompt=system_prompt,
        user_prompt=user_prompt,
        max_tokens=payload.max_tokens,
        temperature=payload.temperature,
    )

    meta["cost_won"] = cost.won_for_usage(
        model_meta, meta["input_tokens"], meta["output_tokens"]
    )

    return {
        "generated_text": text,
        "char_count": len(text.strip()),
        "draft_id": None,                # Task 10 에서 채운다
        "warnings": check_output(text, payload.input.target_chars),
        "save_warning": None,            # Task 10 에서 채운다
        "meta": meta,
    }
```

- [ ] **Step 9: `api/__init__.py`와 `server.py`를 둘 다 고친다**

`api/__init__.py`:
```python
from policy_writer.api.settings import router as settings_router
from policy_writer.api.speech import router as speech_router

__all__ = ["settings_router", "speech_router"]
```

`server.py`의 라우터 자리:
```python
from policy_writer.api import settings_router, speech_router

app.include_router(speech_router, prefix="/api/speech")
app.include_router(settings_router)
```

- [ ] **Step 10: 한글 안전 시험 스크립트를 만든다 (G14)**

`scripts/try_draft.py`:
```python
"""PowerShell ConvertTo-Json 은 한글을 깨뜨린다. 이 스크립트로 시험한다."""
import json
import os
import sys

import httpx

PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-5.6-sol")
KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")

if not KEY:
    sys.exit("환경변수 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 를 설정하세요.")

payload = {
    "input": {
        "event_name": "청년 주거지원 정책 설명회",
        "event_type": sys.argv[1] if len(sys.argv) > 1 else "축사",
        "event_date": "2026년 9월 12일",
        "event_location": "정부세종청사 대강당",
        "speaker_name": "김민수",
        "speaker_role": "장관",
        "speaker_organization": "국토교통부",
        "audience": "청년, 공무원, 전문가",
        "vip_list": ["○○시장", "△△협회장"],
        "target_chars": 1500,
        "key_messages": ["청년 월세 지원 확대", "공공임대 공급 물량 확대"],
        "quotes_or_anecdotes": ["작년 신청자 12만 명"],
        "avoid_phrases": ["만감이 교차"],
        "persona_block": "현장에서 답을 찾겠습니다",
    }
}
headers = {
    "X-LLM-Provider": PROVIDER,
    "X-LLM-Model": MODEL,
    "X-OpenAI-Key" if PROVIDER == "openai" else "X-Anthropic-Key": KEY,
}

res = httpx.post(
    "http://localhost:8010/api/speech/draft",
    json=payload, headers=headers, timeout=180.0,
)
print("HTTP", res.status_code)
data = res.json()
if res.status_code != 200:
    print(json.dumps(data, ensure_ascii=False, indent=2))
    sys.exit(1)

print(data["generated_text"])
print("─" * 50)
print("글자수:", data["char_count"], "/ 경고:", data["warnings"])
print("meta:", json.dumps(data["meta"], ensure_ascii=False))
```

- [ ] **Step 11: 실제로 축사를 뽑아 본다 — Task 5 완료 조건**

```powershell
.\.venv\Scripts\python.exe -m uvicorn policy_writer.server:app --port 8010
# 새 창에서
$env:OPENAI_API_KEY="sk-..."
.\.venv\Scripts\python.exe scripts\try_draft.py
```

눈으로 확인할 것:

| 확인 | 기대 |
|---|---|
| 6단 구조 | 호명 → 의의 → 예우 → 정책(첫째/둘째/셋째) → 당부 → 마무리 |
| 페르소나 반영 | 본문에 "현장에서 답을 찾겠습니다"가 들어감 |
| 금지어 | "만감이 교차"가 **없음** |
| 지어낸 숫자 | 입력에 없는 통계·인명이 **없음** |
| `meta.cost_won` | 값이 채워져 있음 |

`persona_block`을 빈 문자열로 바꿔 한 번 더 돌려서 **해당 문구가 빠지는지** 확인한다.

- [ ] **Step 12: 전체 테스트 + 커밋**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```
기대: `33 passed`

```bash
git add .
git commit -m "feat: 5-layer prompt system and POST /api/speech/draft"
git push
```

---

# Day 2 — 기능이 전부 동작한다 (12시간)

---

## Task 6: 작성 화면 — ★ 1차 완료 (3h)

**Files:**
- Create: `frontend/src/lib/speech-data.ts`, `frontend/src/lib/speechFields.ts`
- Create: `frontend/src/components/Field.tsx`, `frontend/src/components/FormSection.tsx`
- Create: `frontend/src/routes/ResultPanel.tsx`
- Modify: `frontend/src/routes/WritePage.tsx`

**Interfaces:**
- Consumes: `callApi` (Task 3), `POST /api/speech/draft` (Task 5)
- Produces: `EVENT_TYPES`, `AUDIENCES`, `LENGTHS`, `SPEAKER_ROLES`, `speechFields`, `toApiPayload(form) -> SpeechInput`

---

- [ ] **Step 1: `speech-data.ts` — 상수**

```ts
export const EVENT_TYPES = [
  { key: 'chuksa', label: '축사' },
  { key: 'gyenyeomsa', label: '기념사' },
  { key: 'sinnyeonsa', label: '신년사' },
  { key: 'gyeoryeosa', label: '격려사' },
  { key: 'hwanyeongsa', label: '환영사' },
  { key: 'gaehoesa', label: '개회사' },
  { key: 'iimsa', label: '이임사' },
  { key: 'seomyeonchuksa', label: '서면축사' },
] as const

export const AUDIENCES = [
  { key: 'public_servant', label: '공무원' },
  { key: 'citizen', label: '일반 시민' },
  { key: 'expert', label: '전문가' },
  { key: 'student', label: '학생' },
  { key: 'honoree', label: '유공자' },
  { key: 'foreign_guest', label: '외빈' },
  { key: 'industry', label: '산업계' },
  { key: 'media', label: '언론' },
  { key: 'internal_staff', label: '내부 직원' },
  { key: 'local_resident', label: '지역 주민' },
] as const

export const LENGTHS = [
  { key: 'very_short', label: '매우 짧게', chars: 600 },
  { key: 'short', label: '짧게', chars: 900 },
  { key: 'standard', label: '표준', chars: 1500 },
  { key: 'long', label: '길게', chars: 2400 },
  { key: 'very_long', label: '매우 길게', chars: 3500 },
  { key: 'custom', label: '사용자 지정', chars: 1500 },
] as const

export const SPEAKER_ROLES = [
  { key: 'minister', label: '장관' },
  { key: 'vice_minister', label: '차관' },
  { key: 'director_general', label: '실장·국장' },
  { key: 'director', label: '과장·팀장' },
  { key: 'head', label: '기관장' },
] as const

export const CUSTOM_CHARS_MIN = 300
export const CUSTOM_CHARS_MAX = 5000
```

- [ ] **Step 2: `speechFields.ts` — 폼을 데이터로 정의 (G11)**

```ts
import { AUDIENCES, EVENT_TYPES, LENGTHS, SPEAKER_ROLES } from './speech-data'

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

/** ★ 화면은 키를 쓰고, API 로는 한글 라벨을 보낸다. */
export function toApiPayload(form: FormState, customChars: number) {
  const labelOf = (opts: readonly { key: string; label: string }[], key: string) =>
    opts.find((o) => o.key === key)?.label ?? key

  const lengthKey = form.target_chars as string
  const chars =
    lengthKey === 'custom'
      ? customChars
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
    vip_list: form.vip_list as string[],
    target_chars: chars,
    key_messages: form.key_messages as string[],
    quotes_or_anecdotes: form.quotes_or_anecdotes as string[],
    avoid_phrases: form.avoid_phrases as string[],
    persona_block: form.persona_block as string,
  }
}
```

- [ ] **Step 3: `Field.tsx` — 5가지 타입만 그린다**

```tsx
import { FieldSpec } from '../lib/speechFields'

type Props = {
  spec: FieldSpec
  value: string | string[]
  onChange: (v: string | string[]) => void
}

export default function Field({ spec, value, onChange }: Props) {
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
    return (
      <div className="mb-4">
        {label}
        {items.map((item, i) => (
          <div key={i} className="mb-1 flex gap-2">
            <input
              value={item}
              onChange={(e) => onChange(items.map((x, j) => (j === i ? e.target.value : x)))}
              className="flex-1 rounded border px-3 py-2"
            />
            <button
              type="button"
              onClick={() => onChange(items.filter((_, j) => j !== i))}
              className="rounded border px-3"
            >
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
```

- [ ] **Step 4: `ResultPanel.tsx` — 결과 + meta**

```tsx
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
```

- [ ] **Step 5: `WritePage.tsx` — 배열을 map으로 돌린다**

```tsx
import { useState } from 'react'
import { Link } from 'react-router-dom'
import Field from '../components/Field'
import { ApiError, callApi } from '../lib/api'
import { CUSTOM_CHARS_MAX, CUSTOM_CHARS_MIN } from '../lib/speech-data'
import { FormState, initialForm, speechFields, toApiPayload } from '../lib/speechFields'
import ResultPanel, { DraftResult } from './ResultPanel'

export default function WritePage() {
  const [form, setForm] = useState<FormState>(initialForm)
  const [customChars, setCustomChars] = useState(1500)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<{ status: number; message: string } | null>(null)
  const [result, setResult] = useState<DraftResult | null>(null)

  const set = (k: string) => (v: string | string[]) => setForm((f) => ({ ...f, [k]: v }))

  async function submit() {
    setError(null)
    setResult(null)
    if (!(form.event_name as string).trim()) {
      setError({ status: 400, message: '행사명은 필수입니다.' })
      return
    }
    setBusy(true)
    try {
      const data = await callApi<DraftResult>('/api/speech/draft', {
        input: toApiPayload(form, customChars),
      })
      setResult(data)
    } catch (e) {
      const err = e as ApiError
      setError({ status: err.status, message: err.message })
    } finally {
      setBusy(false)
    }
  }

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">말씀자료 작성</h1>

      {speechFields.map((spec) => (
        <div key={spec.key}>
          <Field spec={spec} value={form[spec.key]} onChange={set(spec.key)} />
          {spec.key === 'target_chars' && form.target_chars === 'custom' && (
            <input
              type="number"
              min={CUSTOM_CHARS_MIN}
              max={CUSTOM_CHARS_MAX}
              value={customChars}
              onChange={(e) => setCustomChars(Number(e.target.value))}
              className="-mt-2 mb-4 w-40 rounded border px-3 py-2"
            />
          )}
        </div>
      ))}

      <button
        onClick={submit}
        disabled={busy}
        className="rounded bg-black px-6 py-3 text-white disabled:opacity-50"
      >
        {busy ? '작성 중... (최대 2분)' : '작성'}
      </button>

      {error && (
        <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm">
          {error.message}
          {error.status === 401 && (
            <Link to="/settings" className="ml-2 underline">설정으로 가기</Link>
          )}
        </div>
      )}

      {result && <ResultPanel result={result} />}
    </div>
  )
}
```

- [ ] **Step 6: 줄 수 확인 (G11)**

```powershell
Get-ChildItem frontend\src -Recurse -Include *.tsx,*.ts | ForEach-Object {
  [PSCustomObject]@{ File = $_.Name; Lines = (Get-Content $_ | Measure-Object -Line).Lines }
} | Sort-Object Lines -Descending | Select-Object -First 5
```

**300줄을 넘는 파일이 있으면 쪼갠다.**

- [ ] **Step 7: ★ 1차 완료 확인**

`.\run.ps1` → `http://localhost:5173/write`

| 확인 | 기대 |
|---|---|
| 칸 개수 | **14개가 전부 보인다** |
| 청중 | 칩을 여러 개 고를 수 있다 |
| 핵심 메시지 | [+ 추가]로 줄이 늘고 [−]로 준다 |
| 분량 → 사용자 지정 | 숫자 입력칸이 나타난다 |
| 행사명 비우고 [작성] | "행사명은 필수입니다" |
| 폼 채우고 [작성] | **축사 본문이 화면에 나온다** ← 1차 완료 |
| 결과 상단 | 글자수 · 모델 · 소요시간 · 원화 |
| 설정에서 키 지우고 [작성] | "설정에서 API 키를 먼저 입력해 주세요" + [설정으로 가기] |

- [ ] **Step 8: 커밋**

```bash
git add .
git commit -m "feat: data-driven speech form with result panel (1st milestone)"
git push
```

배포 주소에서도 한 번 돌려 본다.

---

## Task 7: 다운로드 — md + hwpx (2h)

**Files:**
- Create: `src/policy_writer/exporters/__init__.py`, `converters.py`
- Create: `src/policy_writer/api/download.py`, `tests/test_converters.py`
- Modify: `api/__init__.py`, `server.py`, `frontend/src/routes/ResultPanel.tsx`

**Interfaces:**
- Produces:
  - `converters.split_paragraphs(text: str) -> list[str]`
  - `converters.to_markdown(title: str, text: str) -> str`
  - `converters.to_hwpx_bytes(title: str, text: str) -> bytes`
  - `download_router` (`POST /api/download/speech/md`, `/hwpx`)

---

- [ ] **Step 1: 단락 분리 테스트를 쓴다**

`tests/test_converters.py`:
```python
from policy_writer.exporters.converters import split_paragraphs, to_markdown


def test_splits_on_blank_lines():
    text = "첫 단락입니다.\n\n둘째 단락입니다.\n\n\n셋째 단락입니다."
    assert split_paragraphs(text) == ["첫 단락입니다.", "둘째 단락입니다.", "셋째 단락입니다."]


def test_joins_single_newlines_inside_a_paragraph():
    text = "존경하는 여러분,\n반갑습니다.\n\n다음 단락."
    assert split_paragraphs(text) == ["존경하는 여러분, 반갑습니다.", "다음 단락."]


def test_ignores_leading_and_trailing_whitespace():
    assert split_paragraphs("\n\n  본문  \n\n") == ["본문"]


def test_markdown_has_title_heading():
    md = to_markdown("청년 정책 축사", "본문입니다.")
    assert md.startswith("# 청년 정책 축사")
    assert "본문입니다." in md
```

- [ ] **Step 2: 실패 확인 후 `converters.py` 구현**

```python
import re


def split_paragraphs(text: str) -> list[str]:
    """AI 출력은 빈 줄로 단락이 나뉜다. 단락 안의 단일 줄바꿈은 공백으로 합친다."""
    chunks = re.split(r"\n\s*\n+", text.strip())
    out = []
    for c in chunks:
        joined = re.sub(r"\s*\n\s*", " ", c).strip()
        if joined:
            out.append(joined)
    return out


def to_markdown(title: str, text: str) -> str:
    body = "\n\n".join(split_paragraphs(text))
    return f"# {title}\n\n{body}\n"


def to_hwpx_bytes(title: str, text: str) -> bytes:
    """python-hwpx 는 add_paragraph 와 save_to_path 만 쓴다.
    표·이미지·도형은 시도하면 파일이 깨진다."""
    import tempfile
    from pathlib import Path

    from hwpx import HwpxDocument

    doc = HwpxDocument.new()
    doc.add_paragraph(title)
    doc.add_paragraph("")
    for p in split_paragraphs(text):
        doc.add_paragraph(p)

    with tempfile.TemporaryDirectory() as d:
        path = Path(d) / "out.hwpx"
        doc.save_to_path(str(path))
        return path.read_bytes()
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_converters.py -v
```
기대: `4 passed`

- [ ] **Step 3: python-hwpx import를 실제로 확인한다**

```powershell
.\.venv\Scripts\python.exe -c "from hwpx import HwpxDocument; d=HwpxDocument.new(); d.add_paragraph('시험'); d.save_to_path('t.hwpx'); print('ok')"
```

`ImportError`가 나면 패키지 이름이 다른 것이다. `pip index versions python-hwpx`로 확인하고 `pyproject.toml`을 고친다.
생성된 `t.hwpx`를 **한글 프로그램으로 열어 본 뒤 삭제**한다.

- [ ] **Step 4: `api/download.py` — 한글 파일명 (함정 7번)**

```python
from urllib.parse import quote

from fastapi import APIRouter, Response
from pydantic import BaseModel

from policy_writer.exporters.converters import to_hwpx_bytes, to_markdown

router = APIRouter()


class DownloadIn(BaseModel):
    title: str = "말씀자료"
    generated_text: str


def _disposition(filename: str) -> dict:
    # RFC 5987 — filename="..." 로 하면 한글이 깨진다
    return {"Content-Disposition": f"attachment; filename*=UTF-8''{quote(filename)}"}


@router.post("/speech/md")
def download_md(payload: DownloadIn) -> Response:
    body = to_markdown(payload.title, payload.generated_text)
    return Response(
        content=body.encode("utf-8"),
        media_type="text/markdown; charset=utf-8",
        headers=_disposition(f"{payload.title}.md"),
    )


@router.post("/speech/hwpx")
def download_hwpx(payload: DownloadIn) -> Response:
    return Response(
        content=to_hwpx_bytes(payload.title, payload.generated_text),
        media_type="application/vnd.hancom.hwpx",
        headers=_disposition(f"{payload.title}.hwpx"),
    )
```

- [ ] **Step 5: `api/__init__.py`와 `server.py` 둘 다 수정**

```python
# api/__init__.py
from policy_writer.api.download import router as download_router
from policy_writer.api.settings import router as settings_router
from policy_writer.api.speech import router as speech_router

__all__ = ["download_router", "settings_router", "speech_router"]
```

```python
# server.py
app.include_router(speech_router, prefix="/api/speech")
app.include_router(download_router, prefix="/api/download")
app.include_router(settings_router)
```

- [ ] **Step 6: `ResultPanel.tsx`에 다운로드 버튼 추가**

먼저 props 시그니처를 바꾼다. Task 6의 `{ result }: { result: DraftResult }`를 아래로 교체:

```tsx
export default function ResultPanel({
  result,
  title,
}: {
  result: DraftResult
  title: string
}) {
```

그리고 파일 맨 위(컴포넌트 밖)에 다운로드 함수를 추가:
```tsx
async function download(kind: 'md' | 'hwpx', title: string, text: string) {
  const res = await fetch(`/api/download/speech/${kind}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ title, generated_text: text }),
  })
  if (!res.ok) { alert('다운로드에 실패했습니다.'); return }
  const blob = await res.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `${title}.${kind}`
  a.click()
  URL.revokeObjectURL(url)
}
```

```tsx
      <div className="flex gap-2 border-t px-4 py-3">
        <button onClick={() => download('md', title, result.generated_text)}
                className="rounded border px-4 py-2 text-sm">마크다운 받기</button>
        <button onClick={() => download('hwpx', title, result.generated_text)}
                className="rounded border px-4 py-2 text-sm">한글파일 받기</button>
        <button onClick={() => navigator.clipboard.writeText(result.generated_text)}
                className="rounded border px-4 py-2 text-sm">복사</button>
      </div>
```

`WritePage.tsx`에서 `<ResultPanel result={result} title={`${form.event_name}_${labelOf(EVENT_TYPES, form.event_type)}`} />` 로 넘긴다.

- [ ] **Step 7: 수동 확인 — Task 7 완료 조건**

| 확인 | 기대 |
|---|---|
| [한글파일 받기] | 파일이 받아짐 |
| 파일명 | **`청년 주거지원 정책 설명회_축사.hwpx`** — 한글이 안 깨짐 |
| 한글 프로그램으로 열기 | **정상적으로 열림** |
| 단락 | 빈 줄 기준으로 나뉘어 있음 |
| [마크다운 받기] | `# 제목` + 본문 |

- [ ] **Step 8: 커밋**

```bash
git add .
git commit -m "feat: markdown and hwpx download with RFC 5987 filenames"
git push
```

---

## Task 8: 유형 8종 연결 + 유형별 검증 (2h)

**Files:**
- Modify: `src/policy_writer/prompts/l2_domain.py` (필요 시 보강)
- Create: `scripts/try_all_types.py`
- Create: `docs/type-check.md`

**Interfaces:**
- Consumes: `scripts/try_draft.py`(Task 5), `EVENT_TYPES`(Task 6)

---

- [ ] **Step 1: 8종 일괄 시험 스크립트**

`scripts/try_all_types.py`:
```python
"""8종을 한 번씩 돌려 결과를 docs/type-check.md 에 쌓는다."""
import os
import sys
import time
from pathlib import Path

import httpx

TYPES = ["축사", "기념사", "신년사", "격려사", "환영사", "개회사", "이임사", "서면축사"]
TARGET = {"격려사": 900, "환영사": 600}      # 짧은 유형은 목표를 낮춘다

PROVIDER = os.environ.get("TRY_PROVIDER", "openai")
MODEL = os.environ.get("TRY_MODEL", "gpt-5.6-sol")
KEY = os.environ.get("OPENAI_API_KEY") or os.environ.get("ANTHROPIC_API_KEY")
if not KEY:
    sys.exit("환경변수에 키를 설정하세요.")

headers = {
    "X-LLM-Provider": PROVIDER,
    "X-LLM-Model": MODEL,
    "X-OpenAI-Key" if PROVIDER == "openai" else "X-Anthropic-Key": KEY,
}

out = Path("docs/type-check.md")
out.parent.mkdir(exist_ok=True)
lines = [f"# 유형 8종 검증 ({MODEL})\n"]

for t in TYPES:
    target = TARGET.get(t, 1500)
    payload = {"input": {
        "event_name": "청년 주거지원 정책 설명회",
        "event_type": t,
        "event_date": "2026년 9월 12일",
        "event_location": "정부세종청사 대강당",
        "speaker_name": "김민수", "speaker_role": "장관",
        "speaker_organization": "국토교통부",
        "audience": "청년, 공무원",
        "target_chars": target,
        "key_messages": ["청년 월세 지원 확대"],
        "avoid_phrases": ["만감이 교차"],
    }}
    started = time.time()
    res = httpx.post("http://localhost:8010/api/speech/draft",
                     json=payload, headers=headers, timeout=180.0)
    if res.status_code != 200:
        lines.append(f"\n## {t}\n\n❌ HTTP {res.status_code} — {res.text[:200]}\n")
        print(f"{t}: FAIL {res.status_code}")
        continue
    d = res.json()
    text = d["generated_text"]
    lines.append(
        f"\n## {t}\n\n"
        f"- 목표 {target}자 / 실제 {d['char_count']}자 "
        f"({round(d['char_count'] / target * 100)}%)\n"
        f"- 소요 {time.time() - started:.1f}초 · {d['meta']['cost_won']}원\n"
        f"- 금지어 '만감이 교차' 포함: {'❌ 있음' if '만감이 교차' in text else '✅ 없음'}\n\n"
        f"```\n{text}\n```\n"
    )
    print(f"{t}: {d['char_count']}/{target}자")

out.write_text("\n".join(lines), encoding="utf-8")
print(f"\n→ {out}")
```

- [ ] **Step 2: 8종을 전부 돌린다**

```powershell
.\.venv\Scripts\python.exe scripts\try_all_types.py
```

8줄이 전부 성공으로 찍혀야 한다.

- [ ] **Step 3: `docs/type-check.md`를 열어 유형별로 눈으로 확인한다**

| 유형 | 확인할 것 |
|---|---|
| 축사 | 4단(정책·사례)이 가장 두꺼운가 |
| 기념사 | 2단(의의)과 유공자 감사가 강조됐나 |
| 신년사 | 새해·내부 직원 대상 어휘가 나오나 |
| 격려사 | 짧고 노고 인정 중심인가 |
| 환영사 | 1단 외빈 호명에 공을 들였나. 전체가 짧은가 |
| 개회사 | 행사 개시 선언 + 협조 요청이 있나 |
| 이임사 | 회고·당부. **금지어 "만감이 교차"가 없나** |
| **서면축사** | **`안녕하십니까`로 시작하지 않나**. **끝에 서명(소속·직급·이름)이 있나** |

- [ ] **Step 4: 어긋난 유형만 L2를 고친다**

가장 흔한 문제는 **서면축사의 서명 누락**이다. `l2_domain.py`의 서면축사 4단 문단을 강화한다:

```python
4단 기대 + 서명   마지막 줄에 반드시 소속·직급·이름을 남깁니다.
                  이 서명은 생략할 수 없습니다. 본문이 끝나면 빈 줄 하나를 두고
                  다음 형식으로 씁니다.
                  예) 2026년 9월 5일
                      국토교통부 장관 김민수
```

고친 뒤 해당 유형만 다시 돌린다:
```powershell
.\.venv\Scripts\python.exe scripts\try_draft.py 서면축사
```

- [ ] **Step 5: 화면에서 8개를 전부 눌러 본다 — Task 8 완료 조건**

`/write`의 "행사 유형" 드롭다운에 8개가 있고, 각각 작성이 성공하며, **유형마다 톤이 다르다.**

- [ ] **Step 6: 커밋**

```bash
git add .
git commit -m "feat: verify and tune all 8 speech types"
git push
```

---

## Task 9: 파일 올려서 자동 작성 (3h)

**Files:**
- Create: `src/policy_writer/extractors/__init__.py`, `files.py`, `tests/test_extractors.py`
- Modify: `src/policy_writer/api/speech.py` (`/draft-with-docs`, `/auto-draft`)
- Modify: `frontend/src/routes/WritePage.tsx` (업로드 영역)

**Interfaces:**
- Produces:
  - `files.extract_text(filename: str, data: bytes) -> str`
  - `files.is_unsupported(text: str) -> bool`
  - `POST /api/speech/draft-with-docs` (multipart: `input_json`, `plan_file`, `reference_files`)
  - `POST /api/speech/auto-draft` (multipart: `plan_file`)

---

- [ ] **Step 1: 추출기 테스트를 쓴다**

`tests/test_extractors.py`:
```python
from policy_writer.extractors.files import MAX_CHARS, extract_text, is_unsupported


def test_utf8_text():
    assert "한글" in extract_text("a.txt", "한글 본문".encode("utf-8"))


def test_cp949_fallback():
    assert "한글" in extract_text("a.txt", "한글 본문".encode("cp949"))


def test_truncates_to_max_chars():
    assert len(extract_text("a.txt", ("가" * 9999).encode("utf-8"))) <= MAX_CHARS


def test_hwp_returns_guidance_not_exception():
    out = extract_text("a.hwp", b"\x00\x01")
    assert "HWPX" in out
    assert is_unsupported(out)


def test_pptx_returns_guidance():
    out = extract_text("a.pptx", b"\x00\x01")
    assert is_unsupported(out)


def test_normal_text_is_not_flagged_unsupported():
    assert is_unsupported("존경하는 여러분") is False
```

- [ ] **Step 2: 실패 확인 후 `files.py` 구현**

```python
import io
import zipfile
from xml.etree import ElementTree

MAX_CHARS = 5000
UNSUPPORTED_PREFIX = "(미지원)"


def is_unsupported(text: str) -> bool:
    """추출 실패 안내 문자열인지. 이게 프롬프트에 실려 들어가면 안 된다."""
    return text.startswith(UNSUPPORTED_PREFIX)


def _decode(data: bytes) -> str:
    for enc in ("utf-8", "cp949", "euc-kr"):
        try:
            return data.decode(enc)
        except UnicodeDecodeError:
            continue
    return data.decode("utf-8", errors="replace")


def _from_pdf(data: bytes) -> str:
    from pypdf import PdfReader

    reader = PdfReader(io.BytesIO(data))
    pages = reader.pages[:20]
    return "\n".join((p.extract_text() or "") for p in pages)


def _from_docx(data: bytes) -> str:
    import docx

    doc = docx.Document(io.BytesIO(data))
    return "\n".join(p.text for p in doc.paragraphs)


def _from_hwpx(data: bytes) -> str:
    """ZIP 을 열어 Contents/section*.xml 의 <hp:t> 노드를 모은다."""
    texts: list[str] = []
    with zipfile.ZipFile(io.BytesIO(data)) as z:
        names = [n for n in z.namelist() if n.startswith("Contents/section") and n.endswith(".xml")]
        for n in sorted(names):
            root = ElementTree.fromstring(z.read(n))
            for el in root.iter():
                if el.tag.endswith("}t") and el.text:
                    texts.append(el.text)
    return " ".join(texts)


def extract_text(filename: str, data: bytes) -> str:
    """실패해도 예외를 던지지 않고 안내 문자열을 돌려준다."""
    ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

    if ext == "hwp":
        return f"{UNSUPPORTED_PREFIX} .hwp 는 읽을 수 없습니다. HWPX 로 변환 후 업로드 부탁드립니다."
    if ext in {"doc", "ppt", "pptx"}:
        return f"{UNSUPPORTED_PREFIX} .{ext} 는 현재 텍스트 추출을 지원하지 않습니다."

    try:
        if ext == "txt":
            text = _decode(data)
        elif ext == "pdf":
            text = _from_pdf(data)
        elif ext == "docx":
            text = _from_docx(data)
        elif ext == "hwpx":
            text = _from_hwpx(data)
        else:
            return f"{UNSUPPORTED_PREFIX} .{ext or '알 수 없는 형식'} 은 지원하지 않습니다."
    except Exception as e:
        return f"{UNSUPPORTED_PREFIX} 파일을 읽는 중 오류가 발생했습니다: {e}"

    return text.strip()[:MAX_CHARS]
```

```powershell
.\.venv\Scripts\python.exe -m pytest tests/test_extractors.py -v
```
기대: `6 passed`

- [ ] **Step 3: `speech.py`에 업로드 엔드포인트 2개 추가**

`api/speech.py` 맨 아래에:
```python
import json

from fastapi import File, Form, UploadFile

from policy_writer.extractors.files import extract_text, is_unsupported


async def _read_contexts(files: list[UploadFile]) -> tuple[list[str], list[str]]:
    """(프롬프트에 넣을 텍스트, 사용자에게 보여줄 경고)"""
    texts, warnings = [], []
    for f in files:
        if not f or not f.filename:
            continue
        text = extract_text(f.filename, await f.read())
        if is_unsupported(text):
            warnings.append(f"{f.filename}: {text}")   # ★ 프롬프트에는 안 넣는다
        elif text:
            texts.append(text)
    return texts, warnings


@router.post("/draft-with-docs")
async def draft_with_docs(
    request: Request,
    input_json: str = Form(...),
    plan_file: UploadFile | None = File(default=None),
    reference_files: list[UploadFile] = File(default=[]),
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),
    x_llm_model: str | None = Header(default=None),
) -> dict:
    payload = DraftIn(input=SpeechInput(**json.loads(input_json)))
    uploads = ([plan_file] if plan_file else []) + list(reference_files)
    contexts, file_warnings = await _read_contexts(uploads)

    result = await _run_draft(request, payload, contexts, x_llm_provider, x_llm_model)
    result["warnings"] = file_warnings + result["warnings"]
    return result


@router.post("/auto-draft")
async def auto_draft(
    request: Request,
    plan_file: UploadFile = File(...),
    event_name: str = Form(default=""),
    x_llm_provider: str = Header(default=catalog.DEFAULT_PROVIDER),
    x_llm_model: str | None = Header(default=None),
) -> dict:
    contexts, file_warnings = await _read_contexts([plan_file])
    if not contexts:
        raise HTTPException(400, file_warnings[0] if file_warnings else "파일에서 글자를 뽑지 못했습니다.")

    name = event_name.strip() or plan_file.filename.rsplit(".", 1)[0]
    payload = DraftIn(input=SpeechInput(event_name=name, target_chars=1500))
    result = await _run_draft(request, payload, contexts, x_llm_provider, x_llm_model)
    result["warnings"] = file_warnings + result["warnings"]
    return result
```

`/draft` 본문을 `_run_draft`로 뽑아내 세 엔드포인트가 공유하게 한다 (G9):
```python
async def _run_draft(request, payload: DraftIn, contexts: list[str],
                     provider_header: str, model_header: str | None) -> dict:
    provider = norm_provider(provider_header)
    api_key = resolve_user_key(request, provider)
    model_meta = catalog.resolve(provider, model_header)

    system_prompt, user_prompt = build_speech_prompt(payload.input, contexts=contexts)
    text, meta = await call_llm(
        provider=provider, model_meta=model_meta, api_key=api_key,
        system_prompt=system_prompt, user_prompt=user_prompt,
        max_tokens=payload.max_tokens, temperature=payload.temperature,
    )
    meta["cost_won"] = cost.won_for_usage(model_meta, meta["input_tokens"], meta["output_tokens"])
    return {
        "generated_text": text,
        "char_count": len(text.strip()),
        "draft_id": None,
        "warnings": check_output(text, payload.input.target_chars),
        "save_warning": None,
        "meta": meta,
    }
```

`/draft`는 `return await _run_draft(request, payload, payload.reference_texts, x_llm_provider, x_llm_model)` 로 줄인다.
`from fastapi import HTTPException`를 import에 추가한다.

- [ ] **Step 4: 프론트 업로드 영역**

`WritePage.tsx`에 파일 input과 `sendMultipart` 함수를 추가한다.
**`Content-Type`을 직접 지정하지 않는다** — `FormData`를 넘기면 브라우저가 boundary까지 붙여 준다.

```tsx
async function submitWithFiles(files: File[]) {
  const { provider, model, key } = getLLMSettings()
  const fd = new FormData()
  fd.append('input_json', JSON.stringify(toApiPayload(form, customChars)))
  files.forEach((f) => fd.append('reference_files', f))

  const res = await fetch('/api/speech/draft-with-docs', {
    method: 'POST',
    headers: {                                   // Content-Type 을 넣지 않는다
      'X-LLM-Provider': provider,
      'X-LLM-Model': model,
      [provider === 'openai' ? 'X-OpenAI-Key' : 'X-Anthropic-Key']: key,
    },
    body: fd,
  })
  if (!res.ok) throw new ApiError(res.status, (await res.json()).detail)
  return res.json()
}
```

`import { getLLMSettings } from '../hooks/useLLMSettings'`를 추가한다.

- [ ] **Step 5: 수동 확인 — Task 9 완료 조건**

| 시나리오 | 기대 |
|---|---|
| PDF 행사계획서 1개 올리고 [작성] | 축사가 나온다 |
| 결과 검증 | **원본 PDF에 없는 날짜·인명·통계가 없다** (원본과 대조) |
| `.hwp` 올리기 | 노란 경고 띠에 "HWPX로 변환 후 업로드 부탁드립니다" + **본문에 이 문장이 안 들어감** |
| 빈 txt 올리기 | 400 또는 경고. 앱이 안 깨짐 |

- [ ] **Step 6: 커밋**

```bash
git add .
git commit -m "feat: file upload extraction with unsupported-format guard"
git push
```

---

## Task 10: Supabase + 작성 이력 (2h)

**Files:**
- Create: `supabase/migrations/001_init.sql`
- Create: `src/policy_writer/db/__init__.py`, `drafts.py`
- Create: `src/policy_writer/api/drafts.py`
- Modify: `src/policy_writer/api/speech.py` (`_run_draft`에 저장 추가)
- Modify: `api/__init__.py`, `server.py`, `frontend/src/routes/HistoryPage.tsx`

**Interfaces:**
- Produces:
  - `db.drafts.create_draft(event_type, title, form_data, generated_text, llm_meta) -> str`
  - `db.drafts.list_drafts(limit: int = 20) -> list[dict]`
  - `db.drafts.get_draft(draft_id: str) -> dict | None`
  - `db.drafts.delete_draft(draft_id: str) -> None`
  - `db.drafts.is_configured() -> bool`
  - `drafts_router` (`GET /api/drafts`, `GET/DELETE /api/drafts/{id}`)

---

- [ ] **Step 1: `001_init.sql` 작성 후 Supabase에서 실행**

```sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE IF NOT EXISTS public.drafts (
  id             UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
  event_type     TEXT NOT NULL,
  title          TEXT NOT NULL,
  form_data      JSONB NOT NULL DEFAULT '{}'::jsonb,
  generated_text TEXT,
  llm_meta       JSONB DEFAULT '{}'::jsonb,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_drafts_created_at ON public.drafts(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_drafts_event_type ON public.drafts(event_type);

ALTER TABLE public.drafts ENABLE ROW LEVEL SECURITY;
```

Supabase 대시보드 → SQL Editor → New query → 붙여넣기 → Run.

`.env`에 `SUPABASE_URL`과 `SUPABASE_SERVICE_ROLE_KEY`를 채운다.
**`SUPABASE_URL` 끝에 `/rest/v1/`를 붙이지 않는다.** 서버를 재시작한다 (G7, `@lru_cache`).

- [ ] **Step 2: `db/drafts.py` 구현**

```python
import httpx

from policy_writer.config import get_settings

TABLE = "drafts"
TIMEOUT = 15.0


def is_configured() -> bool:
    s = get_settings()
    return bool(s.supabase_url and s.supabase_service_role_key)


def _base() -> tuple[str, dict]:
    s = get_settings()
    url = f"{s.supabase_url.rstrip('/')}/rest/v1/{TABLE}"
    headers = {
        "apikey": s.supabase_service_role_key,
        "Authorization": f"Bearer {s.supabase_service_role_key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    return url, headers


async def create_draft(*, event_type: str, title: str, form_data: dict,
                       generated_text: str, llm_meta: dict) -> str:
    url, headers = _base()
    row = {
        "event_type": event_type,
        "title": title,
        "form_data": form_data,
        "generated_text": generated_text,
        "llm_meta": llm_meta,
    }
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.post(url, headers=headers, json=row)
    res.raise_for_status()
    return res.json()[0]["id"]


async def list_drafts(limit: int = 20) -> list[dict]:
    url, headers = _base()
    params = {"order": "created_at.desc", "limit": str(limit),
              "select": "id,event_type,title,llm_meta,created_at"}
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.get(url, headers=headers, params=params)
    res.raise_for_status()
    return res.json()


async def get_draft(draft_id: str) -> dict | None:
    url, headers = _base()
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.get(url, headers=headers, params={"id": f"eq.{draft_id}"})
    res.raise_for_status()
    rows = res.json()
    return rows[0] if rows else None


async def delete_draft(draft_id: str) -> None:
    url, headers = _base()
    async with httpx.AsyncClient(timeout=TIMEOUT) as c:
        res = await c.delete(url, headers=headers, params={"id": f"eq.{draft_id}"})
    res.raise_for_status()
```

- [ ] **Step 3: `_run_draft`에 저장을 붙인다 — 실패해도 글은 버리지 않는다**

`api/speech.py`의 `_run_draft` 반환문 직전에:
```python
    from policy_writer.db import drafts as drafts_db

    draft_id, save_warning = None, None
    if drafts_db.is_configured():
        try:
            draft_id = await drafts_db.create_draft(
                event_type=payload.input.event_type,
                title=payload.input.event_name,
                form_data=payload.input.model_dump(),
                generated_text=text,
                llm_meta=meta,                      # ★ 모델·비용·소요시간
            )
        except Exception as e:
            save_warning = f"이력 저장에 실패했습니다: {e}"   # 삼키지 않는다
```

반환 dict의 `"draft_id": None` → `draft_id`, `"save_warning": None` → `save_warning`으로 바꾼다.

- [ ] **Step 4: `api/drafts.py`**

```python
from fastapi import APIRouter, HTTPException

from policy_writer.db import drafts as db

router = APIRouter()


def _require_db() -> None:
    if not db.is_configured():
        raise HTTPException(503, "이력 기능이 설정되지 않았습니다 (Supabase 미설정).")


@router.get("")
async def list_all(limit: int = 20) -> dict:
    _require_db()
    return {"drafts": await db.list_drafts(limit)}


@router.get("/{draft_id}")
async def get_one(draft_id: str) -> dict:
    _require_db()
    row = await db.get_draft(draft_id)
    if not row:
        raise HTTPException(404, "해당 이력을 찾을 수 없습니다.")
    return row


@router.delete("/{draft_id}")
async def delete_one(draft_id: str) -> dict:
    _require_db()
    await db.delete_draft(draft_id)
    return {"ok": True}
```

`api/__init__.py`와 `server.py`를 **둘 다** 수정:
```python
app.include_router(speech_router, prefix="/api/speech")
app.include_router(download_router, prefix="/api/download")
app.include_router(drafts_router, prefix="/api/drafts")
app.include_router(settings_router)
```

- [ ] **Step 5: `HistoryPage.tsx`**

```tsx
import { useEffect, useState } from 'react'
import { getJson } from '../lib/api'

type Row = {
  id: string
  event_type: string
  title: string
  llm_meta: { model?: string; cost_won?: number }
  created_at: string
}

export default function HistoryPage() {
  const [rows, setRows] = useState<Row[]>([])
  const [error, setError] = useState<string | null>(null)
  const [open, setOpen] = useState<{ generated_text: string } | null>(null)

  useEffect(() => {
    getJson<{ drafts: Row[] }>('/api/drafts?limit=20')
      .then((d) => setRows(d.drafts))
      .catch(() => setError('이력을 불러오지 못했습니다. Supabase가 설정되지 않았을 수 있습니다.'))
  }, [])

  if (error) return <p className="text-sm text-gray-600">{error}</p>

  return (
    <div>
      <h1 className="mb-6 text-2xl font-bold">작성 이력</h1>
      {rows.length === 0 && <p className="text-sm text-gray-600">아직 작성한 문서가 없습니다.</p>}
      <ul className="divide-y">
        {rows.map((r) => (
          <li key={r.id} className="flex cursor-pointer items-center gap-3 py-3"
              onClick={() => getJson<{ generated_text: string }>(`/api/drafts/${r.id}`).then(setOpen)}>
            <span className="w-20 shrink-0 text-sm text-gray-500">{r.event_type}</span>
            <span className="flex-1 truncate">{r.title}</span>
            <span className="shrink-0 text-xs text-gray-500">
              {r.llm_meta?.model} · {r.llm_meta?.cost_won}원
            </span>
            <span className="shrink-0 text-xs text-gray-400">
              {new Date(r.created_at).toLocaleDateString('ko-KR')}
            </span>
          </li>
        ))}
      </ul>
      {open && (
        <article className="mt-6 whitespace-pre-wrap rounded border p-4 leading-relaxed">
          {open.generated_text}
        </article>
      )}
    </div>
  )
}
```

- [ ] **Step 6: 수동 확인 — Task 10 완료 조건**

| 시나리오 | 기대 |
|---|---|
| 축사를 하나 작성 | 응답 `draft_id`가 uuid |
| `/history` 방문 | 목록에 뜨고 **모델명·비용이 같이 보임** |
| 항목 클릭 | 본문이 다시 열림 |
| `.env`에서 `SUPABASE_URL` 지우고 **서버 재시작** → 작성 | **축사는 정상 생성됨.** `draft_id`가 `null` |
| 그 상태로 `/history` | "Supabase가 설정되지 않았을 수 있습니다" 안내 (앱이 안 깨짐) |
| 일부러 `SUPABASE_SERVICE_ROLE_KEY`를 틀리게 → 작성 | 본문은 나오고 **회색 띠에 `save_warning`** |

- [ ] **Step 7: 커밋**

```bash
git add .
git commit -m "feat: supabase draft history with llm_meta and save_warning"
git push
```

---

# Day 3 — 남에게 보여줄 수 있다 (8시간)

---

## Task 11: 오류 화면 + 모바일 (2h)

**Files:**
- Modify: `frontend/src/routes/WritePage.tsx`, `SettingsPage.tsx`, `App.tsx`
- Create: `frontend/src/components/ErrorBanner.tsx`

---

- [ ] **Step 1: `ErrorBanner.tsx`로 오류 표시를 한 곳에 모은다**

```tsx
import { Link } from 'react-router-dom'

const HINT: Record<number, string> = {
  400: '입력값을 확인해 주세요.',
  401: '설정에서 API 키를 확인해 주세요.',
  404: '요청한 항목을 찾을 수 없습니다.',
  502: 'AI 서버가 응답하지 않습니다. 잠시 후 다시 시도해 주세요.',
  503: '이 기능은 아직 설정되지 않았습니다.',
  504: '시간이 초과되었습니다. 분량을 줄이고 다시 시도해 주세요.',
}

export default function ErrorBanner({ status, message }: { status: number; message: string }) {
  return (
    <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm">
      <p className="font-medium">{message}</p>
      <p className="mt-1 text-gray-600">{HINT[status] ?? '잠시 후 다시 시도해 주세요.'}</p>
      {status === 401 && <Link to="/settings" className="mt-2 inline-block underline">설정으로 가기</Link>}
    </div>
  )
}
```

`WritePage.tsx`의 인라인 오류 블록을 `<ErrorBanner {...error} />`로 교체한다.

- [ ] **Step 2: 오류 시나리오 5개를 전부 눌러 본다**

| 만드는 법 | 기대 |
|---|---|
| 설정에서 키 지우고 [작성] | "설정에서 API 키를 먼저 입력해 주세요" + [설정으로 가기] |
| 틀린 키로 [작성] | "인증 실패 — API 키를 다시 확인해 주세요" |
| 행사명 비우고 [작성] | "행사명은 필수입니다" |
| 백엔드를 끄고 [작성] | 앱이 안 깨지고 오류 띠가 뜬다 |
| Supabase 미설정 상태로 `/history` | 안내 문구 |

**어느 경우에도 흰 화면이 뜨면 안 된다.**

- [ ] **Step 3: 모바일 폭에서 확인**

브라우저 개발자도구 → 375px 폭.

| 확인 | 조치 |
|---|---|
| 가로 스크롤이 생기나 | `max-w-3xl`에 `px-4` 추가 |
| 청중 칩이 넘치나 | 이미 `flex-wrap` — 확인만 |
| 버튼이 잘리나 | `w-full sm:w-auto` |
| 상단 nav가 겹치나 | `flex-wrap` 추가 |

- [ ] **Step 4: 커밋**

```bash
git add .
git commit -m "feat: unified error banner and mobile layout fixes"
git push
```

---

## Task 12: 모델 등급별 비교 실측 (1h) ★ 포트폴리오의 핵심

**Files:**
- Create: `scripts/compare_models.py`
- Create: `docs/model-comparison.md`
- Modify: `README.md` (비교표 갱신)

---

- [ ] **Step 1: 비교 스크립트**

`scripts/compare_models.py`:
```python
"""같은 축사를 모델별로 돌려 비교표를 만든다. 원본 gov-writer 에 없는 데이터다."""
import os
import time
from pathlib import Path

import httpx

TARGET = 1500
PAYLOAD = {"input": {
    "event_name": "청년 주거지원 정책 설명회",
    "event_type": "축사",
    "event_date": "2026년 9월 12일",
    "event_location": "정부세종청사 대강당",
    "speaker_name": "김민수", "speaker_role": "장관",
    "speaker_organization": "국토교통부",
    "audience": "청년, 공무원, 전문가",
    "vip_list": ["○○시장", "△△협회장"],
    "target_chars": TARGET,
    "key_messages": ["청년 월세 지원 확대", "공공임대 공급 물량 확대"],
    "quotes_or_anecdotes": ["작년 신청자 12만 명"],
    "avoid_phrases": ["만감이 교차"],
    "persona_block": "현장에서 답을 찾겠습니다",
}}

CATALOG = httpx.get("http://localhost:8010/api/models", timeout=10).json()
KEYS = {"openai": os.environ.get("OPENAI_API_KEY"),
        "anthropic": os.environ.get("ANTHROPIC_API_KEY")}

rows = ["| 회사 | 등급 | 모델 | 글자수 | 소요 | 1건당 | 6단 | 분량준수 |",
        "|---|---|---|---:|---:|---:|:---:|---:|"]

for provider, models in CATALOG.items():
    key = KEYS.get(provider)
    for m in models:
        if not key:
            rows.append(f"| {provider} | {m['tier']} | `{m['id']}` | — | — | {m['won_per_doc']}원 | — | — |")
            print(f"{m['id']}: 건너뜀 (키 없음)")
            continue
        headers = {
            "X-LLM-Provider": provider,
            "X-LLM-Model": m["id"],
            "X-OpenAI-Key" if provider == "openai" else "X-Anthropic-Key": key,
        }
        started = time.time()
        try:
            res = httpx.post("http://localhost:8010/api/speech/draft",
                             json=PAYLOAD, headers=headers, timeout=180.0)
            res.raise_for_status()
        except Exception as e:
            rows.append(f"| {provider} | {m['tier']} | `{m['id']}` | ❌ {str(e)[:30]} | — | — | — | — |")
            print(f"{m['id']}: FAIL {e}")
            continue
        d = res.json()
        chars = d["char_count"]
        secs = time.time() - started
        rows.append(
            f"| {provider} | {m['tier']} | `{m['id']}` | {chars:,} | {secs:.0f}초 | "
            f"{d['meta']['cost_won']}원 | ✅ | {round(chars / TARGET * 100)}% |"
        )
        print(f"{m['id']}: {chars}자 / {secs:.0f}초")
        Path(f"docs/samples/{m['id']}.md").parent.mkdir(parents=True, exist_ok=True)
        Path(f"docs/samples/{m['id']}.md").write_text(d["generated_text"], encoding="utf-8")

out = Path("docs/model-comparison.md")
out.write_text(
    f"# 모델 비교 실측\n\n행사: 청년 주거지원 정책 설명회 · 유형: 축사 · 목표 {TARGET}자\n\n"
    + "\n".join(rows) + "\n", encoding="utf-8")
print(f"\n→ {out}")
```

- [ ] **Step 2: 돌린다**

```powershell
$env:OPENAI_API_KEY="sk-..."
# Anthropic 키가 있으면
$env:ANTHROPIC_API_KEY="sk-ant-..."
.\.venv\Scripts\python.exe scripts\compare_models.py
```

**최소 OpenAI 3칸은 채워져야 한다.** Anthropic 키가 없으면 2칸은 `—`로 남긴다 — 그게 정직한 상태다.

- [ ] **Step 3: `gpt-5.6-terra`가 400을 내면**

`catalog.py` 주석대로 대응한다. 두 가지 중 하나:
1. 모델 id를 `gpt-4o`로 교체하고 가격을 그 모델 기준으로 갱신
2. 표준형 칸을 빼고 OpenAI 2등급으로 간다

**추측한 id를 새로 넣지 않는다** (G3). 어느 쪽이든 `catalog.py` 맨 위 확인 날짜를 갱신한다.

- [ ] **Step 4: `docs/samples/`의 결과물을 눈으로 비교한다**

| 비교 항목 | 봐야 할 것 |
|---|---|
| 분량 | 경제형이 목표의 절반에서 멈추는가 |
| 6단 | 6개 단이 다 있는가, 4단이 두꺼운가 |
| 자기소개 | 발화자 이름이 본문에 나오는가 |
| 통계 | "12만 명"을 썼는가 |
| 금지어 | "만감이 교차"가 없는가 |
| 페르소나 | "현장에서 답을 찾겠습니다"가 들어갔는가 |

- [ ] **Step 5: README의 비교표를 실제 값으로 갱신**

`README.md`의 「모델 비교 실측」 표를 `docs/model-comparison.md` 내용으로 교체하고,
「지원 모델」 표의 검증 상태(📄 → ✅)를 실제로 호출에 성공한 모델만 바꾼다.

- [ ] **Step 6: 커밋**

```bash
git add .
git commit -m "docs: model comparison measurements across tiers"
git push
```

---

## Task 13: 글 품질 다듬기 (3h) 🔴 자르면 안 되는 것

**Files:**
- Modify: `src/policy_writer/prompts/l2_domain.py`, `l3_rules.py`

**이 task는 코드가 아니라 글을 고치는 일이다.** 시간을 아끼지 않는다.

---

- [ ] **Step 1: 기준선을 만든다**

```powershell
.\.venv\Scripts\python.exe scripts\try_all_types.py
copy docs\type-check.md docs\type-check-before.md
```

- [ ] **Step 2: 4종을 골라 문제를 적는다**

축사·기념사·이임사·서면축사 4종을 소리 내어 읽고, 아래를 종이에 적는다.

| 자주 나오는 문제 | L2·L3에서 고칠 곳 |
|---|---|
| 4단이 추상적이다 ("최선을 다하겠습니다"만 반복) | L2 4단에 "각 항목마다 구체적 수단이나 일정을 한 문장씩 붙일 것" 추가 |
| 문장이 길어 낭독이 힘들다 | L3 문체에 "한 문장 80자" 재강조 + 예시 문장 추가 |
| 정형구를 그대로 베낀다 | L2 정형구 사전에 "그대로 쓰지 말고 행사 성격에 맞게 변형할 것" 추가 |
| 6단 마무리가 밋밋하다 | L2 6단에 유형별 축원 문구 예시 3개 추가 |
| 서면축사에 서명이 빠진다 | Task 8 Step 4 참고 — 더 강하게 |

- [ ] **Step 3: 한 번에 하나씩 고치고 그때마다 돌린다**

```powershell
.\.venv\Scripts\python.exe scripts\try_draft.py 축사
```

**한 번에 여러 곳을 고치면 무엇이 효과가 있었는지 알 수 없다.** 하나 고치고 → 돌리고 → 나아졌으면 유지, 아니면 되돌린다.

- [ ] **Step 4: 8종 전체를 다시 돌려 회귀를 확인한다**

```powershell
.\.venv\Scripts\python.exe scripts\try_all_types.py
```

`docs/type-check-before.md`와 비교한다. **한 유형을 고치다 다른 유형이 나빠지지 않았는지** 본다.

- [ ] **Step 5: 완료 판정 — Task 13 완료 조건**

만든 글을 읽고 **"손보면 쓰겠다"**는 생각이 드는가.
안 들면 Step 2로 돌아간다. 이 판정이 이 프로젝트의 존재 이유다.

- [ ] **Step 6: 커밋**

```bash
git add .
git commit -m "feat: tune L2/L3 prompts for output quality across 4 types"
git push
```

---

## Task 14: 재배포 + 문서 마감 (2h)

**Files:**
- Modify: `README.md` (구축 단계 체크박스, 버전)
- Create: `docs/screenshots/`

---

- [ ] **Step 1: Render 환경변수를 확인한다**

Render 대시보드 → Environment:

```
ENVIRONMENT=production        ← 🔴 있는지 눈으로 확인
SUPABASE_URL=...
SUPABASE_SERVICE_ROLE_KEY=...
OPENAI_API_KEY=               ← 비어 있는지 확인
ANTHROPIC_API_KEY=            ← 비어 있는지 확인
```

- [ ] **Step 2: 배포 후 보안 확인 3가지 🔴**

| 주소 | 기대 | 아니면 |
|---|---|---|
| `https://<주소>/api/local-keys` | **`{"keys":{}}`** | `ENVIRONMENT`가 없다. 즉시 설정하고 **AI 키를 폐기·재발급** |
| `https://<주소>/api/info` | `"environment": "production"` | 위와 같음 |
| `https://<주소>/api/models` | JSON (HTML 아님) | SPA 폴백 순서 확인 (G8) |

`git log --all --full-history -- .env`가 **비어 있는지** 확인한다. 결과가 있으면 키를 폐기하고 재발급한다.

- [ ] **Step 3: 배포 주소에서 처음부터 끝까지 한 바퀴**

| # | 동작 | 기대 |
|---|---|---|
| 1 | 홈 접속 | 화면이 뜬다 |
| 2 | 설정 → 회사·모델·키 입력 → [연결 시험] | "정상 연결되었습니다" |
| 3 | 작성 → 14칸 채우고 [작성] | 축사가 나온다 |
| 4 | 결과 상단 | 모델·시간·비용이 보인다 |
| 5 | [한글파일 받기] | 받아서 한글 프로그램에서 열린다 |
| 6 | 이력 | 방금 것이 목록에 있다 |
| 7 | **남의 폰으로 1~6 반복** | 전부 동작 |

- [ ] **Step 4: 화면 사진 4장**

`docs/screenshots/`에 저장: `hub.png`, `write.png`, `result.png`, `settings.png`.
**설정 화면 사진에 실제 키가 찍히지 않게** 한다 (`type="password"`라 가려지지만 확인).

- [ ] **Step 5: README 마감**

1. 「구축 단계」의 `☐`를 완료한 것만 `☑`로
2. 「지원 모델」의 검증 상태를 Task 12 실측 결과로
3. 「모델 비교 실측」 표를 `docs/model-comparison.md`로 교체
4. 맨 위 버전을 `v0.1.0 (구축 중)` → **`v1.0.0`**
5. 배포 주소를 제목 아래에 추가
6. 화면 사진 4장을 「주요 기능」 아래에 삽입
7. 「문서」 표에 `PLAN.md` 한 줄 추가

- [ ] **Step 6: 최종 확인 + 커밋**

```powershell
.\.venv\Scripts\python.exe -m pytest -v
```

기대: **`43 passed`**

| 파일 | 개수 | 만든 task |
|---|---:|---|
| `test_config.py` | 2 | 1 |
| `test_catalog.py` | 7 | 3 |
| `test_keys.py` | 4 | 3 |
| `test_client_body.py` | 5 | 3 |
| `test_cost.py` | 4 | 4 |
| `test_builder.py` | 8 | 5 |
| `test_quality.py` | 3 | 5 |
| `test_converters.py` | 4 | 7 |
| `test_extractors.py` | 6 | 9 |
| **합계** | **43** | |

```bash
git add .
git commit -m "docs: v1.0.0 — screenshots, measured comparison, completed checklist"
git push
```

---

# 최종 완료 판정

## 기능
- [ ] 유형 8개가 다 동작하고 유형마다 톤이 다르다
- [ ] md·hwpx 다운로드가 되고 hwpx가 한글 프로그램에서 열린다
- [ ] PDF를 올려 자동 작성이 된다
- [ ] `/history`에 이력이 남고 다시 열린다

## 견고함
- [ ] 키가 없어도 앱이 안 깨지고 안내가 뜬다
- [ ] Supabase를 꺼도 축사 생성은 된다
- [ ] 틀린 모델 id → 400, 틀린 키 → 401이 각각 다른 메시지로 뜬다
- [ ] `pytest`가 전부 통과한다

## 보안 🔴
- [ ] 배포 주소의 `/api/local-keys`가 `{"keys":{}}`
- [ ] `/api/info`가 `"environment": "production"`
- [ ] git 이력에 `.env`가 없다

## 포트폴리오
- [ ] 모델 비교표에 최소 3칸이 채워져 있다
- [ ] 남의 폰으로 배포 주소에서 처음부터 끝까지 된다
- [ ] 만든 글을 보고 "손보면 쓰겠다"는 생각이 든다

---

# 시간이 모자라면

| 순서 | 자를 것 | 자른 뒤에도 남는 것 |
|---|---|---|
| 1 | Task 11의 모바일 대응 | 컴퓨터에서는 정상 |
| 2 | Task 9 자동 작성 | 폼으로 직접 쓰는 건 됨 |
| 3 | Task 10 이력 화면 | 저장은 됨, 화면만 없음 |
| 4 | Task 4 모델 선택 → 회사별 기본 1개 고정 | 축사는 그대로 나옴 |
| 5 | Task 7 hwpx | md로 대체 |

## 🔴 절대 자르면 안 되는 것

| | | 왜 |
|---|---|---|
| ① | **Task 2 배포** | 링크가 없으면 보여줄 수가 없다 |
| ② | **Task 11 오류 화면** | 데모 도중 깨지면 그걸로 끝이다 |
| ③ | **Task 13 글 품질 3시간** | 글이 별로면 만든 의미가 없다 |
