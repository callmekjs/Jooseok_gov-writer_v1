import {
  PartyPopper,
  Landmark,
  Sunrise,
  HeartHandshake,
  Users,
  DoorOpen,
  LogOut,
  FileSignature,
  type LucideIcon,
} from 'lucide-react'

type Meta = { icon: LucideIcon; description: string }

/** 홈 카드용 아이콘·한 줄 설명. 키·라벨의 유일한 출처는 speech-data.ts 의 EVENT_TYPES 이고,
 *  여기서는 화면 표시용 부가 정보만 같은 키로 붙인다.
 *  설명 문구는 src/policy_writer/prompts/l2_domain.py 의 유형별 강조점 표를 옮겼다. */
export const EVENT_TYPE_META: Record<string, Meta> = {
  chuksa: { icon: PartyPopper, description: '가장 표준적인 형태의 축하 인사' },
  gyenyeomsa: { icon: Landmark, description: '행사의 역사적 의의와 유공자 감사 중심' },
  sinnyeonsa: { icon: Sunrise, description: '새해 각오와 내부 직원 당부 중심' },
  gyeoryeosa: { icon: HeartHandshake, description: '노고를 인정하고 힘을 북돋기. 짧게' },
  hwanyeongsa: { icon: Users, description: '외빈·귀빈 호명 중심. 짧게' },
  gaehoesa: { icon: DoorOpen, description: '행사 개시를 알리고 협조를 구함' },
  iimsa: { icon: LogOut, description: '재임 기간 회고와 후임·동료 당부' },
  seomyeonchuksa: { icon: FileSignature, description: '낭독 없이 인쇄물에 싣는 축사. 끝에 서명' },
}
