import { Routes, Route } from 'react-router-dom'
import { Toaster } from '@radix-ui/react-toast'
import Layout from './components/Layout'
import LoginPage from './pages/LoginPage'
import DashboardPage from './pages/DashboardPage'
import SignalsPage from './pages/SignalsPage'
import PortfolioPage from './pages/PortfolioPage'
import JournalPage from './pages/JournalPage'
import InsightsPage from './pages/InsightsPage'
import BacktestsPage from './pages/BacktestsPage'
import { AuthProvider, useAuth } from './contexts/AuthContext'

function AppContent() {
  const { isAuthenticated } = useAuth()

  if (!isAuthenticated) {
    return <LoginPage />
  }

  return (
    <Layout>
      <Routes>
        <Route path="/" element={<DashboardPage />} />
        <Route path="/signals" element={<SignalsPage />} />
        <Route path="/portfolio" element={<PortfolioPage />} />
        <Route path="/journal" element={<JournalPage />} />
        <Route path="/insights" element={<InsightsPage />} />
        <Route path="/backtests" element={<BacktestsPage />} />
      </Routes>
    </Layout>
  )
}

function App() {
  return (
    <AuthProvider>
      <AppContent />
      <Toaster />
    </AuthProvider>
  )
}

export default App