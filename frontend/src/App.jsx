import { useState } from 'react'
import AdminDashboard from './AdminDashboard'
import StudentDashboard from './StudentDashboard'
import './App.css'

function App() {
  const [view, setView] = useState('select') // 'select', 'admin', 'student'

  if (view === 'admin') {
    return (
      <div>
        <button 
          onClick={() => setView('select')} 
          style={{
            position: 'fixed',
            top: 20,
            right: 20,
            padding: '10px 20px',
            background: 'white',
            border: '2px solid #667eea',
            borderRadius: '8px',
            cursor: 'pointer',
            zIndex: 1000,
            fontWeight: 'bold'
          }}
        >
          ← Back to Menu
        </button>
        <AdminDashboard />
      </div>
    )
  }

  if (view === 'student') {
    return <StudentDashboard />
  }

  // Selection Screen
  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '20px'
    }}>
      <div style={{
        background: 'white',
        borderRadius: '20px',
        padding: '60px 40px',
        maxWidth: '600px',
        width: '100%',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        textAlign: 'center'
      }}>
        <h1 style={{ fontSize: '2.5em', marginBottom: '20px', color: '#333' }}>
          🎓 Student Risk Assessment System
        </h1>
        <p style={{ fontSize: '1.2em', color: '#666', marginBottom: '40px' }}>
          Choose your portal
        </p>

        <div style={{
          display: 'grid',
          gridTemplateColumns: '1fr 1fr',
          gap: '20px'
        }}>
          <button
            onClick={() => setView('admin')}
            style={{
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '15px',
              fontSize: '1.5em',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              boxShadow: '0 4px 15px rgba(102, 126, 234, 0.4)'
            }}
            onMouseOver={(e) => e.target.style.transform = 'translateY(-5px)'}
            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
          >
            👨‍💼<br/>Admin/Faculty
          </button>

          <button
            onClick={() => setView('student')}
            style={{
              padding: '40px 20px',
              background: 'linear-gradient(135deg, #4CAF50 0%, #388E3C 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '15px',
              fontSize: '1.5em',
              fontWeight: 'bold',
              cursor: 'pointer',
              transition: 'transform 0.2s',
              boxShadow: '0 4px 15px rgba(76, 175, 80, 0.4)'
            }}
            onMouseOver={(e) => e.target.style.transform = 'translateY(-5px)'}
            onMouseOut={(e) => e.target.style.transform = 'translateY(0)'}
          >
            🎓<br/>Student
          </button>
        </div>
      </div>
    </div>
  )
}

export default App