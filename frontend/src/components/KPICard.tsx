import React from 'react'
import styles from './KPICard.module.css'

interface KPICardProps {
  title: string
  value: string | number
  unit?: string
  trend?: 'up' | 'down' | 'neutral'
  trendValue?: number
  status: 'healthy' | 'caution' | 'risk'
  icon?: React.ReactNode
  sparkline?: number[]
}

const KPICard: React.FC<KPICardProps> = ({
  title,
  value,
  unit,
  trend,
  trendValue,
  status,
  icon,
  sparkline
}) => {
  const statusColor = {
    healthy: '#10b981',
    caution: '#f59e0b',
    risk: '#ef4444'
  }

  const trendIcon = {
    up: '↑',
    down: '↓',
    neutral: '→'
  }

  const getTrendColor = () => {
    if (trend === 'up') return status === 'healthy' ? '#10b981' : '#ef4444'
    if (trend === 'down') return status === 'healthy' ? '#ef4444' : '#10b981'
    return '#6b7280'
  }

  return (
    <div className={styles.card}>
      <div className={styles.header}>
        <div className={styles.titleSection}>
          {icon && <span className={styles.icon}>{icon}</span>}
          <h3 className={styles.title}>{title}</h3>
        </div>
        <div
          className={styles.statusBadge}
          style={{ backgroundColor: statusColor[status] }}
        >
          {status.toUpperCase()}
        </div>
      </div>

      <div className={styles.valueSection}>
        <div className={styles.mainValue}>
          <span className={styles.value}>{value}</span>
          {unit && <span className={styles.unit}>{unit}</span>}
        </div>
        {(trend || trendValue) && (
          <div className={styles.trend} style={{ color: getTrendColor() }}>
            <span className={styles.trendIcon}>
              {trend ? trendIcon[trend] : ''}
            </span>
            {trendValue !== undefined && (
              <span className={styles.trendValue}>{trendValue}%</span>
            )}
          </div>
        )}
      </div>

      {sparkline && sparkline.length > 0 && (
        <div className={styles.sparklineContainer}>
          <svg
            className={styles.sparkline}
            viewBox="0 0 100 30"
            preserveAspectRatio="none"
          >
            {/* Simple sparkline path */}
            {/*Render as mini area chart*/}
          </svg>
        </div>
      )}
    </div>
  )
}

export default KPICard
