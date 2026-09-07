import { APP_PASSWORD_STORAGE_KEY } from '../lib/api'

// 0 은 죽은 코드가 아니다 — api.ts:34 가 네트워크 실패/타임아웃 이전의 연결 실패 시
// 실제로 던지는 값이다 (백엔드가 꺼져 있거나 인터넷이 끊긴 경우).
// 422 는 없다 — server.py 의 RequestValidationError 핸들러가 422 를 400 으로 바꾼다.
const HINT: Record<number, string> = {
  0: '인터넷 연결이나 서버 상태를 확인해 주세요.',
  400: '입력값을 확인해 주세요.',
  401: '접속 암호가 올바르지 않거나 서버 키 설정에 문제가 있습니다. 다시 로그인해 보고, 그래도 안 되면 담당자에게 문의해 주세요.',
  404: '요청한 항목을 찾을 수 없습니다.',
  502: 'AI 서버가 응답하지 않습니다. 잠시 후 다시 시도해 주세요.',
  503: '이 기능은 아직 설정되지 않았습니다.',
  504: '시간이 초과되었습니다. 분량을 줄이고 다시 시도해 주세요.',
}

// 401 은 설정 화면(API 키 입력칸 없음)으로 보내봐야 할 수 있는 게 없다 —
// 접속 암호를 지우고 다시 로그인하게 하는 쪽이 실제로 도움이 된다.
function reLogin() {
  localStorage.removeItem(APP_PASSWORD_STORAGE_KEY)
  window.location.reload()
}

export default function ErrorBanner({ status, message }: { status: number; message: string }) {
  return (
    <div className="mt-4 rounded border border-red-300 bg-red-50 px-4 py-3 text-sm">
      <p className="font-medium">{message}</p>
      <p className="mt-1 text-gray-600">{HINT[status] ?? '잠시 후 다시 시도해 주세요.'}</p>
      {status === 401 && (
        <button type="button" onClick={reLogin} className="mt-2 inline-block underline">
          다시 로그인
        </button>
      )}
    </div>
  )
}
