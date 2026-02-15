import { useState } from 'react'
import './StudentDashboard.css'

function StudentDashboard() {
  const [isLoggedIn, setIsLoggedIn] = useState(false)
  const [rollNumber, setRollNumber] = useState('')
  const [studentData, setStudentData] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [chatMessages, setChatMessages] = useState([])
  const [currentQuestion, setCurrentQuestion] = useState('')
  const [chatLoading, setChatLoading] = useState(false)

  // Handle login
  const handleLogin = async (e) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const response = await fetch(
        `http://localhost:8000/api/student/login?roll_number=${rollNumber}`,
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        }
      )

      if (!response.ok) {
        throw new Error('Invalid roll number')
      }

      const data = await response.json()
      setStudentData(data.student)
      setIsLoggedIn(true)
      await fetchDashboardData(data.student.id)
    } catch (err) {
      setError('Invalid roll number. Please try again.')
      setLoading(false)
    }
  }

  // Fetch dashboard data
  const fetchDashboardData = async (studentId) => {
    try {
      const response = await fetch(
        `http://localhost:8000/api/student/dashboard/${studentId}`
      )

      if (!response.ok) {
        throw new Error('Failed to fetch dashboard')
      }

      const data = await response.json()
      setDashboardData(data)
      setLoading(false)
    } catch (err) {
      setError('Failed to load dashboard data')
      setLoading(false)
    }
  }

  // Ask AI Assistant
  const handleAskQuestion = async () => {
    if (!currentQuestion.trim() || !studentData) return

    const userMessage = { type: 'user', text: currentQuestion }
    setChatMessages((prev) => [...prev, userMessage])
    setChatLoading(true)

    try {
      const response = await fetch('http://localhost:8000/api/student/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          question: currentQuestion,
          student_id: studentData.id
        })
      })

      if (!response.ok) {
        throw new Error('AI response failed')
      }

      const data = await response.json()
      const aiMessage = { type: 'ai', text: data.response }

      setChatMessages((prev) => [...prev, aiMessage])
      setCurrentQuestion('')
    } catch (err) {
      const errorMessage = {
        type: 'ai',
        text: 'Sorry, I had trouble understanding that. Please try again.'
      }
      setChatMessages((prev) => [...prev, errorMessage])
    }

    setChatLoading(false)
  }

  const getRiskColor = (level) => {
    switch (level) {
      case 'Low':
        return '#4CAF50'
      case 'Moderate':
        return '#FF9800'
      case 'High':
        return '#f44336'
      default:
        return '#999'
    }
  }

  // Logout
  const handleLogout = () => {
    setIsLoggedIn(false)
    setStudentData(null)
    setDashboardData(null)
    setRollNumber('')
    setChatMessages([])
    setError('')
  }

  // Login Screen
  if (!isLoggedIn) {
    return (
      <div className="student-login">
        <div className="login-container">
          <div className="login-header">
            <h1>🎓 Student Portal</h1>
            <p>Login to view your academic performance</p>
          </div>

          <form onSubmit={handleLogin} className="login-form">
            <div className="form-group">
              <label>Roll Number</label>
              <input
                type="text"
                value={rollNumber}
                onChange={(e) => setRollNumber(e.target.value)}
                placeholder="e.g., 2021BTCS001"
                required
              />
            </div>

            {error && <div className="error-message">{error}</div>}

            <button type="submit" disabled={loading} className="login-button">
              {loading ? 'Logging in...' : 'Login'}
            </button>

            <div className="demo-info">
              <p>Demo Roll Numbers:</p>
              <p>• 2021BTCS001 to 2021BTCS040 (Low Risk)</p>
              <p>• 2021BTCS041 to 2021BTCS050 (At Risk)</p>
            </div>
          </form>
        </div>
      </div>
    )
  }

  // Loading screen
  if (!dashboardData) {
    return <div className="loading">Loading your dashboard...</div>
  }

  const risk = dashboardData.risk_analysis

  return (
    <div className="student-dashboard">
      {/* Header */}
      <header className="dashboard-header">
        <div>
          <h1>Welcome, {studentData.name}! 👋</h1>
          <p className="roll-number">
            {studentData.roll_number} • {studentData.branch}
          </p>
        </div>
        <button onClick={handleLogout} className="logout-button">
          Logout
        </button>
      </header>

      {/* Risk Overview */}
      <div className="risk-overview">
        <div className="risk-card-main">
          <h2>Your Academic Health</h2>
          <div
            className="risk-score-display"
            style={{ borderColor: getRiskColor(risk.risk_level) }}
          >
            <div
              className="risk-level"
              style={{ color: getRiskColor(risk.risk_level) }}
            >
              {risk.risk_level} Risk
            </div>
            <div className="risk-score">{risk.risk_score}</div>
            <div className="risk-label">Risk Score</div>
          </div>
        </div>

        <div className="metrics-summary">
          <div className="metric-box">
            <div className="metric-value">{risk.cgpa}</div>
            <div className="metric-label">CGPA</div>
          </div>
          <div className="metric-box">
            <div className="metric-value">{risk.attendance}%</div>
            <div className="metric-label">Attendance</div>
          </div>
          <div className="metric-box">
            <div className="metric-value">{risk.failed_subjects}</div>
            <div className="metric-label">Backlogs</div>
          </div>
          <div className="metric-box">
            <div className="metric-value">{risk.gpa_trend}</div>
            <div className="metric-label">Trend</div>
          </div>
        </div>
      </div>

      {/* Two Column Layout */}
      <div className="dashboard-content">
        {/* Left Column */}
        <div className="left-column">
          {risk.risk_factors && Object.keys(risk.risk_factors).length > 0 && (
            <div className="section risk-section">
              <h3>⚠️ Areas Needing Attention</h3>
              {Object.entries(risk.risk_factors).map(([key, value]) => (
                <div key={key} className="risk-item">
                  <span className="risk-dot">●</span>
                  <span>{value}</span>
                </div>
              ))}
            </div>
          )}

          {risk.recommendations && risk.recommendations.length > 0 && (
            <div className="section recommendations-section">
              <h3>💡 Personalized Recommendations</h3>
              {risk.recommendations.map((rec, index) => (
                <div key={index} className="recommendation-item">
                  <span className="rec-number">{index + 1}</span>
                  <span>{rec}</span>
                </div>
              ))}
            </div>
          )}

          <div className="section">
            <h3>📊 Semester Performance</h3>
            <div className="semester-list">
              {dashboardData.semester_performance.map((sem) => (
                <div key={sem.semester} className="semester-card">
                  <div className="semester-header">
                    <span className="semester-name">
                      Semester {sem.semester}
                    </span>
                    <span className="semester-gpa">GPA: {sem.gpa}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* Right Column - AI Chat */}
        <div className="right-column">
          <div className="chat-section">
            <h3>🤖 AI Study Assistant</h3>
            <p className="chat-subtitle">
              Ask me anything about your performance!
            </p>

            <div className="chat-messages">
              {chatMessages.length === 0 && (
                <div className="chat-welcome">
                  <p>Hi {studentData.name}! 👋</p>
                  <p>I can help you with:</p>
                  <ul>
                    <li>Understanding your risk factors</li>
                    <li>Improving your CGPA</li>
                    <li>Attendance tracking</li>
                    <li>Study strategies</li>
                  </ul>
                  <p>
                    Try asking: "Why is my risk high?" or "How can I improve?"
                  </p>
                </div>
              )}

              {chatMessages.map((msg, index) => (
                <div key={index} className={`chat-message ${msg.type}`}>
                  <div className="message-content">{msg.text}</div>
                </div>
              ))}

              {chatLoading && (
                <div className="chat-message ai">
                  <div className="message-content">Thinking...</div>
                </div>
              )}
            </div>

            <div className="chat-input">
              <input
                type="text"
                value={currentQuestion}
                onChange={(e) => setCurrentQuestion(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') handleAskQuestion()
                }}
                placeholder="Ask me anything..."
              />
              <button onClick={handleAskQuestion} disabled={chatLoading}>
                Send
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default StudentDashboard
