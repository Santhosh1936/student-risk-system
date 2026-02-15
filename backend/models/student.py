from sqlalchemy import Column, Integer, String, Float, Date, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

Base = declarative_base()

class Student(Base):
    __tablename__ = 'students'
    
    id = Column(Integer, primary_key=True)
    roll_number = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), nullable=False)
    email = Column(String(100), unique=True)
    branch = Column(String(50))
    batch = Column(String(10))
    current_semester = Column(Integer)
    
    grades = relationship('Grade', back_populates='student')
    attendance = relationship('Attendance', back_populates='student')
    risk_scores = relationship('RiskScore', back_populates='student')

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
    risk_score = Column(Float)
    risk_level = Column(String(20))
    confidence = Column(Float)
    factors = Column(JSON)
    generated_at = Column(Date)
    
    student = relationship('Student', back_populates='risk_scores')