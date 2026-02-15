import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from models.student import Student, Grade, Attendance, RiskScore
from datetime import date

class RiskCalculator:
    """Calculate student academic risk scores"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def calculate_cgpa(self, student_id: int) -> float:
        """Calculate cumulative GPA"""
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        if not grades:
            return 0.0
        
        total_points = sum(g.grade_point * g.credits for g in grades)
        total_credits = sum(g.credits for g in grades)
        return round(total_points / total_credits, 2) if total_credits > 0 else 0.0
    
    def calculate_attendance_avg(self, student_id: int) -> float:
        """Calculate average attendance percentage"""
        attendance_records = self.db.query(Attendance).filter(
            Attendance.student_id == student_id
        ).all()
        
        if not attendance_records:
            return 0.0
        
        avg = sum(a.percentage for a in attendance_records) / len(attendance_records)
        return round(avg, 2)
    
    def calculate_gpa_trend(self, student_id: int) -> str:
        """Determine if GPA is improving, declining, or stable"""
        grades = self.db.query(Grade).filter(
            Grade.student_id == student_id
        ).order_by(Grade.semester).all()
        
        # Group by semester
        sem_gpas = {}
        for grade in grades:
            if grade.semester not in sem_gpas:
                sem_gpas[grade.semester] = []
            sem_gpas[grade.semester].append(grade.grade_point * grade.credits)
        
        # Calculate semester averages
        semester_averages = []
        for sem in sorted(sem_gpas.keys()):
            points = sem_gpas[sem]
            avg = sum(points) / len(points)
            semester_averages.append(avg)
        
        if len(semester_averages) < 2:
            return 'stable'
        
        # Check trend in last 3 semesters
        recent = semester_averages[-3:]
        if recent[-1] > recent[0] + 0.5:
            return 'improving'
        elif recent[-1] < recent[0] - 0.5:
            return 'declining'
        return 'stable'
    
    def calculate_risk_score(self, student_id: int) -> dict:
        """Calculate comprehensive risk score for a student"""
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return None
        
        # Calculate metrics
        cgpa = self.calculate_cgpa(student_id)
        attendance_avg = self.calculate_attendance_avg(student_id)
        gpa_trend = self.calculate_gpa_trend(student_id)
        
        # Initialize risk factors
        risk_factors = {}
        risk_score = 0.0
        
        # Factor 1: CGPA (60% weight)
        if cgpa < 5.0:
            risk_factors['low_cgpa'] = f'Critical - CGPA {cgpa} is below 5.0'
            risk_score += 0.6
        elif cgpa < 6.5:
            risk_factors['moderate_cgpa'] = f'CGPA {cgpa} is below 6.5'
            risk_score += 0.35
        elif cgpa < 7.5:
            risk_score += 0.15
        
        # Factor 2: Attendance (20% weight)
        if attendance_avg < 50:
            risk_factors['critical_attendance'] = f'Very low attendance ({attendance_avg:.1f}%)'
            risk_score += 0.2
        elif attendance_avg < 75:
            risk_factors['low_attendance'] = f'Below required 75% ({attendance_avg:.1f}%)'
            risk_score += 0.12
        
        # Factor 3: GPA Trend (10% weight)
        if gpa_trend == 'declining':
            risk_factors['declining_performance'] = 'Performance declining over semesters'
            risk_score += 0.1
        
        # Factor 4: Failed subjects (10% weight)
        failed_subjects = self.db.query(Grade).filter(
            Grade.student_id == student_id,
            Grade.grade_point < 4.0
        ).count()
        
        if failed_subjects > 3:
            risk_factors['multiple_backlogs'] = f'{failed_subjects} failed subjects'
            risk_score += 0.1
        elif failed_subjects > 0:
            risk_score += 0.05
        
        # Normalize to 0-1
        risk_score = min(1.0, risk_score)
        
        # Classify risk level
        if risk_score < 0.35:
            risk_level = 'Low'
        elif risk_score < 0.65:
            risk_level = 'Moderate'
        else:
            risk_level = 'High'
        
        # Calculate confidence
        total_grades = self.db.query(Grade).filter(Grade.student_id == student_id).count()
        confidence = min(1.0, total_grades / 30)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(risk_factors, risk_level)
        
        # Save to database
        risk_record = RiskScore(
            student_id=student_id,
            semester=student.current_semester,
            risk_score=risk_score,
            risk_level=risk_level,
            confidence=confidence,
            factors=risk_factors,
            generated_at=date.today()
        )
        self.db.add(risk_record)
        self.db.commit()
        
        return {
            'student_id': student_id,
            'student_name': student.name,
            'roll_number': student.roll_number,
            'branch': student.branch,
            'cgpa': cgpa,
            'attendance': attendance_avg,
            'gpa_trend': gpa_trend,
            'failed_subjects': failed_subjects,
            'risk_score': round(risk_score, 2),
            'risk_level': risk_level,
            'confidence': round(confidence, 2),
            'risk_factors': risk_factors,
            'recommendations': recommendations
        }
    
    def _generate_recommendations(self, factors: dict, risk_level: str) -> list:
        """Generate actionable recommendations"""
        recommendations = []
        
        if 'low_cgpa' in factors or 'moderate_cgpa' in factors:
            recommendations.append('Priority: Focus on improving grades in core subjects')
            recommendations.append('Consider peer tutoring program')
        
        if 'critical_attendance' in factors or 'low_attendance' in factors:
            recommendations.append('Priority: Improve attendance to meet 75% threshold')
            recommendations.append('Consult academic advisor about attendance')
        
        if 'declining_performance' in factors:
            recommendations.append('Schedule meeting with faculty mentor')
        
        if 'multiple_backlogs' in factors:
            recommendations.append('Priority: Clear backlogs before next semester')
            recommendations.append('Consider reduced course load')
        
        if risk_level == 'Low':
            recommendations.append('Continue current study pattern')
            recommendations.append('Consider advanced electives')
        
        return recommendations