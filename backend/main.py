from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from database.init_db import SessionLocal, get_db
from models.student import Student, Grade, Attendance
from services.risk_calculator import RiskCalculator
from typing import List, Dict
from pydantic import BaseModel
import uvicorn
from openai import OpenAI
import os
from dotenv import load_dotenv
from services.ml_predictor import MLPredictor
from services.ml_predictor import MLPredictor

# Load environment variables
load_dotenv()

# Verify OpenAI key is loaded
if not os.getenv('OPENAI_API_KEY'):
    print("WARNING: OPENAI_API_KEY not found in environment!")
else:
    print("✅ OpenAI API key loaded successfully")

# Create FastAPI app
app = FastAPI(
    title="Student Risk Assessment API",
    description="AI-powered student academic performance risk assessment",
    version="1.0.0"
)

# CORS middleware (allows frontend to connect)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
def root():
    """API health check"""
    return {
        "message": "Student Risk Assessment API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "students": "/api/students",
            "student_detail": "/api/student/{id}",
            "risk_analysis": "/api/risk/{id}",
            "at_risk_students": "/api/students/at-risk",
            "docs": "/docs"
        }
    }

# Get all students
@app.get("/api/students")
def get_students(db: Session = Depends(get_db)):
    """Get list of all students"""
    students = db.query(Student).all()
    return [
        {
            "id": s.id,
            "roll_number": s.roll_number,
            "name": s.name,
            "branch": s.branch,
            "batch": s.batch,
            "semester": s.current_semester,
            "email": s.email
        }
        for s in students
    ]

# Get single student details
@app.get("/api/student/{student_id}")
def get_student(student_id: int, db: Session = Depends(get_db)):
    """Get detailed information about a student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get grades
    grades = db.query(Grade).filter(Grade.student_id == student_id).all()
    grades_data = [
        {
            "semester": g.semester,
            "subject_code": g.subject_code,
            "subject_name": g.subject_name,
            "grade_point": g.grade_point,
            "credits": g.credits
        }
        for g in grades
    ]
    
    # Get attendance
    attendance = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    attendance_data = [
        {
            "semester": a.semester,
            "subject_code": a.subject_code,
            "percentage": a.percentage,
            "attended": a.attended_classes,
            "total": a.total_classes
        }
        for a in attendance
    ]
    
    return {
        "id": student.id,
        "roll_number": student.roll_number,
        "name": student.name,
        "email": student.email,
        "branch": student.branch,
        "batch": student.batch,
        "current_semester": student.current_semester,
        "grades": grades_data,
        "attendance": attendance_data
    }

# Calculate risk for a student
@app.get("/api/risk/{student_id}")
def calculate_risk(student_id: int, db: Session = Depends(get_db)):
    """Calculate risk score and get recommendations for a student"""
    calculator = RiskCalculator(db)
    risk_data = calculator.calculate_risk_score(student_id)
    
    if not risk_data:
        raise HTTPException(status_code=404, detail="Student not found")
    
    return risk_data

# Get all at-risk students
@app.get("/api/students/at-risk")
def get_at_risk_students(db: Session = Depends(get_db)):
    """Get all students with Moderate or High risk"""
    calculator = RiskCalculator(db)
    students = db.query(Student).all()
    
    at_risk = []
    for student in students:
        risk = calculator.calculate_risk_score(student.id)
        if risk['risk_level'] in ['Moderate', 'High']:
            at_risk.append(risk)
    
    # Sort by risk score (highest first)
    at_risk.sort(key=lambda x: x['risk_score'], reverse=True)
    
    return at_risk
# ========== STUDENT ENDPOINTS ==========

# Student login - verify roll number exists
@app.post("/api/student/login")
def student_login(roll_number: str, db: Session = Depends(get_db)):
    """Student login - verify roll number and return student data"""
    student = db.query(Student).filter(Student.roll_number == roll_number).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Invalid roll number")
    
    return {
        "success": True,
        "student": {
            "id": student.id,
            "roll_number": student.roll_number,
            "name": student.name,
            "email": student.email,
            "branch": student.branch,
            "batch": student.batch,
            "current_semester": student.current_semester
        }
    }

# Get student's own dashboard data
@app.get("/api/student/dashboard/{student_id}")
def get_student_dashboard(student_id: int, db: Session = Depends(get_db)):
    """Get complete dashboard data for a student"""
    student = db.query(Student).filter(Student.id == student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get risk data
    calculator = RiskCalculator(db)
    risk_data = calculator.calculate_risk_score(student_id)
    
    # Get all grades grouped by semester
    grades = db.query(Grade).filter(Grade.student_id == student_id).order_by(Grade.semester).all()
    
    # Calculate semester-wise GPA
    semester_gpas = {}
    for grade in grades:
        if grade.semester not in semester_gpas:
            semester_gpas[grade.semester] = []
        semester_gpas[grade.semester].append({
            'subject': grade.subject_name,
            'code': grade.subject_code,
            'grade_point': grade.grade_point,
            'credits': grade.credits
        })
    
    # Calculate GPA for each semester
    semester_data = []
    for sem, sem_grades in sorted(semester_gpas.items()):
        total_points = sum(g['grade_point'] * g['credits'] for g in sem_grades)
        total_credits = sum(g['credits'] for g in sem_grades)
        gpa = round(total_points / total_credits, 2) if total_credits > 0 else 0
        semester_data.append({
            'semester': sem,
            'gpa': gpa,
            'subjects': sem_grades
        })
    
    # Get attendance data
    attendance = db.query(Attendance).filter(Attendance.student_id == student_id).all()
    attendance_data = {}
    for att in attendance:
        if att.subject_code not in attendance_data:
            attendance_data[att.subject_code] = {
                'subject_code': att.subject_code,
                'percentage': att.percentage,
                'attended': att.attended_classes,
                'total': att.total_classes
            }
    
    return {
        "student": {
            "id": student.id,
            "roll_number": student.roll_number,
            "name": student.name,
            "email": student.email,
            "branch": student.branch,
            "batch": student.batch,
            "current_semester": student.current_semester
        },
        "risk_analysis": risk_data,
        "semester_performance": semester_data,
        "attendance": list(attendance_data.values())
    }

# Ask AI Assistant (placeholder for now - we'll add AI later)
# Request model for AI questions
from pydantic import BaseModel

class AskRequest(BaseModel):
    question: str
    student_id: int
@app.post("/api/student/ask")
def ask_assistant(request: AskRequest, db: Session = Depends(get_db)):
    """AI Assistant endpoint with ML predictions"""
    student = db.query(Student).filter(Student.id == request.student_id).first()
    
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    
    # Get risk data for context
    calculator = RiskCalculator(db)
    risk_data = calculator.calculate_risk_score(request.student_id)
    
    # Initialize ML predictor
    ml_predictor = MLPredictor(db)
    
    question_lower = request.question.lower()
    
    # ML-POWERED PREDICTIONS
    if "graduate" in question_lower or "graduation" in question_lower or "final cgpa" in question_lower:
        # Use ML to predict graduation CGPA
        prediction = ml_predictor.predict_graduation_cgpa(request.student_id)
        response = f"""📊 Graduation Prediction:

