"""
Stress & Behavioral Detection Service
Analyzes behavioral patterns, mentor feedback, and engagement metrics to detect stress and wellbeing concerns
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.student import Student, BehavioralLog, MentorNote, Attendance
from datetime import datetime, timedelta
import statistics
import re

class StressDetector:
    """
    Detects stress indicators and behavioral concerns from multiple data sources
    Uses sentiment analysis, attendance patterns, and engagement metrics
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Stress indicator keywords (simplified NLP-based detection)
        self.stress_keywords = {
            "high": ["stressed", "anxious", "overwhelmed", "pressure", "struggling", "worried", 
                    "difficult", "hard time", "can't cope", "breaking down", "exhausted"],
            "moderate": ["tired", "confused", "uncertain", "questioning", "frustrated", 
                        "challenging", "concerned", "hesitant", "unsure"],
            "positive": ["confident", "motivated", "improving", "engaged", "enthusiastic", 
                        "focused", "determined", "positive", "happy", "excited"]
        }
        
        # Behavioral concern patterns
        self.concern_patterns = {
            "social_withdrawal": ["isolated", "withdrawn", "alone", "avoiding", "distant", "quiet"],
            "academic_disengagement": ["disengaged", "uninterested", "absent", "missing", "incomplete", "late"],
            "emotional_distress": ["sad", "depressed", "upset", "crying", "emotional", "distressed"],
            "health_concerns": ["sick", "tired", "fatigue", "sleep", "health", "unwell"]
        }
    
    def analyze_student_wellbeing(self, student_id: int) -> Dict[str, Any]:
        """
        Comprehensive wellbeing analysis for a student
        
        Args:
            student_id: Student's unique identifier
            
        Returns:
            Detailed wellbeing assessment with stress indicators
        """
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        # Analyze different data sources
        stress_assessment = self._analyze_stress_levels(student_id)
        behavioral_analysis = self._analyze_behavioral_patterns(student_id)
        mentor_insights = self._analyze_mentor_observations(student_id)
        attendance_patterns = self._analyze_attendance_patterns(student_id)
        
        # Calculate overall wellbeing score (0-10, higher is better)
        wellbeing_score = self._calculate_wellbeing_score(
            stress_assessment,
            behavioral_analysis,
            attendance_patterns
        )
        
        # Determine alert level
        alert_level, alert_color = self._determine_alert_level(wellbeing_score, stress_assessment)
        
        # Generate recommendations
        recommendations = self._generate_wellbeing_recommendations(
            stress_assessment,
            behavioral_analysis,
            mentor_insights,
            wellbeing_score
        )
        
        # Identify trends
        trends = self._identify_wellbeing_trends(student_id)
        
        analysis = {
            "student_id": student_id,
            "student_name": student.name,
            "analysis_date": datetime.now().isoformat(),
            
            # Overall Assessment
            "wellbeing_score": round(wellbeing_score, 2),
            "alert_level": alert_level,
            "alert_color": alert_color,
            
            # Detailed Analysis
            "stress_assessment": stress_assessment,
            "behavioral_patterns": behavioral_analysis,
            "mentor_observations": mentor_insights,
            "attendance_analysis": attendance_patterns,
            
            # Trends
            "trends": trends,
            
            # Action Items
            "recommendations": recommendations,
            "requires_intervention": alert_level in ["High Alert", "Critical"],
            "suggested_contacts": self._suggest_support_contacts(alert_level),
            
            # Context
            "disclaimer": "This analysis is for support purposes only. Professional counseling should be sought for serious concerns."
        }
        
        return analysis
    
    def _analyze_stress_levels(self, student_id: int) -> Dict[str, Any]:
        """Analyze explicit stress level data"""
        
        # Get recent behavioral logs with stress data
        recent_logs = self.db.query(BehavioralLog).filter(
            BehavioralLog.student_id == student_id
        ).order_by(BehavioralLog.log_date.desc()).limit(10).all()
        
        if not recent_logs:
            return {
                "data_available": False,
                "message": "No stress data recorded"
            }
        
        # Extract stress levels
        stress_levels = [log.stress_level for log in recent_logs if log.stress_level is not None]
        
        if not stress_levels:
            return {
                "data_available": False,
                "message": "No stress measurements available"
            }
        
        avg_stress = statistics.mean(stress_levels)
        max_stress = max(stress_levels)
        latest_stress = stress_levels[0] if stress_levels else None
        
        # Trend analysis
        if len(stress_levels) >= 3:
            recent_avg = statistics.mean(stress_levels[:3])
            older_avg = statistics.mean(stress_levels[-3:])
            trend = "increasing" if recent_avg > older_avg + 1 else ("decreasing" if recent_avg < older_avg - 1 else "stable")
        else:
            trend = "insufficient_data"
        
        return {
            "data_available": True,
            "average_stress_level": round(avg_stress, 2),
            "latest_stress_level": latest_stress,
            "max_stress_level": max_stress,
            "trend": trend,
            "measurements_count": len(stress_levels),
            "assessment": self._interpret_stress_level(avg_stress),
            "concern_level": "high" if avg_stress > 7 else ("moderate" if avg_stress > 5 else "low")
        }
    
    def _interpret_stress_level(self, avg_stress: float) -> str:
        """Interpret stress level value"""
        if avg_stress <= 3:
            return "Low stress - Student appears to be managing well"
        elif avg_stress <= 5:
            return "Moderate stress - Normal academic pressure"
        elif avg_stress <= 7:
            return "Elevated stress - May benefit from support"
        else:
            return "High stress - Intervention recommended"
    
    def _analyze_behavioral_patterns(self, student_id: int) -> Dict[str, Any]:
        """Analyze behavioral logs for patterns"""
        
        logs = self.db.query(BehavioralLog).filter(
            BehavioralLog.student_id == student_id
        ).order_by(BehavioralLog.log_date.desc()).limit(15).all()
        
        if not logs:
            return {"patterns_detected": []}
        
        # Analyze engagement levels
        engagement_levels = [log.engagement_level for log in logs if log.engagement_level]
        avg_engagement = statistics.mean(engagement_levels) if engagement_levels else None
        
        # Analyze notes for concerning patterns
        all_notes = " ".join([log.notes.lower() for log in logs if log.notes])
        
        detected_patterns = []
        
        for pattern_name, keywords in self.concern_patterns.items():
            matches = sum(1 for keyword in keywords if keyword in all_notes)
            if matches > 0:
                detected_patterns.append({
                    "pattern": pattern_name.replace("_", " ").title(),
                    "frequency": matches,
                    "severity": "high" if matches >= 3 else "moderate"
                })
        
        return {
            "average_engagement": round(avg_engagement, 2) if avg_engagement else None,
            "engagement_status": self._interpret_engagement(avg_engagement) if avg_engagement else "Unknown",
            "patterns_detected": detected_patterns,
            "recent_observations_count": len(logs)
        }
    
    def _interpret_engagement(self, engagement: float) -> str:
        """Interpret engagement level"""
        if engagement >= 8:
            return "High engagement"
        elif engagement >= 6:
            return "Moderate engagement"
        elif engagement >= 4:
            return "Low engagement - concern"
        else:
            return "Very low engagement - significant concern"
    
    def _analyze_mentor_observations(self, student_id: int) -> Dict[str, Any]:
        """Analyze mentor notes for wellbeing insights"""
        
        notes = self.db.query(MentorNote).filter(
            MentorNote.student_id == student_id
        ).order_by(MentorNote.created_at.desc()).limit(10).all()
        
        if not notes:
            return {"insights_available": False}
        
        # Combine all note text
        all_text = " ".join([note.note_text.lower() for note in notes])
        
        # Count stress indicators
        stress_indicators = {
            "high_stress": sum(1 for keyword in self.stress_keywords["high"] if keyword in all_text),
            "moderate_stress": sum(1 for keyword in self.stress_keywords["moderate"] if keyword in all_text),
            "positive_indicators": sum(1 for keyword in self.stress_keywords["positive"] if keyword in all_text)
        }
        
        # Extract sentiment
        sentiments = [note.sentiment for note in notes if note.sentiment]
        avg_sentiment = None
        if sentiments:
            sentiment_map = {"positive": 1, "neutral": 0, "negative": -1}
            sentiment_scores = [sentiment_map.get(s, 0) for s in sentiments]
            avg_sentiment = statistics.mean(sentiment_scores)
        
        # Recent concerning notes
        concerning_notes = []
        for note in notes[:5]:
            if note.sentiment == "negative" or any(kw in note.note_text.lower() for kw in self.stress_keywords["high"]):
                concerning_notes.append({
                    "date": note.created_at.isoformat(),
                    "excerpt": note.note_text[:150] + "..." if len(note.note_text) > 150 else note.note_text,
                    "sentiment": note.sentiment
                })
        
        return {
            "insights_available": True,
            "stress_indicators": stress_indicators,
            "average_sentiment": round(avg_sentiment, 2) if avg_sentiment else None,
            "sentiment_interpretation": self._interpret_sentiment(avg_sentiment) if avg_sentiment else "Unknown",
            "concerning_notes_count": len(concerning_notes),
            "recent_concerning_notes": concerning_notes[:3],
            "total_notes_analyzed": len(notes)
        }
    
    def _interpret_sentiment(self, avg_sentiment: float) -> str:
        """Interpret average sentiment score"""
        if avg_sentiment > 0.3:
            return "Positive outlook observed"
        elif avg_sentiment > -0.3:
            return "Neutral/mixed observations"
        else:
            return "Concerning negative pattern"
    
    def _analyze_attendance_patterns(self, student_id: int) -> Dict[str, Any]:
        """Analyze attendance for behavioral indicators"""
        
        attendance_records = self.db.query(Attendance).filter(
            Attendance.student_id == student_id
        ).order_by(Attendance.month.desc()).limit(6).all()
        
        if not attendance_records:
            return {"data_available": False}
        
        percentages = [a.percentage for a in attendance_records]
        avg_attendance = statistics.mean(percentages)
        
        # Detect declining trend
        if len(percentages) >= 3:
            recent_avg = statistics.mean(percentages[:3])
            older_avg = statistics.mean(percentages[-3:])
            trend = "declining" if recent_avg < older_avg - 5 else ("improving" if recent_avg > older_avg + 5 else "stable")
        else:
            trend = "insufficient_data"
        
        # Irregular pattern (high variance)
        variance = statistics.variance(percentages) if len(percentages) > 1 else 0
        is_irregular = variance > 100  # High variance indicates inconsistency
        
        return {
            "data_available": True,
            "average_attendance": round(avg_attendance, 2),
            "trend": trend,
            "is_irregular": is_irregular,
            "latest_percentage": percentages[0],
            "assessment": self._interpret_attendance(avg_attendance, trend),
            "concern": avg_attendance < 75 or trend == "declining"
        }
    
    def _interpret_attendance(self, avg_attendance: float, trend: str) -> str:
        """Interpret attendance patterns"""
        if avg_attendance >= 85:
            return "Excellent attendance - no concerns"
        elif avg_attendance >= 75:
            if trend == "declining":
                return "Acceptable attendance but declining - monitor closely"
            return "Acceptable attendance"
        else:
            return "Poor attendance - significant concern requiring intervention"
    
    def _calculate_wellbeing_score(
        self,
        stress_assessment: Dict,
        behavioral_analysis: Dict,
        attendance_patterns: Dict
    ) -> float:
        """
        Calculate overall wellbeing score (0-10, higher is better)
        """
        score = 10.0  # Start with perfect score
        
        # Deduct for stress
        if stress_assessment.get("data_available"):
            avg_stress = stress_assessment.get("average_stress_level", 0)
            score -= (avg_stress / 10) * 4  # Max deduction: 4 points
        
        # Deduct for low engagement
        avg_engagement = behavioral_analysis.get("average_engagement")
        if avg_engagement:
            engagement_penalty = max(0, (7 - avg_engagement) / 7) * 3  # Max deduction: 3 points
            score -= engagement_penalty
        
        # Deduct for attendance issues
        if attendance_patterns.get("data_available"):
            attendance_pct = attendance_patterns.get("average_attendance", 100)
            if attendance_pct < 75:
                score -= (75 - attendance_pct) / 75 * 2  # Max deduction: 2 points
        
        # Deduct for behavioral concerns
        patterns = behavioral_analysis.get("patterns_detected", [])
        high_severity_patterns = [p for p in patterns if p.get("severity") == "high"]
        score -= len(high_severity_patterns) * 0.5
        
        return max(0, min(10, score))
    
    def _determine_alert_level(self, wellbeing_score: float, stress_assessment: Dict) -> tuple:
        """Determine alert level based on wellbeing score"""
        
        # Override for critical stress levels
        if stress_assessment.get("data_available"):
            if stress_assessment.get("latest_stress_level", 0) >= 9:
                return "Critical", "red"
        
        if wellbeing_score >= 8:
            return "Good", "green"
        elif wellbeing_score >= 6:
            return "Monitor", "yellow"
        elif wellbeing_score >= 4:
            return "High Alert", "orange"
        else:
            return "Critical", "red"
    
    def _generate_wellbeing_recommendations(
        self,
        stress_assessment: Dict,
        behavioral_analysis: Dict,
        mentor_insights: Dict,
        wellbeing_score: float
    ) -> List[Dict[str, str]]:
        """Generate actionable wellbeing recommendations"""
        
        recommendations = []
        
        # Stress-related recommendations
        if stress_assessment.get("concern_level") == "high":
            recommendations.append({
                "priority": "High",
                "category": "Mental Health",
                "action": "Connect student with campus counseling services immediately",
                "rationale": "High stress levels detected requiring professional support"
            })
        
        elif stress_assessment.get("concern_level") == "moderate":
            recommendations.append({
                "priority": "Medium",
                "category": "Stress Management",
                "action": "Encourage participation in stress management workshops",
                "rationale": "Moderate stress levels - preventive support beneficial"
            })
        
        # Engagement-related  recommendations
        avg_engagement = behavioral_analysis.get("average_engagement")
        if avg_engagement and avg_engagement < 5:
            recommendations.append({
                "priority": "High",
                "category": "Re-engagement",
                "action": "Schedule one-on-one mentor meeting to understand disengagement causes",
                "rationale": "Low engagement indicates disconnection from academics"
            })
        
        # Behavioral pattern recommendations
        patterns = behavioral_analysis.get("patterns_detected", [])
        for pattern in patterns:
            if pattern.get("severity") == "high":
                if "social_withdrawal" in pattern.get("pattern", "").lower():
                    recommendations.append({
                        "priority": "High",
                        "category": "Social Support",
                        "action": "Facilitate peer support connections and group activities",
                        "rationale": "Social withdrawal pattern detected"
                    })
        
        # Sentiment-based recommendations
        if mentor_insights.get("insights_available"):
            if mentor_insights.get("concerning_notes_count", 0) >= 2:
                recommendations.append({
                    "priority": "Medium",
                    "category": "Follow-up",
                    "action": "Conduct wellbeing check-in conversation",
                    "rationale": "Multiple concerning observations by mentors"
                })
        
        # Overall wellbeing  recommendations
        if wellbeing_score < 5:
            recommendations.append({
                "priority": "High",
                "category": "Comprehensive Support",
                "action": "Initiate multi-stakeholder support plan (mentor, counselor, family)",
                "rationale": "Low overall wellbeing score requires coordinated intervention"
            })
        
        return recommendations[:6]  # Top 6 recommendations
    
    def _identify_wellbeing_trends(self, student_id: int) -> Dict[str, str]:
        """Identify trends in wellbeing over time"""
        
        # Get historical data over last 60 days
        sixty_days_ago = datetime.now() - timedelta(days=60)
        
        recent_logs = self.db.query(BehavioralLog).filter(
            BehavioralLog.student_id == student_id,
            BehavioralLog.log_date >= sixty_days_ago
        ).order_by(BehavioralLog.log_date).all()
        
        trends = {}
        
        if len(recent_logs) >= 3:
            # Stress trend
            stress_levels = [log.stress_level for log in recent_logs if log.stress_level]
            if len(stress_levels) >= 3:
                first_half = stress_levels[:len(stress_levels)//2]
                second_half = stress_levels[len(stress_levels)//2:]
                if statistics.mean(second_half) > statistics.mean(first_half) + 1:
                    trends["stress"] = "increasing ⬆️"
                elif statistics.mean(second_half) < statistics.mean(first_half) - 1:
                    trends["stress"] = "decreasing ⬇️"
                else:
                    trends["stress"] = "stable ➡️"
            
            # Engagement trend
            engagement_levels = [log.engagement_level for log in recent_logs if log.engagement_level]
            if len(engagement_levels) >= 3:
                first_half = engagement_levels[:len(engagement_levels)//2]
                second_half = engagement_levels[len(engagement_levels)//2:]
                if statistics.mean(second_half) > statistics.mean(first_half) + 1:
                    trends["engagement"] = "improving ⬆️"
                elif statistics.mean(second_half) < statistics.mean(first_half) - 1:
                    trends["engagement"] = "declining ⬇️"
                else:
                    trends["engagement"] = "stable ➡️"
        
        return trends if trends else {"message": "Insufficient historical data for trend analysis"}
    
    def _suggest_support_contacts(self, alert_level: str) -> List[str]:
        """Suggest appropriate support contacts based on alert level"""
        
        contacts = []
        
        if alert_level in ["Critical", "High Alert"]:
            contacts.extend([
                "Campus Counseling Services (Primary Contact)",
                "Academic Mentor",
                "Department HOD",
                "Student Wellness Center"
            ])
        elif alert_level == "Monitor":
            contacts.extend([
                "Academic Mentor",
                "Peer Support Group",
                "Student Wellness Center"
            ])
        else:
            contacts.append("Regular mentor check-ins sufficient")
        
        return contacts


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from database.init_db import SessionLocal
    import json
    
    load_dotenv()
    
    db = SessionLocal()
    
    stress_detector = StressDetector(db)
    analysis = stress_detector.analyze_student_wellbeing(student_id=1)
    
    print("\n" + "="*80)
    print("STUDENT WELLBEING ANALYSIS")
    print("="*80)
    print(f"\nStudent: {analysis['student_name']}")
    print(f"Wellbeing Score: {analysis['wellbeing_score']}/10")
    print(f"Alert Level: {analysis['alert_level']}")
    
    print(f"\n📊 Stress Assessment:")
    if analysis['stress_assessment'].get('data_available'):
        print(f"   Average Stress: {analysis['stress_assessment']['average_stress_level']}/10")
        print(f"   {analysis['stress_assessment']['assessment']}")
    
    print(f"\n🎯 Behavioral Patterns:")
    if analysis['behavioral_patterns']['patterns_detected']:
        for pattern in analysis['behavioral_patterns']['patterns_detected']:
            print(f"   - {pattern['pattern']} (Severity: {pattern['severity']})")
    
    print(f"\n💡 Recommendations:")
    for rec in analysis['recommendations']:
        print(f"   [{rec['priority']}] {rec['action']}")
    
    print("\n" + "="*80)
    
    db.close()
