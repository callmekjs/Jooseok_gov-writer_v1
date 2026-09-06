import { Link } from 'react-router-dom'
import type { LucideIcon } from 'lucide-react'

type Props = {
  to: string
  icon: LucideIcon
  label: string
  description: string
}

/** 홈 화면의 유형 카드 한 장. 참고서 4절의 카드 클래스를 그대로 쓴다. */
export default function EventTypeCard({ to, icon: Icon, label, description }: Props) {
  return (
    <Link
      to={to}
      className="group flex items-start gap-3 rounded-2xl border border-slate-200 bg-white p-5 transition-all hover:border-blue-300 hover:shadow-md active:scale-[0.98] sm:p-6"
    >
      <span className="shrink-0 rounded-lg bg-blue-50 p-2 transition-colors group-hover:bg-blue-100">
        <Icon className="h-5 w-5 text-blue-600" />
      </span>
      <span className="min-w-0">
        <span className="block text-base font-semibold text-slate-900 sm:text-lg">{label}</span>
        <span className="mt-0.5 block text-xs text-slate-600 sm:text-sm">{description}</span>
      </span>
    </Link>
  )
}
