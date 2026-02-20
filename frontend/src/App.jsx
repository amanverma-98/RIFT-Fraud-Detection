import { useState, useEffect } from 'react'
import { useSelector } from 'react-redux'
import { selectStep } from './store/fraudSlice'
import Header from './components/Header'
import HeroSection from './components/HeroSection'
import UploadZone from './components/UploadZone'
import LogTerminal from './components/LogTerminal'
import Dashboard from './components/Dashboard'
import Graph from './components/Graph'
import BottomTabs from './components/BottomTabs'

export default function App() {
  const step = useSelector(selectStep)
  const isDone = step === 'done'
  const [showUpload, setShowUpload] = useState(false)

  // Show upload when analysis starts
  useEffect(() => {
    if (step !== 'idle') {
      setShowUpload(true)
    }
  }, [step])

  return (
    <div className="flex flex-col min-h-screen bg-bg text-ink font-mono">
      <Header showUpload={showUpload} />

      {isDone ? (
        /* Results shown when analysis is done */
        <main className="flex flex-col flex-1 gap-5 px-6 py-5">
          {/* KPI cards */}
          <Dashboard />

          {/* Main graph */}
          <Graph />

          {/* Bottom tables + log */}
          <BottomTabs />
        </main>
      ) : showUpload || step !== 'idle' ? (
        /* Upload + results section - shown after clicking START ANALYSIS */
        <main className="flex flex-col flex-1 gap-6 px-4 md:px-6 py-6 bg-gradient-to-b from-bg via-surface/5 to-bg relative overflow-hidden">
          {/* Ambient backdrop effect */}
          <div className="absolute inset-0 backdrop-blur-sm bg-gradient-to-br from-emerald-600/5 to-cyan-600/5 pointer-events-none"></div>
          
          <div className="relative z-10 w-full flex flex-col gap-6">
            {/* Upload section with soft dark background */}
            <div className="bg-surface/20 rounded-3xl border border-emerald-600/20 backdrop-blur-lg shadow-2xl shadow-black/20 p-8 md:p-12">
              <UploadZone />
            </div>
            
            {/* Log terminal */}
            <LogTerminal />
          </div>
        </main>
      ) : (
        /* Hero section - initial landing */
        <HeroSection onStartAnalysis={() => setShowUpload(true)} />
      )}
    </div>
  )
}
