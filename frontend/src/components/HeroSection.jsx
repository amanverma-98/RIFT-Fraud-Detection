export default function HeroSection({ onStartAnalysis }) {
  const handleClick = () => {
    onStartAnalysis?.()
  }

  return (
    <div className="relative min-h-screen flex items-center justify-center overflow-hidden bg-gradient-to-br from-bg via-bg to-surface" id="hero-section">
      {/* Animated background elements */}
      <div className="absolute inset-0 overflow-hidden pointer-events-none">
        {/* Gradient blur orbs */}
        <div className="absolute top-20 left-20 w-96 h-96 bg-emerald-600 rounded-full opacity-10 blur-3xl animate-pulse"></div>
        <div className="absolute bottom-20 right-32 w-80 h-80 bg-cyan-500 rounded-full opacity-10 blur-3xl animate-pulse" style={{ animationDelay: '1s' }}></div>
        <div className="absolute top-1/2 left-1/3 w-72 h-72 bg-emerald-600 rounded-full opacity-5 blur-3xl animate-pulse" style={{ animationDelay: '2s' }}></div>
      </div>

      {/* Grid overlay */}
      <div className="absolute inset-0 opacity-5 pointer-events-none" style={{
        backgroundImage: 'linear-gradient(0deg, transparent 24%, rgba(16, 185, 129, 0.05) 25%, rgba(16, 185, 129, 0.05) 26%, transparent 27%, transparent 74%, rgba(16, 185, 129, 0.05) 75%, rgba(16, 185, 129, 0.05) 76%, transparent 77%, transparent), linear-gradient(90deg, transparent 24%, rgba(16, 185, 129, 0.05) 25%, rgba(16, 185, 129, 0.05) 26%, transparent 27%, transparent 74%, rgba(16, 185, 129, 0.05) 75%, rgba(16, 185, 129, 0.05) 76%, transparent 77%, transparent)',
        backgroundSize: '60px 60px'
      }}></div>

      {/* Content */}
      <div className="relative z-10 text-center max-w-5xl px-6">
        
        {/* Badge */}
        <div className="inline-block mb-8 animate-fadeIn">
          <span className="px-4 py-2 rounded-full bg-emerald-600/20 border border-emerald-600/40 text-emerald-400 text-sm font-semibold tracking-widest">
            FINANCIAL CRIME DETECTION
          </span>
        </div>

        {/* Main heading with gradient text */}
        <h1 className="text-6xl md:text-7xl font-black tracking-tighter mb-6 animate-fadeIn" style={{ animationDelay: '0.1s' }}>
          <span className="bg-gradient-to-r from-emerald-400 via-cyan-400 to-emerald-500 bg-clip-text text-transparent">
            Money Muling
          </span>
          <br />
          <span className="text-ink">Detection Engine</span>
        </h1>

        {/* Subtitle */}
        <p className="text-xl md:text-2xl text-muted mb-12 max-w-3xl mx-auto leading-relaxed animate-fadeIn font-light" style={{ animationDelay: '0.2s' }}>
          Advanced graph-based analysis powered by cutting-edge algorithms to identify suspicious transaction patterns and financial crime rings in real-time.
        </p>

        {/* Feature pills */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-12 animate-fadeIn" style={{ animationDelay: '0.3s' }}>
          <FeaturePill icon="🔍" title="Pattern Detection" desc="Identify complex fraud rings instantly" />
          <FeaturePill icon="📊" title="Graph Analysis" desc="Visual network mapping of transactions" />
          <FeaturePill icon="⚡" title="Real-Time Processing" desc="Analyze thousands of transactions instantly" />
        </div>

        {/* CTA Button */}
        <div className="animate-fadeIn" style={{ animationDelay: '0.4s' }}>
          <button 
            onClick={handleClick}
            className="px-8 py-4 rounded-lg bg-gradient-to-r from-emerald-600 to-emerald-500 text-white font-bold text-lg tracking-widest hover:shadow-2xl hover:shadow-emerald-600/40 transition-all duration-300 transform hover:scale-105 group cursor-pointer"
          >
            <span className="flex items-center justify-center gap-2">
              START ANALYSIS
              <span className="group-hover:translate-x-1 transition-transform">→</span>
            </span>
          </button>
        </div>

        {/* Scroll indicator */}
        <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-bounce">
          <svg className="w-6 h-6 text-emerald-500 opacity-60" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 14l-7 7m0 0l-7-7m7 7V3" />
          </svg>
        </div>
      </div>

      {/* Floating cards background */}
      <div className="absolute bottom-0 left-0 right-0 h-1/3 bg-gradient-to-t from-surface to-transparent"></div>
    </div>
  )
}

function FeaturePill({ icon, title, desc }) {
  return (
    <div className="group p-6 rounded-xl bg-surface/40 border border-emerald-600/20 hover:border-emerald-600/50 hover:bg-emerald-600/10 transition-all duration-300 backdrop-blur-sm">
      <div className="text-3xl mb-3">{icon}</div>
      <h3 className="text-ink font-bold text-lg mb-2">{title}</h3>
      <p className="text-muted text-sm leading-relaxed">{desc}</p>
    </div>
  )
}
