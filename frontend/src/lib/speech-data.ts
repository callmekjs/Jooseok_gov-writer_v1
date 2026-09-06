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
