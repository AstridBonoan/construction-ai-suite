import React from 'react'
import sample from './mock/phase9_sample.json'
import { Phase9Output } from './types/phase9'
import KPICard from './components/KPICard'
import ChartCard from './components/ChartCard'
import RiskTrendChart from './components/RiskTrendChart'
import ScheduleDelaysChart from './components/ScheduleDelaysChart'
import CostVsScheduleChart from './components/CostVsScheduleChart'
import FinancialOverviewPanel from './components/FinancialOverviewPanel'
import FilterPanel from './components/FilterPanel'
import { BrowserRouter, Routes, Route, useLocation } from 'react-router-dom'
import MondayOnboarding from './components/MondayOnboarding'
import OAuthHandler from './components/OAuthHandler'
import AlertFeed from './components/AlertFeed'
import ExplainabilityPanel from './components/ExplainabilityPanel'
import RiskFactorBreakdown from './components/RiskFactorBreakdown'
import styles from './App.module.css'

import { buildApiUrl } from './config/api';

const getPhase9Url = () => buildApiUrl('/phase9/outputs');

const MainDashboard: React.FC = () => {
  const [mode, setMode] = React.useState<'mock' | 'live'>('mock')
  const [outputs, setOutputs] = React.useState<Phase9Output[] | null>(null)
  const [loading, setLoading] = React.useState(false)

  React.useEffect(() => {
    let cancelled = false

    const load = async () => {
      if (mode === 'mock') {
        setOutputs(sample as any)
        return
      }

      setLoading(true)
      try {
        const url = mode === 'live' ? `${getPhase9Url()}?variant=live` : getPhase9Url()
        const res = await fetch(url)
        if (!res.ok) throw new Error('Network response not ok')
        const data = await res.json()
        if (!cancelled) setOutputs(data)
      } catch (e) {
        // fallback to mock on error
        if (!cancelled) setOutputs(sample as any)
      } finally {
        if (!cancelled) setLoading(false)
      }
    }

    load()
    return () => {
      cancelled = true
    }
  }, [mode])

  const item = outputs?.[0] ?? (sample as any)[0]
  const allItems = outputs || (sample as any)

  return (
    <div className={styles.appContainer}>
      {/* Header */}
      <header className={styles.header}>
        <div className={styles.headerContent}>
          <h1 className={styles.title}>
            <span className={styles.icon}>🏗️</span>
            AI Construction Suite
          </h1>
          <p className={styles.subtitle}>Real-Time Project Intelligence & Risk Management</p>
        </div>
        <div className={styles.headerControls}>
          <button
            onClick={() => {
              setMode('mock')
              window.location.href = '/monday/onboard'
            }}
            data-testid="continue-demo"
            className={`${styles.modeButton} ${mode === 'mock' ? styles.active : ''}`}
          >
            📊 Demo Mode
          </button>
          <button
            onClick={() => setMode('live')}
            disabled={loading}
            className={`${styles.modeButton} ${mode === 'live' ? styles.active : ''}`}
          >
            🔴 Live (Optional)
          </button>
          {loading && <span className={styles.loadingText}>Loading…</span>}
        </div>
      </header>

      {/* Main Content */}
      <main className={styles.main}>
        {/* Filters */}
        <FilterPanel />

        {/* KPI Cards Row */}
        <section className={styles.kpiSection}>
          <KPICard
            title="Overall Project Risk"
            value={Math.round((item?.risk_score ?? 0.65) * 100)}
            unit="%"
            trend="up"
            trendValue={8}
            status={item?.risk_score > 0.7 ? 'risk' : item?.risk_score > 0.5 ? 'caution' : 'healthy'}
            icon="📈"
          />
          <KPICard
            title="Schedule Health"
            value={Math.round((1 - (item?.delay_probability ?? 0.45)) * 100)}
            unit="%"
            trend="down"
            trendValue={5}
            status={item?.delay_probability > 0.5 ? 'risk' : 'caution'}
            icon="📅"
          />
          <KPICard
            title="Cost Variance"
            value={item?.cost_variance_pct?.toFixed(1) ?? '8.2'}
            unit="%"
            trend="down"
            trendValue={2}
            status="caution"
            icon="💰"
          />
          <KPICard
            title="Workforce Reliability"
            value={Math.round(Math.random() * 30 + 65)}
            unit="%"
            trend="down"
            trendValue={3}
            status="caution"
            icon="👥"
          />
          <KPICard
            title="Compliance Risk"
            value={2}
            unit="violations"
            status="warning"
            icon="⚠️"
          />
        </section>

        {/* Charts Grid */}
        <section className={styles.chartsGrid}>
          <ChartCard title="Risk Trend Over Time" subtitle="Last 30 days">
            <RiskTrendChart />
          </ChartCard>
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '20px' }}>
            <ScheduleDelaysChart />
          </div>
        </section>

        <section className={styles.chartsGrid}>
          <div style={{ background: 'white', border: '1px solid #e5e7eb', borderRadius: '8px', padding: '20px' }}>
            <CostVsScheduleChart />
          </div>
          <AlertFeed />
        </section>

        {/* Financial Overview Panel */}
        <section className={styles.fullWidthSection}>
          <FinancialOverviewPanel />
        </section>

        {/* Insights Section */}
        <section className={styles.insightsSection}>
          <div className={styles.insightsPanelContainer}>
            <h2 className={styles.sectionTitle}>🤖 AI Insights & Recommendations</h2>
            <div className={styles.insightsList}>
              <div className={styles.insightItem}>
                <div className={styles.insightDot}></div>
                <p className={styles.insightText}>
                  <strong>Electrical Subcontractor</strong> reliability issues have increased delay risk by <strong>18%</strong>
                </p>
              </div>
              <div className={styles.insightItem}>
                <div className={styles.insightDot}></div>
                <p className={styles.insightText}>
                  <strong>Inspection delays</strong> are now on the critical path. Addressing these could save <strong>5-7 days</strong>
                </p>
              </div>
              <div className={styles.insightItem}>
                <div className={styles.insightDot}></div>
                <p className={styles.insightText}>
                  <strong>Crew B attendance</strong> dropped to 68% this week. Consider staffing reallocation to maintain schedule
                </p>
              </div>
              <div className={styles.insightItem}>
                <div className={styles.insightDot}></div>
                <p className={styles.insightText}>
                  <strong>Material shortage</strong> incoming: Concrete lead time +5 days mid-July. Order now to avoid delay
                </p>
              </div>
              <div className={styles.insightItem}>
                <div className={styles.insightDot}></div>
                <p className={styles.insightText}>
                  <strong>Safety incidents</strong> trending up (5 in 30 days). Compliance training recommended for crew rotation
                </p>
              </div>
            </div>
          </div>

          {/* Explainability */}
          <div style={{ marginTop: 24 }}>
            <ExplainabilityPanel item={item} />
          </div>
        </section>

        {/* Risk Factor Details */}
        <section className={styles.detailsSection}>
          <h2 className={styles.sectionTitle}>Risk Factor Breakdown</h2>
          <RiskFactorBreakdown factors={item.primary_risk_factors} />
        </section>

        {/* Portfolio Table */}
        <section className={styles.portfolioSection}>
          <h2 className={styles.sectionTitle}>Project Portfolio Overview</h2>
          <div className={styles.tableContainer}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Risk Level</th>
                  <th>Schedule Delays</th>
                  <th>Budget Status</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {allItems.slice(0, 3).map((proj: any, idx: number) => (
                  <tr key={idx}>
                    <td className={styles.projectName}>{proj.project_name}</td>
                    <td>
                      <span
                        className={styles.riskBadge}
                        style={{
                          backgroundColor:
                            proj.risk_score > 0.7
                              ? '#ef4444'
                              : proj.risk_score > 0.5
                              ? '#f59e0b'
                              : '#10b981'
                        }}
                      >
                        {proj.risk_score > 0.7 ? 'HIGH' : proj.risk_score > 0.5 ? 'MEDIUM' : 'LOW'}
                      </span>
                    </td>
                    <td>{proj.predicted_delay_days ?? 0} days</td>
                    <td>{proj.cost_variance_pct > 0 ? 'Over Budget' : 'On Track'}</td>
                    <td className={styles.status}>🟢 Active</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      </main>
    </div>
  )
}

const App: React.FC = () => {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/monday/onboard" element={<MondayOnboarding />} />
        <Route path="/monday/oauth/callback" element={<OAuthHandler />} />
        <Route path="/" element={<MainDashboard />} />
        <Route path="*" element={<MainDashboard />} />
      </Routes>
    </BrowserRouter>
  )
}

export default App
