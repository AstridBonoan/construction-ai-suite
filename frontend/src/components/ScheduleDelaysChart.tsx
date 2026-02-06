import React from 'react'
import styles from './ScheduleDelaysChart.module.css'

interface TaskDelay {
  taskName: string
  phase: string
  delayDays: number
  status: 'on-time' | 'delayed' | 'critical'
  category: 'structural' | 'mechanical' | 'electrical' | 'finishing'
}

interface ScheduleDelaysChartProps {
  data?: TaskDelay[]
}

const ScheduleDelaysChart: React.FC<ScheduleDelaysChartProps> = ({
  data = [
    { taskName: 'Foundation', phase: 'Phase 1', delayDays: 0, status: 'on-time', category: 'structural' },
    { taskName: 'Framing', phase: 'Phase 2', delayDays: 2, status: 'delayed', category: 'structural' },
    { taskName: 'HVAC Install', phase: 'Phase 3', delayDays: 5, status: 'delayed', category: 'mechanical' },
    { taskName: 'Electrical', phase: 'Phase 4', delayDays: 8, status: 'critical', category: 'electrical' },
    { taskName: 'Plumbing', phase: 'Phase 3', delayDays: 3, status: 'delayed', category: 'mechanical' },
    { taskName: 'Drywall', phase: 'Phase 5', delayDays: 1, status: 'delayed', category: 'finishing' },
    { taskName: 'Inspect', phase: 'Phase 6', delayDays: 6, status: 'critical', category: 'finishing' }
  ]
}) => {
  // Group by phase
  const phases = Array.from(new Set(data.map(d => d.phase))).sort()
  const categoryColors = {
    structural: '#8b5cf6',
    mechanical: '#f59e0b',
    electrical: '#ef4444',
    finishing: '#10b981'
  }

  const statusColor = {
    'on-time': '#10b981',
    'delayed': '#f59e0b',
    'critical': '#ef4444'
  }

  const chartWidth = 700
  const chartHeight = 350
  const padding = { top: 40, right: 20, bottom: 60, left: 60 }
  const plotWidth = chartWidth - padding.left - padding.right
  const plotHeight = chartHeight - padding.top - padding.bottom

  const maxDelay = Math.max(...data.map(d => d.delayDays), 10)
  const barWidth = plotWidth / phases.length * 0.7
  const barSpacing = plotWidth / phases.length

  const [hoveredTask, setHoveredTask] = React.useState<string | null>(null)

  return (
    <div className={styles.container}>
      <div className={styles.header}>
        <h3 className={styles.title}>Schedule Delays by Phase</h3>
        <p className={styles.subtitle}>Task delays grouped by project phase</p>
      </div>

      <svg viewBox={`0 0 ${chartWidth} ${chartHeight}`} className={styles.chart}>
        {/* Grid lines */}
        {[0, 2, 4, 6, 8, 10].map((val) => (
          <g key={`grid-${val}`}>
            <line
              x1={padding.left}
              y1={padding.top + plotHeight - (val / maxDelay) * plotHeight}
              x2={chartWidth - padding.right}
              y2={padding.top + plotHeight - (val / maxDelay) * plotHeight}
              className={styles.gridLine}
            />
            <text
              x={padding.left - 8}
              y={padding.top + plotHeight - (val / maxDelay) * plotHeight + 4}
              className={styles.gridLabel}
              textAnchor="end"
            >
              {val}d
            </text>
          </g>
        ))}

        {/* Y-axis */}
        <line
          x1={padding.left}
          y1={padding.top}
          x2={padding.left}
          y2={chartHeight - padding.bottom}
          stroke="#d1d5db"
          strokeWidth="1"
        />

        {/* X-axis */}
        <line
          x1={padding.left}
          y1={chartHeight - padding.bottom}
          x2={chartWidth - padding.right}
          y2={chartHeight - padding.bottom}
          stroke="#d1d5db"
          strokeWidth="1"
        />

        {/* Y-axis label */}
        <text
          x={15}
          y={padding.top + plotHeight / 2}
          textAnchor="middle"
          className={styles.axisLabel}
          transform={`rotate(-90 15 ${padding.top + plotHeight / 2})`}
        >
          Delay (Days)
        </text>

        {/* Bars for each phase */}
        {phases.map((phase, phaseIdx) => {
          const phaseTasks = data.filter(d => d.phase === phase)
          const xPos = padding.left + (phaseIdx + 0.5) * barSpacing
          let stackedY = 0

          return (
            <g key={`phase-${phase}`}>
              {phaseTasks.map((task, taskIdx) => {
                const barHeight = (task.delayDays / maxDelay) * plotHeight
                const barY = padding.top + plotHeight - stackedY - barHeight
                const color = hoveredTask === task.taskName ? '#ffeb3b' : statusColor[task.status]
                stackedY += barHeight

                return (
                  <g key={`task-${task.taskName}`}>
                    <rect
                      x={xPos - barWidth / 2}
                      y={barY}
                      width={barWidth}
                      height={barHeight}
                      fill={color}
                      stroke={task.status === 'critical' ? '#fff' : 'none'}
                      strokeWidth="2"
                      className={styles.bar}
                      onMouseEnter={() => setHoveredTask(task.taskName)}
                      onMouseLeave={() => setHoveredTask(null)}
                      style={{ cursor: 'pointer', opacity: hoveredTask === null || hoveredTask === task.taskName ? 1 : 0.6 }}
                    />
                    {/* Tooltip on hover */}
                    {hoveredTask === task.taskName && (
                      <g>
                        <rect
                          x={xPos - 50}
                          y={barY - 50}
                          width="100"
                          height="45"
                          rx="4"
                          fill="white"
                          stroke="#374151"
                          strokeWidth="1"
                        />
                        <text
                          x={xPos}
                          y={barY - 32}
                          className={styles.tooltipText}
                          textAnchor="middle"
                        >
                          {task.taskName}
                        </text>
                        <text
                          x={xPos}
                          y={barY - 18}
                          className={styles.tooltipValue}
                          textAnchor="middle"
                        >
                          {task.delayDays} days
                        </text>
                      </g>
                    )}
                  </g>
                )
              })}

              {/* X-axis label */}
              <text
                x={xPos}
                y={chartHeight - padding.bottom + 18}
                className={styles.xLabel}
                textAnchor="middle"
              >
                {phase}
              </text>
            </g>
          )
        })}
      </svg>

      {/* Legend */}
      <div className={styles.legend}>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: statusColor['on-time'] }}></span>
          On Time
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: statusColor['delayed'] }}></span>
          Delayed
        </div>
        <div className={styles.legendItem}>
          <span className={styles.legendColor} style={{ backgroundColor: statusColor['critical'] }}></span>
          Critical (on critical path)
        </div>
      </div>

      {/* Task summary */}
      <div className={styles.summary}>
        <p>Total Delayed Tasks: {data.filter(d => d.delayDays > 0).length} | Critical Path: {data.filter(d => d.status === 'critical').length}</p>
      </div>
    </div>
  )
}

export default ScheduleDelaysChart
