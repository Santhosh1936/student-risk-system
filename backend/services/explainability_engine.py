"""
Explainability Engine - Generates transparent, evidence-based explanations for risk assessments
Converts opaque risk scores into clear, actionable insights
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.student import Student, Grade, Attendance, MentorNote, BehavioralLog
from datetime import datetime, timedelta
import statistics

class ExplainabilityEngine:
    """
    Generates human-readable explanations for student risk assessments
    Follows principles of Explainable AI (XAI) and transparency
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def explain_risk_score(self, student_id: int, risk_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate comprehensive explanation for a student's risk score
        
        Args:
            student_id: Student's unique identifier
            risk_data: Risk assessment data from RiskCalculator
            
        Returns:
            Detailed explanation with evidence, factors, and recommendations
        """
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        risk_score = risk_data.get('risk_score', 0.0)
        factors = risk_data.get('factors', {})
        
        # Categorize risk level
        risk_level, risk_color = self._categorize_risk(risk_score)
        
        # Analyze each factor
        factor_explanations = self._explain_factors(student_id, factors)
        
        # Generate comparative insights
        comparative_analysis = self._generate_comparative_analysis(student_id, factors)
        
        # Identify key risk drivers
        top_risk_factors = self._identify_top_risks(factor_explanations)
        
        # Generate actionable recommendations
        recommendations = self._generate_recommendations(student_id, top_risk_factors, risk_score)
        
        # Build narrative explanation
        narrative = self._build_narrative(student, risk_score, risk_level, top_risk_factors)
        
        # Evidence trail
        evidence = self._gather_evidence(student_id, top_risk_factors)
        
        explanation = {
            "student_id": student_id,
            "student_name": student.name,
            "risk_score": round(risk_score, 3),
            "risk_level": risk_level,
            "risk_color": risk_color,
            "timestamp": datetime.now().isoformat(),
            
            # Core explanation
            "executive_summary": narrative,
            
            # Detailed factor breakdown
            "factor_analysis": factor_explanations,
            
            # Top 3 risk drivers
            "key_risk_drivers": top_risk_factors,
            
            # Comparative context
            "comparative_analysis": comparative_analysis,
            
            # Evidence supporting assessment
            "supporting_evidence": evidence,
            
            # Actionable next steps
            "recommendations": recommendations,
            
            # Confidence and limitations
            "confidence_metrics": self._calculate_confidence(student_id, factors),
            
            # Ethical considerations
            "disclaimer": "This assessment is analytical guidance, not a prediction. Student outcomes depend on many factors and personal agency."
        }
        
        return explanation
    
    def _categorize_risk(self, risk_score: float) -> tuple:
        """Categorize risk into levels with colors"""
        if risk_score < 0.25:
            return "Low Risk", "green"
        elif risk_score < 0.50:
            return "Moderate Risk", "yellow"
        elif risk_score < 0.75:
            return "High Risk", "orange"
        else:
            return "Critical Risk", "red"
    
    def _explain_factors(self, student_id: int, factors: Dict[str, float]) -> List[Dict[str, Any]]:
        """Provide detailed explanation for each factor"""
        
        explanations = []
        
        for factor_name, factor_score in factors.items():
            impact_level = self._get_impact_level(factor_score)
            
            # Get specific context for this factor
            context = self._get_factor_context(student_id, factor_name)
            
            explanation = {
                "factor_name": factor_name.replace('_', ' ').title(),
                "score": round(factor_score, 3),
                "impact_level": impact_level,
                "description": self._get_factor_description(factor_name),
                "current_status": context,
                "interpretation": self._interpret_factor(factor_name, factor_score, context)
            }
            
            explanations.append(explanation)
        
        # Sort by impact (highest first)
        explanations.sort(key=lambda x: x['score'], reverse=True)
        
        return explanations
    
    def _get_impact_level(self, score: float) -> str:
        """Determine impact level of a factor"""
        if score < 0.2:
            return "Minimal"
        elif score < 0.4:
            return "Low"
        elif score < 0.6:
            return "Moderate"
        elif score < 0.8:
            return "High"
        else:
            return "Critical"
    
    def _get_factor_description(self, factor_name: str) -> str:
        """Get human-readable description of factor"""
        descriptions = {
            "academic_performance": "Overall academic achievement measured by CGPA and grade trends",
            "attendance": "Class attendance percentage and consistency",
            "behavioral": "Engagement, participation, and behavioral observations",
            "stress_level": "Mental health indicators and stress factors",
            "engagement": "Academic engagement, participation, and motivation",
            "progression": "Credit completion rate and academic progression speed"
        }
        return descriptions.get(factor_name, "Contributing factor to overall risk assessment")
    
    def _get_factor_context(self, student_id: int, factor_name: str) -> Dict[str, Any]:
        """Get specific data context for a factor"""
        
        context = {}
        
        if factor_name == "academic_performance":
            grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
            if grades:
                cgpa = sum(g.grade_point * g.credits for g in grades) / sum(g.credits for g in grades)
                context = {
                    "cgpa": round(cgpa, 2),
                    "courses_completed": len(grades),
                    "recent_trend": self._calculate_grade_trend(grades)
                }
        
        elif factor_name == "attendance":
            attendance = self.db.query(Attendance).filter(
                Attendance.student_id == student_id
            ).all()
            if attendance:
                avg_attendance = sum(a.percentage for a in attendance) / len(attendance)
                context = {
                    "average_attendance": round(avg_attendance, 2),
                    "records_count": len(attendance),
                    "trend": "declining" if len(attendance) > 1 and attendance[-1].percentage < attendance[0].percentage else "stable"
                }
        
        elif factor_name == "behavioral":
            logs = self.db.query(BehavioralLog).filter(
                BehavioralLog.student_id == student_id
            ).order_by(BehavioralLog.log_date.desc()).limit(5).all()
            
            if logs:
                engagement_levels = [log.engagement_level for log in logs if log.engagement_level]
                context = {
                    "recent_observations": len(logs),
                    "avg_engagement": round(sum(engagement_levels) / len(engagement_levels), 2) if engagement_levels else None,
                    "latest_note": logs[0].notes if logs else None
                }
        
        elif factor_name == "stress_level":
            logs = self.db.query(BehavioralLog).filter(
                BehavioralLog.student_id == student_id
            ).order_by(BehavioralLog.log_date.desc()).limit(5).all()
            
            stress_levels = [log.stress_level for log in logs if log.stress_level]
            if stress_levels:
                context = {
                    "average_stress": round(sum(stress_levels) / len(stress_levels), 2),
                    "max_stress": max(stress_levels),
                    "recent_trend": "increasing" if len(stress_levels) > 1 and stress_levels[0] > stress_levels[-1] else "stable"
                }
        
        return context
    
    def _interpret_factor(self, factor_name: str, score: float, context: Dict) -> str:
        """Generate human-readable interpretation"""
        
        if factor_name == "academic_performance":
            cgpa = context.get('cgpa', 0)
            if score < 0.3:
                return f"Strong academic performance with CGPA of {cgpa}. Maintaining consistent grades."
            elif score < 0.6:
                return f"Moderate academic standing with CGPA of {cgpa}. Some areas need improvement."
            else:
                return f"Academic performance requires attention. CGPA of {cgpa} is below optimal level."
        
        elif factor_name == "attendance":
            avg = context.get('average_attendance', 0)
            if score < 0.3:
                return f"Excellent attendance at {avg}%. Consistently present in classes."
            elif score < 0.6:
                return f"Attendance at {avg}% needs improvement. Missing classes impacts learning."
            else:
                return f"Critical attendance issue at {avg}%. Regular absence is a major concern."
        
        elif factor_name == "behavioral":
            if score < 0.3:
                return "Positive engagement and participation observed. Active in academic activities."
            elif score < 0.6:
                return "Some behavioral concerns noted. Engagement could be improved."
            else:
                return "Significant behavioral concerns. Low engagement and participation noted."
        
        elif factor_name == "stress_level":
            avg_stress = context.get('average_stress')
            if avg_stress:
                if score < 0.3:
                    return f"Stress levels appear manageable (avg: {avg_stress}/10). No immediate concerns."
                elif score < 0.6:
                    return f"Moderate stress levels detected (avg: {avg_stress}/10). Monitoring recommended."
                else:
                    return f"High stress levels observed (avg: {avg_stress}/10). Support services recommended."
        
        return "Contributing to overall risk assessment. Monitoring recommended."
    
    def _calculate_grade_trend(self, grades: List[Grade]) -> str:
        """Calculate if grades are improving, declining, or stable"""
        if len(grades) < 3:
            return "insufficient_data"
        
        # Sort by semester
        sorted_grades = sorted(grades, key=lambda g: g.semester)
        recent_gpa = sum(g.grade_point for g in sorted_grades[-3:]) / 3
        older_gpa = sum(g.grade_point for g in sorted_grades[:3]) / 3
        
        if recent_gpa > older_gpa + 0.3:
            return "improving"
        elif recent_gpa < older_gpa - 0.3:
            return "declining"
        else:
            return "stable"
    
    def _identify_top_risks(self, factor_explanations: List[Dict]) -> List[Dict]:
        """Identify top 3 risk drivers"""
        # Already sorted by score
        return factor_explanations[:3]
    
    def _generate_comparative_analysis(self, student_id: int, factors: Dict) -> Dict[str, Any]:
        """Compare student's metrics against cohort"""
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        
        # Get cohort (same branch and batch)
        cohort = self.db.query(Student).filter(
            Student.branch == student.branch,
            Student.batch == student.batch,
            Student.id != student_id
        ).all()
        
        if not cohort:
            return {"message": "Insufficient cohort data for comparison"}
        
        # Calculate cohort statistics
        cohort_cgpas = []
        for peer in cohort:
            grades = self.db.query(Grade).filter(Grade.student_id == peer.id).all()
            if grades:
                cgpa = sum(g.grade_point * g.credits for g in grades) / sum(g.credits for g in grades)
                cohort_cgpas.append(cgpa)
        
        # Student's CGPA
        student_grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        student_cgpa = 0
        if student_grades:
            student_cgpa = sum(g.grade_point * g.credits for g in student_grades) / sum(g.credits for g in student_grades)
        
        comparison = {
            "cohort_size": len(cohort),
            "student_cgpa": round(student_cgpa, 2),
            "cohort_average_cgpa": round(statistics.mean(cohort_cgpas), 2) if cohort_cgpas else None,
            "cohort_median_cgpa": round(statistics.median(cohort_cgpas), 2) if cohort_cgpas else None,
            "percentile_rank": self._calculate_percentile(student_cgpa, cohort_cgpas) if cohort_cgpas else None,
            "interpretation": self._interpret_percentile(self._calculate_percentile(student_cgpa, cohort_cgpas)) if cohort_cgpas else "Insufficient data"
        }
        
        return comparison
    
    def _calculate_percentile(self, value: float, values: List[float]) -> float:
        """Calculate percentile rank"""
        if not values:
            return 0.0
        below = sum(1 for v in values if v < value)
        return round((below / len(values)) * 100, 1)
    
    def _interpret_percentile(self, percentile: float) -> str:
        """Interpret percentile rank"""
        if percentile >= 75:
            return "Performing in the top quartile of the cohort"
        elif percentile >= 50:
            return "Performing above the median of the cohort"
        elif percentile >= 25:
            return "Performing below the cohort median"
        else:
            return "Performing in the bottom quartile - requires attention"
    
    def _generate_recommendations(self, student_id: int, top_risks: List[Dict], risk_score: float) -> List[Dict[str, str]]:
        """Generate personalized, actionable recommendations"""
        
        recommendations = []
        
        for risk in top_risks:
            factor = risk['factor_name'].lower().replace(' ', '_')
            impact = risk['impact_level']
            
            if impact in ["High", "Critical"]:
                recs = self._get_recommendations_for_factor(factor, impact)
                recommendations.extend(recs)
        
        # Add general recommendations based on overall risk
        if risk_score > 0.7:
            recommendations.append({
                "priority": "High",
                "category": "Immediate Action",
                "recommendation": "Schedule meeting with academic advisor within 48 hours",
                "rationale": "Critical risk level requires immediate intervention and support planning"
            })
        
        return recommendations[:5]  # Top 5 recommendations
    
    def _get_recommendations_for_factor(self, factor: str, impact: str) -> List[Dict]:
        """Get specific recommendations for a factor"""
        
        recommendations_map = {
            "academic_performance": [
                {
                    "priority": "High",
                    "category": "Academic Support",
                    "recommendation": "Enroll in peer tutoring program for struggling subjects",
                    "rationale": "One-on-one tutoring has shown 30% improvement in grades"
                },
                {
                    "priority": "Medium",
                    "category": "Study Skills",
                    "recommendation": "Attend study skills workshop and time management training",
                    "rationale": "Building foundational study habits improves long-term outcomes"
                }
            ],
            "attendance": [
                {
                    "priority": "High",
                    "category": "Attendance Improvement",
                    "recommendation": "Meet with counselor to identify and address attendance barriers",
                    "rationale": "Understanding root causes is key to improving attendance patterns"
                }
            ],
            "behavioral": [
                {
                    "priority": "Medium",
                    "category": "Engagement",
                    "recommendation": "Join student study groups or academic clubs in your field",
                    "rationale": "Peer engagement improves motivation and academic connection"
                }
            ],
            "stress_level": [
                {
                    "priority": "High",
                    "category": "Wellbeing",
                    "recommendation": "Connect with campus counseling services for stress management",
                    "rationale": "Mental health support is crucial for academic success"
                }
            ]
        }
        
        return recommendations_map.get(factor, [])
    
    def _build_narrative(self, student: Student, risk_score: float, risk_level: str, top_risks: List[Dict]) -> str:
        """Build a narrative summary of the risk assessment"""
        
        narrative_parts = []
        
        # Opening
        narrative_parts.append(
            f"{student.name} (Roll: {student.roll_number}) currently has a {risk_level} with an assessment score of {round(risk_score, 2)}."
        )
        
        # Key factors
        if top_risks:
            factor_names = [r['factor_name'] for r in top_risks[:2]]
            narrative_parts.append(
                f"The primary factors contributing to this assessment are {factor_names[0]}"
            )
            if len(factor_names) > 1:
                narrative_parts[-1] += f" and {factor_names[1]}"
            narrative_parts[-1] += "."
        
        # Context
        if risk_score < 0.3:
            narrative_parts.append(
                "The student is demonstrating strong academic performance and positive engagement. Continue monitoring for sustained success."
            )
        elif risk_score < 0.6:
            narrative_parts.append(
                "The student shows some areas requiring attention. Early intervention and targeted support can prevent escalation."
            )
        else:
            narrative_parts.append(
                "The student requires immediate attention and structured intervention. Coordinated support from advisors, faculty, and counselors is recommended."
            )
        
        return " ".join(narrative_parts)
    
    def _gather_evidence(self, student_id: int, top_risks: List[Dict]) -> List[Dict[str, Any]]:
        """Gather specific evidence supporting the assessment"""
        
        evidence = []
        
        # Recent grades
        recent_grades = self.db.query(Grade).filter(
            Grade.student_id == student_id
        ).order_by(Grade.semester.desc()).limit(3).all()
        
        if recent_grades:
            evidence.append({
                "type": "Academic Records",
                "data": [
                    {
                        "course": g.subject_code,
                        "grade": g.grade_point,
                        "semester": g.semester
                    } for g in recent_grades
                ],
                "timestamp": datetime.now().isoformat()
            })
        
        # Recent mentor notes
        recent_notes = self.db.query(MentorNote).filter(
            MentorNote.student_id == student_id
        ).order_by(MentorNote.created_at.desc()).limit(2).all()
        
        if recent_notes:
            evidence.append({
                "type": "Mentor Observations",
                "data": [
                    {
                        "note": n.note_text[:200] + "..." if len(n.note_text) > 200 else n.note_text,
                        "date": n.note_date.isoformat(),
                        "sentiment": n.sentiment
                    } for n in recent_notes
                ],
                "timestamp": datetime.now().isoformat()
            })
        
        return evidence
    
    def _calculate_confidence(self, student_id: int, factors: Dict) -> Dict[str, Any]:
        """Calculate confidence metrics for the assessment"""
        
        # Data completeness
        student = self.db.query(Student).filter(Student.id == student_id).first()
        grades_count = self.db.query(Grade).filter(Grade.student_id == student_id).count()
        attendance_count = self.db.query(Attendance).filter(Attendance.student_id == student_id).count()
        notes_count = self.db.query(MentorNote).filter(MentorNote.student_id == student_id).count()
        
        data_completeness = min(100, (grades_count * 10 + attendance_count * 5 + notes_count * 10))
        
        confidence = {
            "overall_confidence": "High" if data_completeness > 70 else "Medium" if data_completeness > 40 else "Low",
            "data_completeness_score": min(100, data_completeness),
            "data_sources": {
                "grades_records": grades_count,
                "attendance_records": attendance_count,
                "mentor_notes": notes_count
            },
            "limitations": []
        }
        
        if grades_count < 3:
            confidence['limitations'].append("Limited academic history - assessment based on early data")
        
        if notes_count == 0:
            confidence['limitations'].append("No mentor observations available - assessment relies solely on quantitative data")
        
        return confidence


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from database.init_db import SessionLocal
    from services.risk_calculator import RiskCalculator
    
    load_dotenv()
    
    db = SessionLocal()
    
    # Get risk data
    risk_calc = RiskCalculator(db)
    risk_data = risk_calc.calculate_risk(student_id=1)
    
    # Generate explanation
    explainer = ExplainabilityEngine(db)
    explanation = explainer.explain_risk_score(1, risk_data)
    
    print("\n" + "="*80)
    print("EXPLAINABLE RISK ASSESSMENT")
    print("="*80)
    print(f"\nStudent: {explanation['student_name']}")
    print(f"Risk Level: {explanation['risk_level']} ({explanation['risk_score']})")
    print(f"\n{explanation['executive_summary']}")
    print("\n" + "="*80)
    
    db.close()
