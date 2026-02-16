"""
Career Prediction Service - Maps academic performance to career recommendations
Uses RAG to provide evidence-based career guidance aligned with student strengths
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from models.student import Student, Grade, MentorNote, BehavioralLog
import statistics

class CareerPredictor:
    """
    Analyzes student academic profile and predicts suitable career paths
    Based on subject performance, interests, and behavioral patterns
    """
    
    def __init__(self, db: Session):
        self.db = db
        
        # Career path requirements (simplified model)
        self.career_profiles = {
            "Software Engineer": {
                "key_subjects": ["programming", "data structures", "algorithms", "database", "software"],
                "min_cgpa": 7.0,
                "skills": ["coding", "problem solving", "logical thinking"],
                "industry_demand": "Very High",
                "salary_range": "8-25 LPA"
            },
            "Data Scientist": {
                "key_subjects": ["machine learning", "statistics", "python", "data", "analytics"],
                "min_cgpa": 7.5,
                "skills": ["analytical thinking", "statistics", "programming"],
                "industry_demand": "Very High",
                "salary_range": "10-30 LPA"
            },
            "Cloud Architect": {
                "key_subjects": ["cloud computing", "networks", "distributed systems", "devops"],
                "min_cgpa": 7.0,
                "skills": ["system design", "cloud platforms", "automation"],
                "industry_demand": "High",
                "salary_range": "12-35 LPA"
            },
            "Cyber Security Analyst": {
                "key_subjects": ["security", "cryptography", "networks", "ethical hacking"],
                "min_cgpa": 7.0,
                "skills": ["security mindset", "attention to detail", "problem solving"],
                "industry_demand": "High",
                "salary_range": "8-22 LPA"
            },
            "Full Stack Developer": {
                "key_subjects": ["web development", "frontend", "backend", "database", "api"],
                "min_cgpa": 6.5,
                "skills": ["web technologies", "ui/ux", "api design"],
                "industry_demand": "Very High",
                "salary_range": "7-20 LPA"
            },
            "AI/ML Engineer": {
                "key_subjects": ["artificial intelligence", "machine learning", "deep learning", "neural networks"],
                "min_cgpa": 8.0,
                "skills": ["mathematical aptitude", "research orientation", "programming"],
                "industry_demand": "Very High",
                "salary_range": "12-40 LPA"
            },
            "DevOps Engineer": {
                "key_subjects": ["linux", "automation", "docker", "kubernetes", "ci/cd"],
                "min_cgpa": 6.5,
                "skills": ["automation", "scripting", "infrastructure"],
                "industry_demand": "High",
                "salary_range": "9-25 LPA"
            },
            "Mobile App Developer": {
                "key_subjects": ["mobile development", "android", "ios", "app design"],
                "min_cgpa": 6.5,
                "skills": ["mobile platforms", "ui/ux", "api integration"],
                "industry_demand": "High",
                "salary_range": "7-20 LPA"
            },
            "Business Analyst": {
                "key_subjects": ["business", "analytics", "communication", "requirements"],
                "min_cgpa": 6.5,
                "skills": ["communication", "analytical thinking", "business acumen"],
                "industry_demand": "Medium",
                "salary_range": "6-18 LPA"
            },
            "Research Scientist": {
                "key_subjects": ["research methods", "algorithms", "theory", "mathematics"],
                "min_cgpa": 8.5,
                "skills": ["research aptitude", "academic excellence", "innovation"],
                "industry_demand": "Medium",
                "salary_range": "10-35 LPA (academia/industry)"
            }
        }
    
    def predict_career_paths(self, student_id: int, top_n: int = 5) -> Dict[str, Any]:
        """
        Predict most suitable career paths for a student
        
        Args:
            student_id: Student's unique identifier
            top_n: Number of top recommendations to return
            
        Returns:
            Career predictions with match scores and explanations
        """
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {"error": "Student not found"}
        
        # Get student's academic profile
        profile = self._build_student_profile(student_id)
        
        # Calculate match scores for each career
        career_matches = []
        
        for career_name, career_req in self.career_profiles.items():
            match_score = self._calculate_career_match(profile, career_req)
            
            if match_score['total_score'] > 0:  # Only include viable careers
                career_matches.append({
                    "career_name": career_name,
                    "match_score": match_score['total_score'],
                    "match_percentage": round(match_score['total_score'] * 100, 1),
                    "score_breakdown": match_score['breakdown'],
                    "career_details": career_req,
                    "why_suitable": self._explain_career_match(career_name, profile, match_score),
                    "preparation_steps": self._get_preparation_steps(career_name, profile)
                })
        
        # Sort by match score
        career_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # Get top N recommendations
        top_recommendations = career_matches[:top_n]
        
        response = {
            "student_id": student_id,
            "student_name": student.name,
            "current_cgpa": profile['cgpa'],
            "current_semester": student.current_semester,
            "analysis_date": profile['analysis_date'],
            
            "top_career_recommendations": top_recommendations,
            
            "strengths_identified": profile['strengths'],
            
            "skill_development_needed": self._identify_skill_gaps(profile, top_recommendations),
            
            "general_advice": self._generate_career_advice(profile, top_recommendations)
        }
        
        return response
    
    def _build_student_profile(self, student_id: int) -> Dict[str, Any]:
        """Build comprehensive academic profile"""
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        
        # Calculate CGPA
        cgpa = 0.0
        if grades:
            total_points = sum(g.grade_point * g.credits for g in grades)
            total_credits = sum(g.credits for g in grades)
            cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        
        # Identify strong subjects (grade > 8.0)
        strong_subjects = [
            g.subject_code.lower() for g in grades if g.grade_point >= 8.0
        ]
        
        # Subject areas with consistent performance
        subject_performance = {}
        for grade in grades:
            subject_performance[grade.subject_code.lower()] = grade.grade_point
        
        # Identify interest areas from mentor notes
        notes = self.db.query(MentorNote).filter(
            MentorNote.student_id == student_id
        ).all()
        
        interests = []
        for note in notes:
            text = note.note_text.lower()
            if "interest" in text:
                interests.append(text)
        
        # Behavioral traits
        behavioral_logs = self.db.query(BehavioralLog).filter(
            BehavioralLog.student_id == student_id
        ).all()
        
        avg_engagement = None
        if behavioral_logs:
            engagement_scores = [b.engagement_level for b in behavioral_logs if b.engagement_level]
            if engagement_scores:
                avg_engagement = round(statistics.mean(engagement_scores), 2)
        
        profile = {
            "student_id": student_id,
            "branch": student.branch,
            "semester": student.current_semester,
            "cgpa": cgpa,
            "strong_subjects": strong_subjects,
            "subject_performance": subject_performance,
            "interests_mentioned": interests,
            "avg_engagement": avg_engagement,
            "analysis_date": "2026-02-16",
            "strengths": self._identify_strengths(cgpa, strong_subjects, avg_engagement)
        }
        
        return profile
    
    def _calculate_career_match(self, profile: Dict, career_req: Dict) -> Dict[str, Any]:
        """Calculate how well a student matches a career path"""
        
        scores = {}
        
        # 1. CGPA Match (30% weight)
        cgpa_score = 0.0
        if profile['cgpa'] >= career_req['min_cgpa']:
            cgpa_score = min(1.0, profile['cgpa'] / 10.0)
        else:
            cgpa_score = max(0, profile['cgpa'] / career_req['min_cgpa'] - 0.2)
        
        scores['cgpa_match'] = round(cgpa_score * 0.3, 3)
        
        # 2. Subject Match (50% weight)
        subject_matches = 0
        total_key_subjects = len(career_req['key_subjects'])
        
        for key_subject in career_req['key_subjects']:
            # Check if student has done well in related subjects
            for student_subject in profile['strong_subjects']:
                if key_subject in student_subject or student_subject in key_subject:
                    subject_matches += 1
                    break
        
        subject_score = subject_matches / total_key_subjects if total_key_subjects > 0 else 0
        scores['subject_match'] = round(subject_score * 0.5, 3)
        
        # 3. Engagement (20% weight)
        engagement_score = 0.0
        if profile['avg_engagement']:
            engagement_score = profile['avg_engagement'] / 10.0
        else:
            engagement_score = 0.7  # Default moderate engagement
        
        scores['engagement_match'] = round(engagement_score * 0.2, 3)
        
        # Total score
        total = sum(scores.values())
        
        return {
            "total_score": round(total, 3),
            "breakdown": scores
        }
    
    def _explain_career_match(self, career_name: str, profile: Dict, match_score: Dict) -> str:
        """Generate explanation for career recommendation"""
        
        explanations = []
        
        breakdown = match_score['breakdown']
        
        if breakdown['subject_match'] > 0.3:
            explanations.append(f"Strong performance in relevant technical subjects")
        
        if breakdown['cgpa_match'] > 0.25:
            explanations.append(f"CGPA of {profile['cgpa']} meets requirements")
        
        if breakdown['engagement_match'] > 0.15:
            explanations.append(f"Good academic engagement level")
        
        if not explanations:
            explanations.append("Viable option with further skill development")
        
        return "; ".join(explanations)
    
    def _get_preparation_steps(self, career_name: str, profile: Dict) -> List[str]:
        """Get actionable steps to prepare for this career"""
        
        career_req = self.career_profiles[career_name]
        
        steps = []
        
        # Check if CGPA needs improvement
        if profile['cgpa'] < career_req['min_cgpa']:
            gap = career_req['min_cgpa'] - profile['cgpa']
            steps.append(f"Focus on improving CGPA by {gap:.1f} points through consistent performance")
        
        # Subject-specific recommendations
        missing_subjects = []
        for key_subject in career_req['key_subjects']:
            found = False
            for student_subject in profile['strong_subjects']:
                if key_subject in student_subject:
                    found = True
                    break
            if not found:
                missing_subjects.append(key_subject)
        
        if missing_subjects:
            steps.append(f"Strengthen knowledge in: {', '.join(missing_subjects[:3])}")
        
        # Skill development
        steps.append(f"Develop skills: {', '.join(career_req['skills'][:3])}")
        
        # Practical experience
        steps.append(f"Gain hands-on experience through projects and internships in {career_name.lower()}")
        
        # Certifications
        if career_name in ["Data Scientist", "Cloud Architect", "Cyber Security Analyst"]:
            steps.append("Consider relevant industry certifications to enhance credibility")
        
        return steps[:5]
    
    def _identify_strengths(self, cgpa: float, strong_subjects: List[str], engagement: Optional[float]) -> List[str]:
        """Identify student's key strengths"""
        
        strengths = []
        
        if cgpa >= 8.5:
            strengths.append("Academic Excellence")
        elif cgpa >= 7.5:
            strengths.append("Strong Academic Performance")
        elif cgpa >= 6.5:
            strengths.append("Consistent Academic Standing")
        
        if len(strong_subjects) >= 5:
            strengths.append("Broad Technical Competence")
        elif len(strong_subjects) >= 3:
            strengths.append("Focused Technical Strength")
        
        if engagement and engagement >= 8.0:
            strengths.append("High Engagement & Motivation")
        
        # Subject area analysis
        programming_subjects = [s for s in strong_subjects if any(
            kw in s for kw in ['program', 'code', 'software', 'java', 'python', 'cpp']
        )]
        
        if len(programming_subjects) >= 2:
            strengths.append("Programming Aptitude")
        
        return strengths if strengths else ["Developing Skills"]
    
    def _identify_skill_gaps(self, profile: Dict, recommendations: List[Dict]) -> List[str]:
        """Identify skills needing development"""
        
        gaps = []
        
        if profile['cgpa'] < 7.0:
            gaps.append("Academic performance improvement needed")
        
        if len(profile['strong_subjects']) < 3:
            gaps.append("Broaden technical subject performance")
        
        if profile['avg_engagement'] and profile['avg_engagement'] < 6.0:
            gaps.append("Increase academic engagement and participation")
        
        # Check if top recommendations require skills student hasn't demonstrated
        if recommendations:
            top_career = recommendations[0]
            if top_career['match_percentage'] < 60:
                gaps.append("Focus on developing key skills for target careers")
        
        return gaps if gaps else ["Continue building on current strengths"]
    
    def _generate_career_advice(self, profile: Dict, recommendations: List[Dict]) -> str:
        """Generate general career guidance"""
        
        if not recommendations:
            return "Focus on improving academic performance and exploring different subject areas to identify interests."
        
        top_match = recommendations[0]
        
        advice_parts = []
        
        if top_match['match_percentage'] >= 70:
            advice_parts.append(f"You show strong potential for {top_match['career_name']}.")
        elif top_match['match_percentage'] >= 50:
            advice_parts.append(f"{top_match['career_name']} is a viable path with focused preparation.")
        else:
            advice_parts.append("Explore multiple career options while building foundational skills.")
        
        if profile['semester'] <= 4:
            advice_parts.append("Early semesters are ideal for exploring internships and building projects.")
        elif profile['semester'] <= 6:
            advice_parts.append("Focus on targeted internships and specialized skill development.")
        else:
            advice_parts.append("Prioritize interview preparation and industry-specific projects.")
        
        advice_parts.append("Consider joining relevant student clubs, contributing to open-source, and building a strong portfolio.")
        
        return " ".join(advice_parts)


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from database.init_db import SessionLocal
    import json
    
    load_dotenv()
    
    db = SessionLocal()
    
    career_predictor = CareerPredictor(db)
    predictions = career_predictor.predict_career_paths(student_id=1, top_n=5)
    
    print("\n" + "="*80)
    print("CAREER PATH PREDICTIONS")
    print("="*80)
    print(f"\nStudent: {predictions['student_name']}")
    print(f"Current CGPA: {predictions['current_cgpa']}")
    print(f"\nTop Career Recommendations:")
    
    for i, career in enumerate(predictions['top_career_recommendations'], 1):
        print(f"\n{i}. {career['career_name']} - {career['match_percentage']}% Match")
        print(f"   {career['why_suitable']}")
        print(f"   Salary Range: {career['career_details']['salary_range']}")
    
    print("\n" + "="*80)
    
    db.close()
