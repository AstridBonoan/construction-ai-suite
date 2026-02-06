import React from 'react'
import styles from './RiskTrendChart.module.css'

interface RiskTrendChartProps {
  data?: Array<{ date: string; risk: number }>
}

const RiskTrendChart: React.FC<RiskTrendChartProps> = ({
  data = [
    { date: 'Jan', risk: 35 },
    { date: 'Feb', risk: 42 },
    { date: 'Mar', risk: 38 },
    { date: 'Apr', risk: 51 },
    { date: 'May', risk: 58 },
    { date: 'Jun', risk: 65 },
    { date: 'Jul', risk: 72 }
  ]
}) => {
  const maxRisk = 100
  const chartWidth = 600
  const chartHeight = 250
  const padding = 40

  const points = data.map((d, i) => ({
    x: padding + (i / (data.length - 1)) * (chartWidth - 2 * padding),
    y: chartHeight - padding - (d.risk / maxRisk) * (chartHeight - 2 * padding),
    risk: d.risk,
    date: d.date
  }))

  const pathD = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ')

  const [hoveredIndex, setHoveredIndex] = React.useState<number | null>(null)

  return (
    <div className={styles.container}>
      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className={styles.chart}>
        {/* Grid lines */}
        {[0, 25, 50, 75, 100].map((val) => (
          <g key={`grid-${val}`}>
            <line
              x1={padding}
              y1={chartHeight - padding - (val / 100) * (chartHeight - 2 * padding)}
              x2={chartWidth - padding}
              y2={chartHeight - padding - (val / 100) * (chartHeight - 2 * padding)}
              className={styles.gridLine}
            />
            <text
              x={padding - 8}
              y={chartHeight - padding - (val / 100) * (chartHeight - 2 * padding) + 4}
              className={styles.gridLabel}
              textAnchor="end"
            >
              {val}%
            </text>
          </g>
        ))}

        {/* X-axis */}
        <line
          x1={padding}
          y1={chartHeight - padding}
          x2={chartWidth - padding}
          y2={chartHeight - padding}
          stroke="#d1d5db"
          strokeWidth="1"
        />

        {/* Y-axis */}
        <line
          x1={padding}
          y1={padding}
          x2={padding}
          y2={chartHeight - padding}
          stroke="#d1d5db"
          strokeWidth="1"
        />

        {/* Risk area fill */}
        <defs>
          <linearGradient id="riskGradient" x1="0%" y1="0%" x2="0%" y2="100%">
            <stop offset="0%" style={{ stopColor: '#ef4444', stopOpacity: 0.2 }} />
            <stop offset="100%" style={{ stopColor: '#ef4444', stopOpacity: 0.05 }} />
          </linearGradient>
        </defs>
        <path
          d={`${pathD} L ${points[points.length - 1].x} ${chartHeight - padding} L ${padding} ${chartHeight - padding} Z`}
          fill="url(#riskGradient)"
        />

        {/* Risk line */}
        <path
          d={pathD}
          className={styles.line}
          stroke="#ef4444"
          strokeWidth="2"
          fill="none"
        />

        {/* Data points */}
        {points.map((p, i) => (
          <circle
            key={`point-${i}`}
            cx={p.x}
            cy={p.y}
            r={hoveredIndex === i ? 5 : 3}
            className={styles.point}
            onMouseEnter={() => setHoveredIndex(i)}
            onMouseLeave={() => setHoveredIndex(null)}
          />
        ))}

        {/* Tooltip */}
        {hoveredIndex !== null && (
          <g>
            <rect
              x={points[hoveredIndex].x - 40}
              y={points[hoveredIndex].y - 50}
              width="80"
              height="40"
              rx="4"
              className={styles.tooltip}
            />
            <text
              x={points[hoveredIndex].x}
              y={points[hoveredIndex].y - 32}
              className={styles.tooltipText}
              textAnchor="middle"
            >
              {points[hoveredIndex].risk}%
            </text>
            <text
              x={points[hoveredIndex].x}
              y={points[hoveredIndex].y - 18}
              className={styles.tooltipDate}
              textAnchor="middle"
            >
              {data[hoveredIndex].date}
            </text>
          </g>
        )}

        {/* X-axis labels */}
        {points.map((p, i) => (
          i % 2 === 0 && (
            <text
              key={`label-${i}`}
              x={p.x}
              y={chartHeight - padding + 18}
              className={styles.xLabel}
              textAnchor="middle"
            >
              {data[i].date}
            </text>
          )
        ))}
      </svg>
    </div>
  )
}

export default RiskTrendChart
