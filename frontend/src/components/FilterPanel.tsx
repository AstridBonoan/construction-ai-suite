import React from 'react'
import styles from './FilterPanel.module.css'

interface FilterPanelProps {
  onProjectChange?: (project: string) => void
  onDateRangeChange?: (range: string) => void
  onCategoryChange?: (category: string) => void
}

const FilterPanel: React.FC<FilterPanelProps> = ({
  onProjectChange,
  onDateRangeChange,
  onCategoryChange
}) => {
  const [selectedProject, setSelectedProject] = React.useState('riverside-tower')
  const [selectedRange, setSelectedRange] = React.useState('30days')
  const [selectedCategory, setSelectedCategory] = React.useState('all')

  const projects = [
    { id: 'riverside-tower', name: 'Riverside Tower' },
    { id: 'grandview-mall', name: 'Grandview Mall' },
    { id: 'downtown-hq', name: 'Downtown HQ' }
  ]

  const dateRanges = [
    { id: '7days', label: 'Last 7 Days' },
    { id: '30days', label: 'Last 30 Days' },
    { id: '90days', label: 'Last 90 Days' },
    { id: 'all', label: 'All Time' }
  ]

  const categories = [
    { id: 'all', label: 'All Categories' },
    { id: 'cost', label: 'Cost Risk' },
    { id: 'schedule', label: 'Schedule Risk' },
    { id: 'labor', label: 'Labor Risk' },
    { id: 'compliance', label: 'Compliance Risk' }
  ]

  const handleProjectChange = (value: string) => {
    setSelectedProject(value)
    onProjectChange?.(value)
  }

  const handleRangeChange = (value: string) => {
    setSelectedRange(value)
    onDateRangeChange?.(value)
  }

  const handleCategoryChange = (value: string) => {
    setSelectedCategory(value)
    onCategoryChange?.(value)
  }

  return (
    <div className={styles.container}>
      <div className={styles.filterGroup}>
        <label htmlFor="project" className={styles.label}>
          Project
        </label>
        <select
          id="project"
          value={selectedProject}
          onChange={(e) => handleProjectChange(e.target.value)}
          className={styles.select}
        >
          {projects.map((p) => (
            <option key={p.id} value={p.id}>
              {p.name}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.filterGroup}>
        <label htmlFor="dateRange" className={styles.label}>
          Timeframe
        </label>
        <select
          id="dateRange"
          value={selectedRange}
          onChange={(e) => handleRangeChange(e.target.value)}
          className={styles.select}
        >
          {dateRanges.map((r) => (
            <option key={r.id} value={r.id}>
              {r.label}
            </option>
          ))}
        </select>
      </div>

      <div className={styles.filterGroup}>
        <label htmlFor="category" className={styles.label}>
          Risk Category
        </label>
        <select
          id="category"
          value={selectedCategory}
          onChange={(e) => handleCategoryChange(e.target.value)}
          className={styles.select}
        >
          {categories.map((c) => (
            <option key={c.id} value={c.id}>
              {c.label}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}

export default FilterPanel
