import { useState } from 'react';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/Login';
import { Servers } from './pages/Servers';
import Analytics from './pages/Analytics';

type Page = 'servers' | 'analytics';

function MainApp() {
  const { isAuthenticated } = useAuth();
  const [page, setPage] = useState<Page>('servers');

  if (!isAuthenticated) return <Login />;

  return (
    <div style={{ minHeight: '100vh', background: 'var(--color-background, #020817)', color: '#f1f5f9', fontFamily: "'Inter', sans-serif" }}>

      {/* Top-level page tab bar (rendered only when authenticated) */}
      <div style={{
        position: 'sticky', top: 0, zIndex: 50,
        background: 'rgba(2,8,23,0.85)', backdropFilter: 'blur(16px)',
        borderBottom: '1px solid rgba(255,255,255,0.07)',
        display: 'flex', alignItems: 'center',
        padding: '0 24px',
      }}>
        {/* Brand */}
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginRight: 32, padding: '12px 0' }}>
          <div style={{
            width: 32, height: 32, borderRadius: 8,
            background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 14,
          }}>⚡</div>
          <span style={{ fontWeight: 700, fontSize: 14, letterSpacing: '-0.02em', color: '#e2e8f0' }}>
            EnergyAware Sim
          </span>
        </div>

        {/* Nav tabs */}
        {([
          { id: 'servers',   label: '🖥️  Data Center',   desc: 'Server management & workloads' },
          { id: 'analytics', label: '📡  Analytics',      desc: 'Resource monitor & telemetry' },
        ] as { id: Page; label: string; desc: string }[]).map(tab => (
          <button
            key={tab.id}
            onClick={() => setPage(tab.id)}
            title={tab.desc}
            style={{
              padding: '16px 20px',
              background: 'transparent',
              border: 'none',
              borderBottom: page === tab.id ? '2px solid #6366f1' : '2px solid transparent',
              color: page === tab.id ? '#a5b4fc' : '#64748b',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: page === tab.id ? 700 : 500,
              transition: 'all 0.15s',
              letterSpacing: '-0.01em',
            }}
            onMouseEnter={e => { if (page !== tab.id) e.currentTarget.style.color = '#94a3b8'; }}
            onMouseLeave={e => { if (page !== tab.id) e.currentTarget.style.color = '#64748b'; }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Page content */}
      {page === 'servers'   && <Servers />}
      {page === 'analytics' && <Analytics />}
    </div>
  );
}

function App() {
  return (
    <AuthProvider>
      <MainApp />
    </AuthProvider>
  );
}

export default App;