Current CGPA: {prediction['current_cgpa']}
Predicted Final CGPA: {prediction['predicted_final_cgpa']}
Outlook: {prediction['outlook']}

{prediction['message']}

Your grades are {prediction['trend']}. With {prediction['semesters_remaining']} semesters remaining, {"you're on track!" if prediction['predicted_final_cgpa'] >= 6.5 else "you need to improve significantly."}"""
    
    elif "what if" in question_lower or "if i get" in question_lower:
        # Extract GPA from question (simplified - looks for numbers)
        import re
        numbers = re.findall(r'\d+\.?\d*', request.question)
        target_gpa = float(numbers[0]) if numbers else 8.0
        target_gpa = min(10.0, max(0.0, target_gpa))  # Clamp to 0-10
        
        # Use ML for what-if analysis
        analysis = ml_predictor.what_if_analysis(request.student_id, target_gpa)
        response = f"""🔮 What-If Analysis:

If you achieve {analysis['target_next_semester_gpa']} GPA next semester:

- Your CGPA will rise from {analysis['current_cgpa']} to {analysis['predicted_new_cgpa']} (+{analysis['cgpa_change']})
- Your risk will change from {analysis['current_risk_level']} ({analysis['current_risk_score']}) to {analysis['predicted_risk_level']} ({analysis['predicted_risk_score']})
- Risk improvement: {abs(analysis['risk_change']):.2f} {"⬇️ (better!)" if analysis['risk_change'] < 0 else "⬆️ (worse)"}

Feasibility: {analysis['feasibility']}

{
"This is an ambitious target! You'll need strong focus and dedication." if analysis['feasibility'] == 'Very Challenging' 
else "This is achievable with consistent effort!" if analysis['feasibility'] == 'Achievable'
else "This is realistic - you can do it!"
}"""
    
    elif "fail" in question_lower or "pass" in question_lower:
        # Use ML to predict failure risk
        prediction = ml_predictor.predict_subject_failure(request.student_id)
        response = f"""⚠️ Performance Prediction:

