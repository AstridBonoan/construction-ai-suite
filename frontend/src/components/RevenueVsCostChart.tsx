import React from 'react'
import styles from './RevenueVsCostChart.module.css'

interface FinancialData {
  period: string
  revenue: number
  cost: number
}

interface RevenueVsCostChartProps {
  data?: FinancialData[]
}

const RevenueVsCostChart: React.FC<RevenueVsCostChartProps> = ({
  data = [
    { period: 'Week 1', revenue: 50000, cost: 45000 },
    { period: 'Week 2', revenue: 120000, cost: 95000 },
    { period: 'Week 3', revenue: 200000, cost: 155000 },
    { period: 'Week 4', revenue: 280000, cost: 240000 },
    { period: 'Week 5', revenue: 350000, cost: 310000 },
    { period: 'Week 6', revenue: 420000, cost: 385000 },
    { period: 'Week 7', revenue: 480000, cost: 445000 },
    { period: 'Week 8', revenue: 520000, cost: 490000 }
  ]
}) => {
  const chartWidth = 600
  const chartHeight = 300
  const padding = { top: 30, right: 20, bottom: 50, left: 60 }
  const plotWidth = chartWidth - padding.left - padding.right
  const plotHeight = chartHeight - padding.top - padding.bottom

  const maxValue = Math.max(...data.flatMap(d => [d.revenue, d.cost]))
  const [hoveredPeriod, setHoveredPeriod] = React.useState<string | null>(null)

  const points = data.map((d, i) => ({
    x: padding.left + (i / (data.length - 1)) * plotWidth,
    revenueY: padding.top + plotHeight - (d.revenue / maxValue) * plotHeight,
    costY: padding.top + plotHeight - (d.cost / maxValue) * plotHeight,
    revenue: d.revenue,
    cost: d.cost,
    period: d.period
  }))

  const revenuePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.revenueY}`).join(' ')
  const costPath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.costY}`).join(' ')

  return (
    <div className={styles.container}>
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className={styles.chart}>
        {/* Grid lines */}
        {[0, 0.25, 0.5, 0.75, 1].map((val) => (
          <g key={`grid-${val}`}>
            <line
              x1={padding.left}
              y1={padding.top + val * plotHeight}
              x2={chartWidth - padding.right}
              y2={padding.top + val * plotHeight}
              className={styles.gridLine}
            />
            <text
              x={padding.left - 8}
              y={padding.top + val * plotHeight + 4}
              className={styles.gridLabel}
              textAnchor="end"
            >
              ${((1 - val) * maxValue / 1000).toFixed(0)}k
            </text>
          </g>
        ))}

        {/* Axes */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={chartHeight - padding.bottom}
          stroke="#1f2937"
          strokeWidth="2"
        />
        <line
          x1={padding.left}
          y1={chartHeight - padding.bottom}
          x2={chartWidth - padding.right}
          y2={chartHeight - padding.bottom}
          stroke="#1f2937"
          strokeWidth="2"
        />

        {/* Y-axis label */}
        <text
          x={15}
          y={padding.top + plotHeight / 2}
          textAnchor="middle"
          className={styles.axisLabel}
          transform={`rotate(-90 15 ${padding.top + plotHeight / 2})`}
        >
          Amount ($)
        </text>

        {/* Cost area fill */}
        <defs>
          <linearGradient id="costGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#fbbf24', stopOpacity: 0.2 }} />
            <stop offset="100%" style={{ stopColor: '#fbbf24', stopOpacity: 0.05 }} />
          </linearGradient>
          <linearGradient id="revenueGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#10b981', stopOpacity: 0.2 }} />
            <stop offset="100%" style={{ stopColor: '#10b981', stopOpacity: 0.05 }} />
          </linearGradient>
        </defs>

        {/* Revenue area */}
        <path
          d={`${revenuePath} L ${points[points.length - 1].x} ${chartHeight - padding.bottom} L ${padding.left} ${chartHeight - padding.bottom} Z`}
          fill="url(#revenueGradient)"
        />

        {/* Cost area */}
        <path
          d={`${costPath} L ${points[points.length - 1].x} ${chartHeight - padding.bottom} L ${padding.left} ${chartHeight - padding.bottom} Z`}
          fill="url(#costGradient)"
        />

        {/* Revenue line */}
        <path
          d={revenuePath}
          className={styles.line}
          stroke="#10b981"
          strokeWidth="3"
          fill="none"
        />

        {/* Cost line */}
        <path
          d={costPath}
          className={styles.line}
          stroke="#f59e0b"
          strokeWidth="3"
          fill="none"
        />

        {/* Data points and interaction */}
        {points.map((p, i) => (
          <g key={`period-${i}`}>
            {/* Revenue points */}
            <circle
              cx={p.x}
              cy={p.revenueY}
              r={hoveredPeriod === p.period ? 5 : 3}
              fill="#10b981"
              className={styles.point}
              onMouseEnter={() => setHoveredPeriod(p.period)}
              onMouseLeave={() => setHoveredPeriod(null)}
            />

            {/* Cost points */}
            <circle
              cx={p.x}
              cy={p.costY}
              r={hoveredPeriod === p.period ? 5 : 3}
              fill="#f59e0b"
              className={styles.point}
              onMouseEnter={() => setHoveredPeriod(p.period)}
              onMouseLeave={() => setHoveredPeriod(null)}
            />

            {/* Period label */}
            <text
              x={p.x}
              y={chartHeight - padding.bottom + 16}
              className={styles.xLabel}
              textAnchor="middle"
            >
              {p.period}
            </text>

            {/* Tooltip */}
            {hoveredPeriod === p.period && (
              <g>
                <rect
                  x={p.x - 60}
                  y={p.revenueY - 55}
                  width="120"
                  height="50"
                  rx="4"
                  fill="white"
                  stroke="#374151"
                  strokeWidth="1"
                />
                <text x={p.x} y={p.revenueY - 40} className={styles.tooltipLabel} textAnchor="middle">
                  {p.period}
                </text>
                <text x={p.x} y={p.revenueY - 26} className={styles.tooltipRevenue} textAnchor="middle">
                  Rev: ${(p.revenue / 1000).toFixed(0)}k
                </text>
                <text x={p.x} y={p.revenueY - 12} className={styles.tooltipCost} textAnchor="middle">
                  Cost: ${(p.cost / 1000).toFixed(0)}k
                </text>
              </g>
            )}
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendLine} style={{ backgroundColor: '#10b981' }}></span>
          <span>Revenue</span>
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendLine} style={{ backgroundColor: '#f59e0b' }}></span>
          <span>Cost</span>
        </div>
      </div>
    </div>
  )
}

export default RevenueVsCostChart
