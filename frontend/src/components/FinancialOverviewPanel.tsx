import React from 'react'
import FinancialCard from './FinancialCard'
import RevenueVsCostChart from './RevenueVsCostChart'
import styles from './FinancialOverviewPanel.module.css'

interface FinancialOverviewPanelProps {
  revenue?: number
  cost?: number
  profit?: number
  revenueChange?: number
  costChange?: number
}

const FinancialOverviewPanel: React.FC<FinancialOverviewPanelProps> = ({
  revenue = 520000,
  cost = 490000,
  profit = 30000,
  revenueChange = 5,
  costChange = 3
}) => {
  // DEMO DATA — Replace with real backend integration in Phase 3
  const profitMargin = ((profit / revenue) * 100).toFixed(1)
  const profitStatus = profit > 0 ? 'positive' : profit < 0 ? 'negative' : 'neutral'
  const profitTrend = profit > 0 ? 'up' : 'down'

  return (
    <div className={styles.container}>
      <h2 className={styles.title}>💰 Financial Overview</h2>

      {/* KPI Cards Grid */}
      <div className={styles.cardsGrid}>
        <FinancialCard
          title="Total Revenue"
          value={revenue}
          trend={revenueChange}
          trendDirection="up"
          status="positive"
          icon="📈"
        />
        <FinancialCard
          title="Total Cost"
          value={cost}
          trend={costChange}
          trendDirection="up"
          status="negative"
          icon="📉"
        />
        <FinancialCard
          title="Net Profit"
          value={profit}
          trend={Math.abs(profit) / 100}
          trendDirection={profitTrend as 'up' | 'down'}
          status={profitStatus}
          icon="💵"
        />
        <div className={styles.metricCard}>
          <div className={styles.metricLabel}>Profit Margin</div>
          <div className={styles.metricValue}>{profitMargin}%</div>
          <div className={styles.metricBar}>
            <div
              className={styles.metricBarFill}
              style={{
                width: `${Math.min(100, parseFloat(profitMargin))}%`,
                backgroundColor: parseFloat(profitMargin) > 10 ? '#10b981' : parseFloat(profitMargin) > 5 ? '#f59e0b' : '#ef4444'
              }}
            ></div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className={styles.chartsSection}>
        <div className={styles.chartContainer}>
          <h3 className={styles.chartTitle}>Revenue vs Cost Trend</h3>
          <RevenueVsCostChart />
        </div>
      </div>

      {/* Summary Stats */}
      <div className={styles.summarySection}>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Budget Utilization</span>
          <span className={styles.summaryValue}>{((cost / revenue) * 100).toFixed(1)}%</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Cost Per Day</span>
          <span className={styles.summaryValue}>${(cost / 8 / 1000).toFixed(0)}k</span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Days to Break-Even</span>
          <span className={styles.summaryValue}>
            {profit > 0 ? Math.ceil((cost / (profit / 100)) / 1000).toString() : '∞'}
          </span>
        </div>
        <div className={styles.summaryItem}>
          <span className={styles.summaryLabel}>Cost Trend</span>
          <span className={styles.summaryValue} style={{ color: costChange > 0 ? '#ef4444' : '#10b981' }}>
            {costChange > 0 ? '+' : ''}{costChange}%
          </span>
        </div>
      </div>

      {/* Insights */}
      <div className={styles.insightBox}>
        <p className={styles.insightTitle}>📊 Financial Health Assessment</p>
        <ul className={styles.insightList}>
          <li>Revenue trending {revenueChange > 0 ? 'up' : 'down'} {revenueChange}% week-over-week</li>
          <li>Profit margin at {profitMargin}% — {parseFloat(profitMargin) > 10 ? 'Excellent' : parseFloat(profitMargin) > 5 ? 'Good' : 'Needs attention'}</li>
          <li>Cost control: Costs increased {costChange}% while revenue increased {revenueChange}%</li>
          <li>Current cash position: {profit > 0 ? 'Positive' : 'At risk'} with ${(profit / 1000).toFixed(0)}k net profit</li>
        </ul>
      </div>
    </div>
  )
}

export default FinancialOverviewPanel
