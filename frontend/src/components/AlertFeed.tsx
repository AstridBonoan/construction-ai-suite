import React from 'react'
import styles from './AlertFeed.module.css'

interface Alert {
  id: string
  severity: 'critical' | 'warning' | 'info'
  title: string
  message: string
  timestamp: Date
  actionLabel?: string
}

interface AlertFeedProps {
  alerts?: Alert[]
}

const AlertFeed: React.FC<AlertFeedProps> = ({
  alerts = [
    {
      id: '1',
      severity: 'critical',
      title: 'Schedule at Risk',
      message: 'Electrical subcontractor delays impacting critical path',
      timestamp: new Date(Date.now() - 30 * 60000)
    },
    {
      id: '2',
      severity: 'warning',
      title: 'Workforce Issue',
      message: 'Crew B attendance rate dropped to 68% this week',
      timestamp: new Date(Date.now() - 2 * 3600000)
    },
    {
      id: '3',
      severity: 'warning',
      title: 'Compliance Alert',
      message: '2 safety violations logged; inspection pending',
      timestamp: new Date(Date.now() - 4 * 3600000)
    },
    {
      id: '4',
      severity: 'info',
      title: 'Material Update',
      message: 'Concrete shortage expected mid-July; lead time +5 days',
      timestamp: new Date(Date.now() - 8 * 3600000)
    }
  ]
}) => {
  const severityConfig = {
    critical: { color: '#ef4444', label: 'CRITICAL', icon: '🔴' },
    warning: { color: '#f59e0b', label: 'WARNING', icon: '🟡' },
    info: { color: '#3b82f6', label: 'INFO', icon: '🔵' }
  }

  const formatTime = (date: Date) => {
    const now = new Date()
    const diffMs = now.getTime() - date.getTime()
    const diffMins = Math.floor(diffMs / 60000)
    const diffHours = Math.floor(diffMs / 3600000)
    const diffDays = Math.floor(diffMs / 86400000)

    if (diffMins < 1) return 'now'
    if (diffMins < 60) return `${diffMins}m ago`
    if (diffHours < 24) return `${diffHours}h ago`
    if (diffDays < 7) return `${diffDays}d ago`
    return date.toLocaleDateString()
  }

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Recent Alerts</h3>
      <div className={styles.feed}>
        {alerts.length === 0 ? (
          <div className={styles.empty}>
            <p>No alerts at this time</p>
          </div>
        ) : (
          alerts.map((alert) => {
            const config = severityConfig[alert.severity]
            return (
              <div key={alert.id} className={styles.alertItem}>
                <div className={styles.alertHeader}>
                  <div className={styles.metadata}>
                    <span
                      className={styles.severityBadge}
                      style={{ backgroundColor: config.color }}
                    >
                      {config.icon} {config.label}
                    </span>
                    <span className={styles.timestamp}>{formatTime(alert.timestamp)}</span>
                  </div>
                </div>
                <div className={styles.content}>
                  <h4 className={styles.alertTitle}>{alert.title}</h4>
                  <p className={styles.alertMessage}>{alert.message}</p>
                </div>
                {alert.actionLabel && (
                  <button className={styles.actionButton}>{alert.actionLabel}</button>
                )}
              </div>
            )
          })
        )}
      </div>
    </div>
  )
}

export default AlertFeed
