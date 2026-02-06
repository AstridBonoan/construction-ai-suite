import React from 'react'
import styles from './ChartCard.module.css'

interface ChartCardProps {
  title: string
  subtitle?: string
  children: React.ReactNode
  footer?: string
}

const ChartCard: React.FC<ChartCardProps> = ({
  title,
  subtitle,
  children,
  footer
}) => {
  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <div>
          <h3 className={styles.title}>{title}</h3>
          {subtitle && <p className={styles.subtitle}>{subtitle}</p>}
        </div>
      </div>
      <div className={styles.content}>
        {children}
      </div>
      {footer && <div className={styles.footer}>{footer}</div>}
    </div>
  )
}

export default ChartCard
