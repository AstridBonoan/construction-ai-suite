import React from 'react'
import styles from './FinancialCard.module.css'

interface FinancialCardProps {
  title: string
  value: number
  currency?: boolean
  trend?: number
  trendDirection?: 'up' | 'down'
  status?: 'positive' | 'negative' | 'neutral'
  icon?: string
}

const FinancialCard: React.FC<FinancialCardProps> = ({
  title,
  value,
  currency = true,
  trend,
  trendDirection,
  status = 'neutral',
  icon
}) => {
  const statusColor = {
    positive: '#10b981',
    negative: '#ef4444',
    neutral: '#6b7280'
  }

  const trendIcon = trendDirection === 'up' ? '↑' : trendDirection === 'down' ? '↓' : '→'

  const formatValue = (val: number) => {
    if (Math.abs(val) >= 1000000) {
      return `$${(val / 1000000).toFixed(1)}M`
    }
    if (Math.abs(val) >= 1000) {
      return `$${(val / 1000).toFixed(0)}K`
    }
    return `$${val.toFixed(0)}`
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <h4 className={styles.title}>{title}</h4>
        </div>
        <div
          className={styles.statusDot}
          style={{ backgroundColor: statusColor[status] }}
        ></div>
      </div>

      <div className={styles.valueSection}>
        <div className={styles.mainValue}>
          <span className={styles.value}>{currency ? formatValue(value) : value.toFixed(0)}</span>
        </div>
        {trend !== undefined && (
          <div
            className={styles.trend}
            style={{
              color: trendDirection === 'up' && status === 'positive' ? '#10b981' : trendDirection === 'down' && status === 'negative' ? '#10b981' : '#ef4444'
            }}
          >
            <span className={styles.trendIcon}>{trendIcon}</span>
            <span className={styles.trendValue}>{Math.abs(trend)}%</span>
          </div>
        )}
      </div>

      {/* Mini bar under the value */}
      <div className={styles.bar}>
        <div
          className={styles.barFill}
          style={{
            backgroundColor: statusColor[status],
            width: `${Math.min(100, Math.abs(value) / 10000)}%`
          }}
        ></div>
      </div>
    </div>
  )
}

export default FinancialCard
