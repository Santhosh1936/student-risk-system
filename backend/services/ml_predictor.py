import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.student import Student, Grade, Attendance
import numpy as np
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.model_selection import train_test_split
import joblib
import warnings
warnings.filterwarnings('ignore')

class MLPredictor:
    """ML-powered predictions for student outcomes"""
    
    def __init__(self, db: Session):
        self.db = db
        self.failure_model = None
        self.cgpa_model = None
    
    def train_models(self):
        """Train ML models on existing student data"""
        print("🤖 Training ML models...")
        
        # Prepare training data
        students = self.db.query(Student).all()
        training_data = []
        
        for student in students:
            # Get student metrics
            grades = self.db.query(Grade).filter(Grade.student_id == student.id).all()
            attendance = self.db.query(Attendance).filter(Attendance.student_id == student.id).all()
            
            if not grades or not attendance:
                continue
            
            # Calculate features
            all_grades = [g.grade_point for g in grades]
            avg_grade = np.mean(all_grades)
            grade_std = np.std(all_grades)
            avg_attendance = np.mean([a.percentage for a in attendance])
            
            # Calculate trend (last 2 semesters vs first 2)
            sems = {}
            for g in grades:
                if g.semester not in sems:
                    sems[g.semester] = []
                sems[g.semester].append(g.grade_point)
            
            if len(sems) >= 4:
                early_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[:2]])
                recent_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[-2:]])
                trend = recent_avg - early_avg
            else:
                trend = 0
            
            # Count failures
            failures = len([g for g in grades if g.grade_point < 4.0])
            
            training_data.append({
                'avg_grade': avg_grade,
                'grade_std': grade_std,
                'avg_attendance': avg_attendance,
                'trend': trend,
                'failures': failures,
                'final_cgpa': avg_grade  # For CGPA prediction
            })
        
        if len(training_data) < 10:
            print("⚠️  Not enough data to train models")
            return False
        
        # Train Failure Prediction Model
        X_failure = [[d['avg_grade'], d['grade_std'], d['avg_attendance'], d['trend']] 
                     for d in training_data]
        y_failure = [1 if d['failures'] > 0 else 0 for d in training_data]
        
        self.failure_model = RandomForestClassifier(n_estimators=50, random_state=42)
        self.failure_model.fit(X_failure, y_failure)
        
        # Train CGPA Prediction Model
        X_cgpa = [[d['avg_grade'], d['avg_attendance'], d['trend'], d['failures']] 
                  for d in training_data]
        y_cgpa = [d['final_cgpa'] for d in training_data]
        
        self.cgpa_model = RandomForestRegressor(n_estimators=50, random_state=42)
        self.cgpa_model.fit(X_cgpa, y_cgpa)
        
        print(f"✅ Models trained on {len(training_data)} students!")
        return True
    
    def predict_subject_failure(self, student_id: int, subject_code: str = None) -> dict:
        """Predict if student will fail a subject"""
        
        if not self.failure_model:
            self.train_models()
        
        # Get student data
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        attendance = self.db.query(Attendance).filter(Attendance.student_id == student_id).all()
        
        if subject_code:
            # Specific subject prediction
            subject_grades = [g for g in grades if g.subject_code == subject_code]
            subject_attendance = [a for a in attendance if a.subject_code == subject_code]
            
            if not subject_grades:
                return {'error': 'No data for this subject'}
            
            avg_grade = np.mean([g.grade_point for g in subject_grades])
            grade_std = np.std([g.grade_point for g in subject_grades]) if len(subject_grades) > 1 else 0
            avg_att = np.mean([a.percentage for a in subject_attendance]) if subject_attendance else 75
            trend = 0
            
        else:
            # Overall prediction
            avg_grade = np.mean([g.grade_point for g in grades])
            grade_std = np.std([g.grade_point for g in grades])
            avg_att = np.mean([a.percentage for a in attendance])
            
            # Calculate trend
            sems = {}
            for g in grades:
                if g.semester not in sems:
                    sems[g.semester] = []
                sems[g.semester].append(g.grade_point)
            
            if len(sems) >= 4:
                early_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[:2]])
                recent_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[-2:]])
                trend = recent_avg - early_avg
            else:
                trend = 0
        
        # Predict
        features = [[avg_grade, grade_std, avg_att, trend]]
        probability = self.failure_model.predict_proba(features)[0]

        # Handle edge case where model only learned one class
        if len(probability) == 1:
            # Model only has one class - check which one
            classes = self.failure_model.classes_
            if classes[0] == 1:  # Only failures in training data
                fail_prob = 100.0
                pass_prob = 0.0
            else:  # Only passes in training data
                fail_prob = 0.0
                pass_prob = 100.0
        else:
            fail_prob = probability[1] * 100  # Probability of failure
            pass_prob = probability[0] * 100  # Probability of passing
        
        # Determine risk level
        if fail_prob > 70:
            risk = "Very High"
            message = "Strong likelihood of failure. Immediate intervention needed!"
        elif fail_prob > 50:
            risk = "High"
            message = "At significant risk of failing. Take action now."
        elif fail_prob > 30:
            risk = "Moderate"
            message = "Some risk of failure. Stay focused and improve."
        else:
            risk = "Low"
            message = "On track to pass. Keep up the good work!"
        
        return {
            'subject': subject_code or 'Overall',
            'failure_probability': round(fail_prob, 1),
            'pass_probability': round(pass_prob, 1),
            'risk_level': risk,
            'message': message,
            'current_grade': round(avg_grade, 2),
            'current_attendance': round(avg_att, 1)
        }
    
    def predict_graduation_cgpa(self, student_id: int, semesters_remaining: int = 2) -> dict:
        """Predict final graduation CGPA"""
        
        if not self.cgpa_model:
            self.train_models()
        
        # Get current student data
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        attendance = self.db.query(Attendance).filter(Attendance.student_id == student_id).all()
        
        current_cgpa = np.mean([g.grade_point for g in grades])
        avg_attendance = np.mean([a.percentage for a in attendance])
        failures = len([g for g in grades if g.grade_point < 4.0])
        
        # Calculate trend
        sems = {}
        for g in grades:
            if g.semester not in sems:
                sems[g.semester] = []
            sems[g.semester].append(g.grade_point)
        
        if len(sems) >= 4:
            early_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[:2]])
            recent_avg = np.mean([np.mean(sems[s]) for s in sorted(sems.keys())[-2:]])
            trend = recent_avg - early_avg
        else:
            trend = 0
        
        # Predict
        features = [[current_cgpa, avg_attendance, trend, failures]]
        predicted_cgpa = self.cgpa_model.predict(features)[0]
        
        # Determine outlook
        if predicted_cgpa >= 8.5:
            outlook = "Excellent"
            message = "On track for honors/distinction!"
        elif predicted_cgpa >= 7.5:
            outlook = "Very Good"
            message = "Strong performance, good placement prospects"
        elif predicted_cgpa >= 6.5:
            outlook = "Good"
            message = "Solid performance, continue improving"
        elif predicted_cgpa >= 5.5:
            outlook = "Fair"
            message = "Below average, significant improvement needed"
        else:
            outlook = "At Risk"
            message = "At risk of not meeting graduation requirements"
        
        return {
            'current_cgpa': round(current_cgpa, 2),
            'predicted_final_cgpa': round(predicted_cgpa, 2),
            'semesters_remaining': semesters_remaining,
            'outlook': outlook,
            'message': message,
            'trend': 'improving' if trend > 0 else 'declining' if trend < 0 else 'stable'
        }
    
    def what_if_analysis(self, student_id: int, next_semester_gpa: float) -> dict:
        """Calculate impact of achieving a certain GPA next semester"""
        
        # Get current data
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        
        current_cgpa = np.mean([g.grade_point for g in grades])
        total_credits = len(grades) * 4  # Assuming 4 credits per subject
        
        # Calculate new CGPA if student gets next_semester_gpa
        # Assuming 6 subjects next semester, 4 credits each = 24 credits
        next_sem_credits = 24
        total_points_current = current_cgpa * total_credits
        total_points_new = total_points_current + (next_semester_gpa * next_sem_credits)
        new_cgpa = total_points_new / (total_credits + next_sem_credits)
        
        # Calculate risk change
        from services.risk_calculator import RiskCalculator
        calculator = RiskCalculator(self.db)
        current_risk = calculator.calculate_risk_score(student_id)
        
        # Estimate new risk (simplified)
        cgpa_change = new_cgpa - current_cgpa
        estimated_risk_change = -cgpa_change * 0.2  # Rough estimate
        new_risk_score = max(0, min(1, current_risk['risk_score'] + estimated_risk_change))
        
        if new_risk_score < 0.35:
            new_risk_level = 'Low'
        elif new_risk_score < 0.65:
            new_risk_level = 'Moderate'
        else:
            new_risk_level = 'High'
        
        return {
            'current_cgpa': round(current_cgpa, 2),
            'target_next_semester_gpa': next_semester_gpa,
            'predicted_new_cgpa': round(new_cgpa, 2),
            'cgpa_change': round(new_cgpa - current_cgpa, 2),
            'current_risk_level': current_risk['risk_level'],
            'current_risk_score': current_risk['risk_score'],
            'predicted_risk_level': new_risk_level,
            'predicted_risk_score': round(new_risk_score, 2),
            'risk_change': round(new_risk_score - current_risk['risk_score'], 2),
            'feasibility': 'Very Challenging' if next_semester_gpa > current_cgpa + 2 
                          else 'Challenging' if next_semester_gpa > current_cgpa + 1
                          else 'Achievable' if next_semester_gpa > current_cgpa 
                          else 'Realistic'
        }