Current Grade: {prediction['current_grade']}
Current Attendance: {prediction['current_attendance']}%

Failure Risk: {prediction['risk_level']}
- Pass Probability: {prediction['pass_probability']}%
- Fail Probability: {prediction['failure_probability']}%

{prediction['message']}"""
    
    elif "risk" in question_lower or "why" in question_lower:
        factors = risk_data.get('risk_factors', {})
        if factors:
            response = f"Your risk is {risk_data['risk_level']} because:\n\n"
            for i, (key, value) in enumerate(factors.items(), 1):
                response += f"{i}. {value}\n"
            response += f"\n💡 Want to see how you can improve? Ask 'What if I get 8.0 next semester?'"
        else:
            response = "Your risk is Low! Keep up the good work! 🎉"
    
    elif "attendance" in question_lower:
        response = f"📊 Your average attendance is {risk_data['attendance']}%. "
        if risk_data['attendance'] < 75:
            response += f"\n\n⚠️ This is below the 75% requirement!\n\n"
            needed = 75 - risk_data['attendance']
            response += f"You need to improve by {needed:.1f}% to meet the minimum requirement. Try to attend all upcoming classes!"
        else:
            response += "\n\n✅ Great job maintaining attendance above the 75% requirement!"
    
    elif "cgpa" in question_lower or "gpa" in question_lower:
        response = f"📊 Your current CGPA is {risk_data['cgpa']}. "
        if risk_data['gpa_trend'] == 'improving':
            response += "\n\n📈 Great news - your grades are improving! Keep it up!"
        elif risk_data['gpa_trend'] == 'declining':
            response += "\n\n📉 Your grades are declining. Let's work on reversing this trend."
        else:
            response += "\n\n➡️ Your performance is stable."
        
        response += f"\n\n💡 Curious about your future? Ask 'What will my graduation CGPA be?'"
    
    elif "improve" in question_lower or "help" in question_lower:
        recommendations = risk_data.get('recommendations', [])
        if recommendations:
            response = "Here's your personalized action plan:\n\n"
            for i, rec in enumerate(recommendations, 1):
                response += f"{i}. {rec}\n"
            response += f"\n💡 Want to see the impact? Try asking 'What if I get 9.0 next semester?'"
        else:
            response = "You're doing well! Keep maintaining your current study habits. 🌟"
    
    else:
        response = f"""Hi {student.name}! 👋 I'm your AI study assistant.

I can help you with:

🔮 Predictions:
- "What will my graduation CGPA be?"
- "Will I fail any subjects?"
- "What if I get 9.0 next semester?"

📊 Your Performance:
- "Why is my risk high?"
- "What's my CGPA?"
- "How's my attendance?"

💡 Guidance:
- "How can I improve?"
- "What should I focus on?"

Try asking any of these questions!"""
    
    return {
        "question": request.question,
        "response": response,
        "student_name": student.name
    }

# ========== ML PREDICTION ENDPOINTS ==========

@app.get("/api/ml/predict-failure/{student_id}")
def predict_failure(student_id: int, subject_code: str = None, db: Session = Depends(get_db)):
    """Predict if student will fail (overall or specific subject)"""
    predictor = MLPredictor(db)
    prediction = predictor.predict_subject_failure(student_id, subject_code)
    return prediction

@app.get("/api/ml/predict-graduation/{student_id}")
def predict_graduation(student_id: int, db: Session = Depends(get_db)):
    """Predict final graduation CGPA"""
    predictor = MLPredictor(db)
    prediction = predictor.predict_graduation_cgpa(student_id)
    return prediction

@app.get("/api/ml/what-if/{student_id}")
def what_if_scenario(student_id: int, next_gpa: float, db: Session = Depends(get_db)):
    """Calculate impact of achieving a certain GPA next semester"""
    if next_gpa < 0 or next_gpa > 10:
        raise HTTPException(status_code=400, detail="GPA must be between 0 and 10")
    
    predictor = MLPredictor(db)
    analysis = predictor.what_if_analysis(student_id, next_gpa)
    return analysis


# Run the server
if __name__ == "__main__":
    print("🚀 Starting Student Risk Assessment API...")
    print("📍 API will be available at: http://localhost:8000")
    print("📚 API Documentation at: http://localhost:8000/docs")
    print("🔄 Press CTRL+C to stop")
    uvicorn.run(app, host="0.0.0.0", port=8000)