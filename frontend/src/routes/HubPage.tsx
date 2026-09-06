import { Link } from 'react-router-dom'
import { History, Settings } from 'lucide-react'
import { EVENT_TYPES } from '../lib/speech-data'
import { EVENT_TYPE_META } from '../lib/event-type-meta'
import EventTypeCard from '../components/EventTypeCard'

const SECONDARY_LINK_CLASS =
  'flex flex-col items-center justify-center gap-1 rounded-xl border border-slate-200 bg-white px-2 py-3 text-xs text-slate-700 transition-all hover:border-slate-300 active:scale-[0.98] sm:flex-row sm:justify-start sm:gap-2 sm:px-4 sm:text-sm'

export default function HubPage() {
  return (
    <div className="min-h-screen bg-gradient-to-br from-white via-slate-50 to-blue-50 p-4 sm:p-6">
      <div className="mx-auto max-w-4xl">
        <header className="pt-6 text-center sm:pt-8 sm:pb-12 pb-8">
          <span className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700">
            <span className="h-1.5 w-1.5 rounded-full bg-blue-500" />
            AI 말씀자료 초안 생성
          </span>
          <h1 className="mt-4 text-2xl font-bold text-slate-900 sm:text-3xl">말씀자료 작성기</h1>
          <p className="mt-2 text-sm text-slate-600 sm:text-base">
            유형을 고르면 그 유형이 선택된 채 작성 화면으로 이동합니다.
          </p>
        </header>

        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
          {EVENT_TYPES.map((t) => (
            <EventTypeCard
              key={t.key}
              to={`/write?type=${t.key}`}
              icon={EVENT_TYPE_META[t.key].icon}
              label={t.label}
              description={EVENT_TYPE_META[t.key].description}
            />
          ))}
        </div>

        <div className="mt-6 grid grid-cols-2 gap-3">
          <Link to="/history" className={SECONDARY_LINK_CLASS}>
            <History className="h-4 w-4 text-slate-500" />
            작성 이력
          </Link>
          <Link to="/settings" className={SECONDARY_LINK_CLASS}>
            <Settings className="h-4 w-4 text-slate-500" />
            설정
          </Link>
        </div>

        <footer className="mt-12 text-center text-xs text-slate-400 sm:mt-16">
          정부부처 말씀자료 초안 작성 도구 · 최종 검수는 담당자가 진행해 주세요
        </footer>
      </div>
    </div>
  )
}
