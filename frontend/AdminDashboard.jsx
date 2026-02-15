import { useState, useEffect } from 'react'
import './App.css'

function AdminDashboard() {
  const [students, setStudents] = useState([])
  const [atRiskStudents, setAtRiskStudents] = useState([])
  const [selectedStudent, setSelectedStudent] = useState(null)
  const [riskData, setRiskData] = useState(null)
  const [loading, setLoading] = useState(true)
  const [view, setView] = useState('all') // 'all' or 'at-risk'

  // Fetch all students on component mount
  useEffect(() => {
    fetchStudents()
    fetchAtRiskStudents()
  }, [])

  const fetchStudents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/students')
      const data = await response.json()
      setStudents(data)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching students:', error)
      setLoading(false)
    }
  }

  const fetchAtRiskStudents = async () => {
    try {
      const response = await fetch('http://localhost:8000/api/students/at-risk')
      const data = await response.json()
      setAtRiskStudents(data)
    } catch (error) {
      console.error('Error fetching at-risk students:', error)
    }
  }

  const fetchRiskData = async (studentId) => {
    try {
      const response = await fetch(`http://localhost:8000/api/risk/${studentId}`)
      const data = await response.json()
      setRiskData(data)
      setSelectedStudent(studentId)
    } catch (error) {
      console.error('Error fetching risk data:', error)
    }
  }

  const getRiskColor = (level) => {
    switch(level) {
      case 'Low': return '#4CAF50'
      case 'Moderate': return '#FF9800'
      case 'High': return '#f44336'
      default: return '#999'
    }
  }

  if (loading) {
    return <div className="loading">Loading students...</div>
  }

  return (
    <div className="App">
      <header className="header">
        <h1>🎓 Student Risk Assessment System</h1>
        <p className="subtitle">AI-Powered Academic Performance Analysis</p>
      </header>

      <div className="stats-bar">
        <div className="stat-card">
          <div className="stat-number">{students.length}</div>
          <div className="stat-label">Total Students</div>
        </div>
        <div className="stat-card warning">
          <div className="stat-number">{atRiskStudents.length}</div>
          <div className="stat-label">At-Risk Students</div>
        </div>
        <div className="stat-card success">
          <div className="stat-number">{students.length - atRiskStudents.length}</div>
          <div className="stat-label">Low Risk Students</div>
        </div>
      </div>

      <div className="view-selector">
        <button 
          className={view === 'all' ? 'active' : ''} 
          onClick={() => setView('all')}
        >
          All Students ({students.length})
        </button>
        <button 
          className={view === 'at-risk' ? 'active' : ''} 
          onClick={() => setView('at-risk')}
        >
          At-Risk Only ({atRiskStudents.length})
        </button>
      </div>

      <div className="main-content">
        <div className="students-list">
          <h2>{view === 'all' ? 'All Students' : 'At-Risk Students'}</h2>
          {(view === 'all' ? students : atRiskStudents).map((student) => (
            <div 
              key={student.id || student.student_id} 
              className={`student-card ${selectedStudent === (student.id || student.student_id) ? 'selected' : ''}`}
              onClick={() => fetchRiskData(student.id || student.student_id)}
            >
              <div className="student-info">
                <div className="student-name">{student.name || student.student_name}</div>
                <div className="student-details">
                  {student.roll_number} • {student.branch}
                </div>
              </div>
              {student.risk_level && (
                <div 
                  className="risk-badge"
                  style={{ backgroundColor: getRiskColor(student.risk_level) }}
                >
                  {student.risk_level}
                </div>
              )}
            </div>
          ))}
        </div>

        <div className="risk-details">
          {!riskData ? (
            <div className="empty-state">
              <h2>👈 Select a student to view risk analysis</h2>
              <p>Click on any student from the list to see detailed risk assessment</p>
            </div>
          ) : (
            <div>
              <div className="risk-header">
                <h2>{riskData.student_name}</h2>
                <div className="risk-score-badge" style={{ backgroundColor: getRiskColor(riskData.risk_level) }}>
                  Risk: {riskData.risk_level}
                </div>
              </div>

              <div className="metrics-grid">
                <div className="metric-card">
                  <div className="metric-label">CGPA</div>
                  <div className="metric-value">{riskData.cgpa}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Attendance</div>
                  <div className="metric-value">{riskData.attendance}%</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Risk Score</div>
                  <div className="metric-value">{riskData.risk_score}</div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Confidence</div>
                  <div className="metric-value">{(riskData.confidence * 100).toFixed(0)}%</div>
                </div>
              </div>

              <div className="section">
                <h3>📊 Performance Indicators</h3>
                <div className="indicator-grid">
                  <div className="indicator">
                    <span className="indicator-label">GPA Trend:</span>
                    <span className={`indicator-value ${riskData.gpa_trend}`}>
                      {riskData.gpa_trend === 'improving' ? '📈' : riskData.gpa_trend === 'declining' ? '📉' : '➡️'} 
                      {riskData.gpa_trend}
                    </span>
                  </div>
                  <div className="indicator">
                    <span className="indicator-label">Failed Subjects:</span>
                    <span className="indicator-value">{riskData.failed_subjects}</span>
                  </div>
                  <div className="indicator">
                    <span className="indicator-label">Branch:</span>
                    <span className="indicator-value">{riskData.branch}</span>
                  </div>
                </div>
              </div>

              {Object.keys(riskData.risk_factors).length > 0 && (
                <div className="section risk-factors">
                  <h3>⚠️ Risk Factors</h3>
                  {Object.entries(riskData.risk_factors).map(([key, value]) => (
                    <div key={key} className="risk-factor-item">
                      <span className="risk-icon">🔴</span>
                      <span>{value}</span>
                    </div>
                  ))}
                </div>
              )}

              {riskData.recommendations.length > 0 && (
                <div className="section recommendations">
                  <h3>💡 Recommendations</h3>
                  {riskData.recommendations.map((rec, index) => (
                    <div key={index} className="recommendation-item">
                      <span className="rec-number">{index + 1}</span>
                      <span>{rec}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

export default AdminDashboard