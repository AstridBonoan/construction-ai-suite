import React from 'react'
import styles from './CostVsScheduleChart.module.css'

interface TaskImpact {
  taskName: string
  scheduleDelayDays: number
  costVariance: number
  priority: 'low' | 'medium' | 'high' | 'critical'
  onCriticalPath: boolean
}

interface CostVsScheduleChartProps {
  data?: TaskImpact[]
  correlation?: number
}

const CostVsScheduleChart: React.FC<CostVsScheduleChartProps> = ({
  data = [
    { taskName: 'Electrical', scheduleDelayDays: 8, costVariance: 45000, priority: 'critical', onCriticalPath: true },
    { taskName: 'Inspection', scheduleDelayDays: 6, costVariance: 12000, priority: 'high', onCriticalPath: true },
    { taskName: 'HVAC', scheduleDelayDays: 5, costVariance: 35000, priority: 'high', onCriticalPath: false },
    { taskName: 'Plumbing', scheduleDelayDays: 3, costVariance: 18000, priority: 'medium', onCriticalPath: false },
    { taskName: 'Drywall', scheduleDelayDays: 1, costVariance: 8000, priority: 'medium', onCriticalPath: false },
    { taskName: 'Framing', scheduleDelayDays: 2, costVariance: 22000, priority: 'high', onCriticalPath: true },
    { taskName: 'Foundation', scheduleDelayDays: 0, costVariance: -5000, priority: 'low', onCriticalPath: false },
    { taskName: 'Finishing', scheduleDelayDays: 1, costVariance: 5000, priority: 'low', onCriticalPath: false }
  ],
  correlation = 0.87
}) => {
  const chartWidth = 700
  const chartHeight = 380
  const padding = { top: 40, right: 80, bottom: 60, left: 80 }
  const plotWidth = chartWidth - padding.left - padding.right
  const plotHeight = chartHeight - padding.top - padding.bottom

  // Calculate axis ranges
  const maxDelay = Math.max(...data.map(d => d.scheduleDelayDays), 10)
  const maxCost = Math.max(...data.map(d => Math.abs(d.costVariance)), 50000)
  const minCost = Math.min(...data.map(d => d.costVariance), -10000)

  const [hoveredTask, setHoveredTask] = React.useState<string | null>(null)

  const priorityRadius = {
    low: 4,
    medium: 6,
    high: 8,
    critical: 10
  }

  const priorityColor = {
    low: '#d1d5db',
    medium: '#f59e0b',
    high: '#ef4444',
    critical: '#7c2d12'
  }

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Cost vs Schedule Impact (Correlation: {correlation.toFixed(2)})</h3>
        <p className={styles.subtitle}>Dual-axis analysis: schedule delays vs cost variance</p>
      </div>

      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className={styles.chart}>
        {/* Grid lines (vertical for schedule) */}
        {[0, 2, 4, 6, 8, 10].map((val) => (
          <line
            key={`vgrid-${val}`}
            x1={padding.left + (val / maxDelay) * plotWidth}
            y1={padding.top}
            x2={padding.left + (val / maxDelay) * plotWidth}
            y2={chartHeight - padding.bottom}
            className={styles.gridLine}
          />
        ))}

        {/* Grid lines (horizontal for cost) */}
        {[-50000, -25000, 0, 25000, 50000].map((val) => {
          const normalizedVal = (val - minCost) / (maxCost - minCost)
          return (
            <line
              key={`hgrid-${val}`}
              x1={padding.left}
              y1={padding.top + plotHeight - normalizedVal * plotHeight}
              x2={chartWidth - padding.right}
              y2={padding.top + plotHeight - normalizedVal * plotHeight}
              className={styles.gridLine}
            />
          )
        })}

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

        {/* Right Y-axis for budget % */}
        <line
          x1={chartWidth - padding.right}
          y1={padding.top}
          x2={chartWidth - padding.right}
          y2={chartHeight - padding.bottom}
          stroke="#9ca3af"
          strokeWidth="1"
          strokeDasharray="4"
        />

        {/* Axis labels */}
        <text
          x={padding.left - 8}
          y={padding.top - 8}
          className={styles.axisLabel}
        >
          Cost Variance ($)
        </text>
        <text
          x={padding.left + plotWidth / 2}
          y={chartHeight - 8}
          className={styles.axisLabel}
          textAnchor="middle"
        >
          Schedule Delays (Days)
        </text>

        {/* Left Y-axis ticks and labels */}
        {[-50000, -25000, 0, 25000, 50000].map((val) => {
          const normalizedVal = (val - minCost) / (maxCost - minCost)
          const yPos = padding.top + plotHeight - normalizedVal * plotHeight

          return (
            <g key={`yleft-${val}`}>
              <line x1={padding.left - 4} y1={yPos} x2={padding.left} y2={yPos} stroke="#9ca3af" strokeWidth="1" />
              <text x={padding.left - 8} y={yPos + 4} className={styles.yLabel} textAnchor="end">
                {val / 1000}k
              </text>
            </g>
          )
        })}

        {/* Bottom X-axis ticks */}
        {[0, 2, 4, 6, 8, 10].map((val) => {
          const xPos = padding.left + (val / maxDelay) * plotWidth

          return (
            <g key={`xbottom-${val}`}>
              <line x1={xPos} y1={chartHeight - padding.bottom} x2={xPos} y2={chartHeight - padding.bottom + 4} stroke="#9ca3af" strokeWidth="1" />
              <text x={xPos} y={chartHeight - padding.bottom + 16} className={styles.xLabel} textAnchor="middle">
                {val}d
              </text>
            </g>
          )
        })}

        {/* Data points (scatter) */}
        {data.map((task) => {
          const xPos = padding.left + (task.scheduleDelayDays / maxDelay) * plotWidth
          const normalizedCost = (task.costVariance - minCost) / (maxCost - minCost)
          const yPos = padding.top + plotHeight - normalizedCost * plotHeight
          const radius = priorityRadius[task.priority]
          const color = priorityColor[task.priority]
          const isHovered = hoveredTask === task.taskName

          return (
            <g key={`point-${task.taskName}`}>
              {/* Point */}
              <circle
                cx={xPos}
                cy={yPos}
                r={isHovered ? radius + 3 : radius}
                fill={color}
                stroke={task.onCriticalPath ? '#fff' : 'none'}
                strokeWidth="2"
                className={styles.point}
                onMouseEnter={() => setHoveredTask(task.taskName)}
                onMouseLeave={() => setHoveredTask(null)}
              />

              {/* Tooltip */}
              {isHovered && (
                <g>
                  <rect
                    x={xPos - 65}
                    y={yPos - 60}
                    width="130"
                    height="55"
                    rx="4"
                    fill="white"
                    stroke="#374151"
                    strokeWidth="1"
                  />
                  <text x={xPos} y={yPos - 45} className={styles.tooltipTitle} textAnchor="middle">
                    {task.taskName}
                  </text>
                  <text x={xPos} y={yPos - 31} className={styles.tooltipText} textAnchor="middle">
                    Delay: {task.scheduleDelayDays}d
                  </text>
                  <text x={xPos} y={yPos - 17} className={styles.tooltipText} textAnchor="middle">
                    Cost: ${(task.costVariance / 1000).toFixed(0)}k
                  </text>
                </g>
              )}
            </g>
          )
        })}

        {/* Correlation line annotation */}
        <text x={chartWidth - padding.right - 8} y={padding.top + 16} className={styles.annotation} textAnchor="end">
          r = {correlation.toFixed(2)}
        </text>
      </svg>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendGroup}>
          <span className={styles.legendLabel}>Priority:</span>
          <div className={styles.legendItem}>
            <circle cx="0" cy="0" r="4" fill={priorityColor.low} />
            <span>Low</span>
          </div>
          <div className={styles.legendItem}>
            <circle cx="0" cy="0" r="6" fill={priorityColor.medium} />
            <span>Medium</span>
          </div>
          <div className={styles.legendItem}>
            <circle cx="0" cy="0" r="8" fill={priorityColor.high} />
            <span>High</span>
          </div>
          <div className={styles.legendItem}>
            <circle cx="0" cy="0" r="10" fill={priorityColor.critical} />
            <span>Critical</span>
          </div>
        </div>
        <div className={styles.legendGroup}>
          <span className={styles.legendLabel}>
            ⭐ = On Critical Path
          </span>
        </div>
      </div>

      {/* Insight */}
      <div className={styles.insight}>
        <p className={styles.insightText}>
          <strong>Insight:</strong> Strong correlation ({correlation.toFixed(2)}) indicates that delayed tasks directly impact project costs. 
          Focus on {data.filter(d => d.onCriticalPath && d.scheduleDelayDays > 0)[0]?.taskName || 'critical path'} to reduce both delay and cost impact.
        </p>
      </div>
    </div>
  )
}

export default CostVsScheduleChart
