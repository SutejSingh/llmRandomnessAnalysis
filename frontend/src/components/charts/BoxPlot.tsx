interface BoxPlotProps {
  min: number
  q25: number
  median: number
  q75: number
  max: number
}

const BoxPlot = ({ min, q25, median, q75, max }: BoxPlotProps) => {
  const width = 600
  const height = 200
  const padding = 80
  const plotWidth = width - 2 * padding
  const plotHeight = height - 2 * padding

  const range = max - min || 1
  const scale = (value: number) => {
    if (range === 0) return padding + plotWidth / 2
    return ((value - min) / range) * plotWidth + padding
  }

  const xMin = scale(min)
  const xQ25 = scale(q25)
  const xMedian = scale(median)
  const xQ75 = scale(q75)
  const xMax = scale(max)

  const boxY = padding + plotHeight / 2 - 30
  const boxHeight = 60
  const whiskerY = boxY + boxHeight / 2

  const minLabelX = Math.max(padding, xMin - 40)
  const q25LabelX = Math.max(xQ25 - 30, minLabelX + 80)
  const q75LabelX = Math.min(xQ75 + 30, width - padding - 80)
  const maxLabelX = Math.min(width - padding, xMax + 40)

  return (
    <div style={{ width: '100%', display: 'flex', flexDirection: 'column', alignItems: 'center', padding: '20px 0' }}>
      <svg width={width} height={height} style={{ border: '1px solid #e0e0e0', borderRadius: '6px', background: 'white' }}>
        <line x1={padding} y1={whiskerY} x2={width - padding} y2={whiskerY} stroke="#000" strokeWidth="2" />
        <line x1={xMin} y1={whiskerY - 10} x2={xMin} y2={whiskerY + 10} stroke="#000" strokeWidth="2" />
        <line x1={xMin} y1={whiskerY} x2={xQ25} y2={whiskerY} stroke="#000" strokeWidth="1" strokeDasharray="3,3" />
        <rect x={Math.min(xQ25, xQ75)} y={boxY} width={Math.abs(xQ75 - xQ25) || 2} height={boxHeight} fill="#f0f0f0" stroke="#000" strokeWidth="2" />
        <line x1={xMedian} y1={boxY} x2={xMedian} y2={boxY + boxHeight} stroke="#000" strokeWidth="3" />
        <line x1={xMax} y1={whiskerY - 10} x2={xMax} y2={whiskerY + 10} stroke="#000" strokeWidth="2" />
        <line x1={xQ75} y1={whiskerY} x2={xMax} y2={whiskerY} stroke="#000" strokeWidth="1" strokeDasharray="3,3" />

        <text x={minLabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">Min</text>
        <text x={q25LabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">Q25</text>
        <text x={xMedian} y={boxY - 15} textAnchor="middle" fontSize="12" fill="#000" fontFamily="Courier New" fontWeight="bold">Median</text>
        <text x={q75LabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">Q75</text>
        <text x={maxLabelX} y={boxY + boxHeight + 25} textAnchor="middle" fontSize="11" fill="#666" fontFamily="Courier New">Max</text>

        <text x={minLabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">{min.toFixed(4)}</text>
        <text x={q25LabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">{q25.toFixed(4)}</text>
        <text x={xMedian} y={boxY - 2} textAnchor="middle" fontSize="10" fill="#000" fontFamily="Courier New" fontWeight="bold">{median.toFixed(4)}</text>
        <text x={q75LabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">{q75.toFixed(4)}</text>
        <text x={maxLabelX} y={boxY + boxHeight + 40} textAnchor="middle" fontSize="10" fill="#666" fontFamily="Courier New">{max.toFixed(4)}</text>
      </svg>

      <div style={{ marginTop: '20px', padding: '15px', background: '#f9f9f9', borderRadius: '6px', border: '1px solid #e0e0e0', width: '100%', maxWidth: width }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '10px', fontFamily: 'Courier New', fontSize: '13px' }}>
          <div><strong>Minimum:</strong> {min.toFixed(4)}</div>
          <div><strong>First Quartile (Q25):</strong> {q25.toFixed(4)}</div>
          <div><strong>Median:</strong> {median.toFixed(4)}</div>
          <div><strong>Third Quartile (Q75):</strong> {q75.toFixed(4)}</div>
          <div><strong>Maximum:</strong> {max.toFixed(4)}</div>
        </div>
      </div>
    </div>
  )
}

export default BoxPlot
