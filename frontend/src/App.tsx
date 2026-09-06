import { BrowserRouter, Routes, Route } from 'react-router-dom'
import HubPage from './routes/HubPage'
import WritePage from './routes/WritePage'
import HistoryPage from './routes/HistoryPage'
import SettingsPage from './routes/SettingsPage'

// 원본 gov-writer 에는 공용 네비게이션 바가 없다 — 각 페이지가 독립적이고
// 홈으로 돌아가는 링크를 각자 갖는다 (design-reference.md 3절). 홈이 이제
// 유형 8종 + 이력 + 설정으로 가는 카드를 모두 갖췄으므로 상단 nav 를 없애고
// 그 패턴을 따른다. 각 하위 페이지는 자체 "← 홈" 링크를 갖는다.
export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HubPage />} />
        <Route path="/write" element={<WritePage />} />
        <Route path="/history" element={<HistoryPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Routes>
    </BrowserRouter>
  )
}
