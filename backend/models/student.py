from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON, Text, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    roll_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    phone = Column(String(15))
    branch = Column(String(50))
    batch = Column(String(10))
    current_semester = Column(Integer)
    mentor_id = Column(Integer, ForeignKey('users.id'))
    
    # Additional fields for comprehensive tracking
    date_of_birth = Column(Date)
    address = Column(Text)
    parent_contact = Column(String(15))
    admission_date = Column(Date)
    
    # Relationships
    grades = relationship('Grade', back_populates='student', cascade='all, delete-orphan')
    attendance = relationship('Attendance', back_populates='student', cascade='all, delete-orphan')
    risk_scores = relationship('RiskScore', back_populates='student', cascade='all, delete-orphan')
    mentor_notes = relationship('MentorNote', back_populates='student', cascade='all, delete-orphan')
    behavioral_logs = relationship('BehavioralLog', back_populates='student', cascade='all, delete-orphan')
    interventions = relationship('Intervention', back_populates='student', cascade='all, delete-orphan')
    career_assessments = relationship('CareerAssessment', back_populates='student', cascade='all, delete-orphan')

class Grade(Base):
    __tablename__ = 'grades'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    semester = Column(Integer, nullable=False)
    subject_code = Column(String(20), nullable=False)
    subject_name = Column(String(100))
    grade_point = Column(Float)
    credits = Column(Integer)
    
    student = relationship('Student', back_populates='grades')

class Attendance(Base):
    __tablename__ = 'attendance'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    semester = Column(Integer)
    subject_code = Column(String(20))
    total_classes = Column(Integer)
    attended_classes = Column(Integer)
    percentage = Column(Float)
    
    student = relationship('Student', back_populates='attendance')

class RiskScore(Base):
    __tablename__ = 'risk_scores'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'))
    semester = Column(Integer)
    risk_score = Column(Float)  # SARS: 0.0 to 1.0
    risk_level = Column(String(20))  # low, moderate, high, critical
    confidence = Column(Float)
    factors = Column(JSON)  # Detailed breakdown of risk factors
    explanation = Column(Text)  # Human-readable explanation
    recommendations = Column(JSON)  # Intervention recommendations
    comparative_benchmark = Column(JSON)  # Comparison with peers
    historical_pattern = Column(JSON)  # Historical trend analysis
    generated_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship('Student', back_populates='risk_scores')

class User(Base):
    """Users table for authentication (students, faculty, admin)"""
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(100))
    role = Column(String(20), nullable=False)  # student, faculty, admin
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    
    # If user is a mentor/faculty
    department = Column(String(50))
    designation = Column(String(50))

class MentorNote(Base):
    """Mentor's qualitative observations about students"""
    __tablename__ = 'mentor_notes'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    mentor_id = Column(Integer, ForeignKey('users.id'))  # Made optional
    
    note_text = Column(Text, nullable=False)
    sentiment = Column(String(20))  # positive, neutral, negative, concerning
    category = Column(String(50))  # academic, behavioral, personal, attendance
    is_confidential = Column(Boolean, default=False)
    
    # For RAG: These will be embedded into vector database
    embedding_id = Column(String(100))  # Reference to vector DB
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    student = relationship('Student', back_populates='mentor_notes')

class BehavioralLog(Base):
    """Track behavioral patterns and engagement metrics"""
    __tablename__ = 'behavioral_logs'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    
    semester = Column(Integer)
    log_date = Column(Date, nullable=False)
    
    # Engagement metrics
    class_participation = Column(Integer)  # 1-5 scale
    assignment_submission_rate = Column(Float)
    library_visits = Column(Integer)
    lab_attendance = Column(Float)
    
    # Behavioral indicators
    discipline_issues = Column(Boolean, default=False)
    late_submissions = Column(Integer)
    missed_deadlines = Column(Integer)
    
    # Extracurricular
    club_participation = Column(Boolean, default=False)
    sports_participation = Column(Boolean, default=False)
    
    # Stress/wellbeing indicators
    stress_level = Column(Integer)  # 1-10 scale, from mentor observation
    peer_interaction = Column(String(20))  # good, average, poor, isolated
    
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship('Student', back_populates='behavioral_logs')

class Intervention(Base):
    """Track interventions and their outcomes"""
    __tablename__ = 'interventions'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    initiated_by = Column(Integer, ForeignKey('users.id'))
    
    intervention_type = Column(String(50))  # counseling, tutoring, academic_warning, parent_meeting
    description = Column(Text, nullable=False)
    recommended_by = Column(String(50))  # system, mentor, admin
    
    status = Column(String(20), default='planned')  # planned, ongoing, completed, cancelled
    priority_level = Column(String(20))  # low, medium, high, urgent
    
    scheduled_date = Column(Date)
    completed_date = Column(Date)
    
    outcome = Column(Text)
    effectiveness_rating = Column(Integer)  # 1-5 scale
    
    follow_up_required = Column(Boolean, default=False)
    follow_up_date = Column(Date)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    student = relationship('Student', back_populates='interventions')

class CareerAssessment(Base):
    """Career prediction and guidance"""
    __tablename__ = 'career_assessments'
    
    id = Column(Integer, primary_key=True)
    student_id = Column(Integer, ForeignKey('students.id'), nullable=False)
    
    assessment_date = Column(Date, nullable=False)
    semester = Column(Integer)
    
    # Academic strengths (from performance analysis)
    strong_subjects = Column(JSON)  # List of subject areas
    weak_subjects = Column(JSON)
    
    # Predicted career paths
    recommended_careers = Column(JSON)  # List with match scores
    industry_alignment = Column(JSON)  # Tech, finance, research, etc.
    
    # Skills assessment
    technical_skills = Column(JSON)
    soft_skills_score = Column(Float)
    
    # Placement readiness
    placement_readiness_score = Column(Float)  # 0-1
    recommended_improvements = Column(JSON)
    
    # Additional assessments
    aptitude_scores = Column(JSON)
    interest_areas = Column(JSON)
    
    confidence = Column(Float)
    explanation = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    student = relationship('Student', back_populates='career_assessments')

class AcademicQuery(Base):
    """Log of student/faculty queries for RAG system"""
    __tablename__ = 'academic_queries'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    student_id = Column(Integer, ForeignKey('students.id'))  # Subject of query
    
    query_text = Column(Text, nullable=False)
    query_language = Column(String(20))  # en, hi, regional
    intent = Column(String(50))  # risk_check, performance_analysis, advice, etc.
    
    # Agentic workflow
    agent_plan = Column(JSON)  # Steps the agent planned to execute
    data_retrieved = Column(JSON)  # What data was accessed
    
    response_text = Column(Text)
    response_language = Column(String(20))
    
    # Performance metrics
    query_timestamp = Column(DateTime, default=datetime.utcnow)
    response_time_ms = Column(Integer)
    tokens_used = Column(Integer)
    
    # Feedback
    user_rating = Column(Integer)  # 1-5
    was_helpful = Column(Boolean)
    
    student = relationship('Student', foreign_keys=[student_id])