import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy.orm import Session
from database.init_db import SessionLocal, engine
from models.student import Student, Grade, Attendance, Base
import random
from datetime import date

def generate_sample_data():
    """Generate 50 sample students with realistic data"""
    
    # Ensure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    # Check if data already exists
    existing = db.query(Student).count()
    if existing > 0:
        print(f"⚠️  Database already has {existing} students. Skipping data generation.")
        print("   Delete student_risk.db if you want to regenerate data.")
        db.close()
        return
    
    branches = ['Computer Science', 'Mechanical', 'Electrical', 'Civil']
    
    subjects = [
        ('CS101', 'Programming', 4),
        ('CS102', 'Data Structures', 4),
        ('CS201', 'Algorithms', 4),
        ('CS202', 'Database Systems', 3),
        ('MA101', 'Calculus', 4),
        ('PH101', 'Physics', 3)
    ]
    
    print("🔄 Generating 50 sample students...")
    
    # Generate 50 students
    for i in range(1, 51):
        student = Student(
            roll_number=f'2021BTCS{i:03d}',
            name=f'Student {i}',
            email=f'student{i}@university.edu',
            branch=random.choice(branches),
            batch='2021',
            current_semester=6
        )
        db.add(student)
        db.flush()
        
        # Generate grades for 6 semesters
        for sem in range(1, 7):
            for subj_code, subj_name, credits in subjects:
                # Last 10 students have lower grades (at-risk)
                if i > 40:
                    grade_point = random.uniform(4.0, 7.0)
                else:
                    grade_point = random.uniform(6.0, 10.0)
                
                grade = Grade(
                    student_id=student.id,
                    semester=sem,
                    subject_code=subj_code,
                    subject_name=subj_name,
                    grade_point=round(grade_point, 2),
                    credits=credits
                )
                db.add(grade)
                
                # Generate attendance
                total = random.randint(40, 50)
                if i > 40:  # At-risk students have lower attendance
                    attended = random.randint(int(total * 0.5), int(total * 0.75))
                else:
                    attended = random.randint(int(total * 0.75), total)
                
                attendance = Attendance(
                    student_id=student.id,
                    semester=sem,
                    subject_code=subj_code,
                    total_classes=total,
                    attended_classes=attended,
                    percentage=round((attended/total)*100, 2)
                )
                db.add(attendance)
    
    db.commit()
    print("✅ Successfully generated 50 students!")
    print("   - 40 students with good performance")
    print("   - 10 students with at-risk indicators")
    print("   - 6 semesters of data per student")
    print("   - 6 subjects per semester")
    db.close()

if __name__ == '__main__':
    generate_sample_data()