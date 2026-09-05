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
