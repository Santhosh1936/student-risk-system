"""
Enhanced Sample Data Generator
Creates comprehensive, realistic student data for testing the complete system
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.init_db import SessionLocal
from models.student import Student, Grade, Attendance, MentorNote, BehavioralLog
from datetime import datetime, timedelta
import random

def clear_existing_data(db):
    """Clear all existing data"""
    print("🗑️  Clearing existing data...")
    db.query(BehavioralLog).delete()
    db.query(MentorNote).delete()
    db.query(Attendance).delete()
    db.query(Grade).delete()
    db.query(Student).delete()
    db.commit()
    print("✅ Data cleared!")

def generate_students(db, count=20):
    """Generate sample students"""
    print(f"\n👥 Generating {count} students...")
    
    branches = ["CSE", "ECE", "ME", "CE", "EE"]
    first_names = ["Rahul", "Priya", "Amit", "Sneha", "Vikram", "Ananya", "Rohan", "Divya", 
                   "Arjun", "Meera", "Karan", "Pooja", "Aditya", "Riya", "Sanjay", 
                   "Nisha", "Varun", "Kavya", "Rajesh", "Swati"]
    last_names = ["Sharma", "Gupta", "Patel", "Singh", "Kumar", "Reddy", "Verma", "Joshi",
                  "Mehta", "Shah", "Rao", "Nair", "Kapoor", "Malhotra", "Agarwal"]
    
    students = []
    for i in range(count):
        name = f"{random.choice(first_names)} {random.choice(last_names)}"
        branch = random.choice(branches)
        batch = random.choice([2022, 2023, 2024])
        semester = 8 - (2026 - batch) * 2 if batch < 2026 else 2
        semester = max(1, min(8, semester))
        
        student = Student(
            roll_number=f"{batch}{branch}{i+1:03d}",
            name=name,
            email=f"{name.lower().replace(' ', '.')}@university.edu",
            branch=branch,
            batch=batch,
            current_semester=semester
        )
        
        db.add(student)
        students.append(student)
    
    db.commit()
    print(f"✅ Created {len(students)} students!")
    return students

def generate_grades(db, students):
    """Generate realistic grade data"""
    print("\n📚 Generating grade data...")
    
    subjects_by_semester = {
        1: [("CS101", "Programming Fundamentals", 4), ("MA101", "Calculus 1", 4), 
            ("PH101", "Physics", 3), ("EE101", "Circuits", 3)],
        2: [("CS102", "Data Structures", 4), ("MA102", "Linear Algebra", 4), 
            ("CH101", "Chemistry", 3), ("ME101", "Engineering Mechanics", 3)],
        3: [("CS201", "Algorithms", 4), ("CS202", "Database Systems", 3), 
            ("MA201", "Probability", 3), ("EC201", "Digital Logic", 3)],
        4: [("CS203", "Operating Systems", 4), ("CS204", "Computer Networks", 3), 
            ("CS205", "Software Engineering", 3), ("HU201", "Professional Ethics", 2)],
        5: [("CS301", "Machine Learning", 4), ("CS302", "Compiler Design", 3), 
            ("CS303", "Web Technologies", 3), ("MG301", "Economics", 2)],
        6: [("CS304", "AI", 4), ("CS305", "Cloud Computing", 3), 
            ("CS306", "Mobile Development", 3), ("CS307", "Cryptography", 3)],
        7: [("CS401", "Big Data", 3), ("CS402", "DevOps", 3), 
            ("CS403", "Cyber Security", 3), ("CS404", "IoT", 3)],
        8: [("CS405", "Project", 6), ("CS406", "Seminar", 2), 
            ("CS407", "Elective", 3)]
    }
    
    grade_count = 0
    
    for student in students:
        # Determine student profile (excellent, good, average, struggling)
        profile = random.choices(
            ["excellent", "good", "average", "struggling"], 
            weights=[0.15, 0.35, 0.35, 0.15]
        )[0]
        
        base_grade = {
            "excellent": 9.0,
            "good": 7.5,
            "average": 6.5,
            "struggling": 5.5
        }[profile]
        
        # Generate trend (improving, stable, declining)
        trend = random.choice(["improving", "stable", "declining"])
        
        for sem in range(1, student.current_semester + 1):
            if sem in subjects_by_semester:
                for subject_code, subject_name, credits in subjects_by_semester[sem]:
                    # Apply trend
                    if trend == "improving":
                        grade_adjustment = (sem - 1) * 0.2
                    elif trend == "declining":
                        grade_adjustment = -(sem - 1) * 0.2
                    else:
                        grade_adjustment = random.uniform(-0.2, 0.2)
                    
                    grade_point = base_grade + grade_adjustment + random.uniform(-0.5, 0.5)
                    grade_point = max(0, min(10, grade_point))
                    
                    grade = Grade(
                        student_id=student.id,
                        semester=sem,
                        subject_code=subject_code,
                        subject_name=subject_name,
                        grade_point=round(grade_point, 2),
                        credits=credits
                    )
                    
                    db.add(grade)
                    grade_count += 1
    
    db.commit()
    print(f"✅ Created {grade_count} grade records!")

def generate_attendance(db, students):
    """Generate attendance data"""
    print("\n📊 Generating attendance data...")
    
    attendance_count = 0
    
    for student in students:
        # Attendance profile correlates with academic performance
        attendance_base = random.uniform(70, 95)
        
        for sem in range(1, student.current_semester + 1):
            subjects = ["CS101", "CS102", "CS201", "CS202", "CS301"][:sem]
            
            for subject in subjects:
                total_classes = random.randint(40, 60)
                percentage = attendance_base + random.uniform(-10, 5)
                percentage = max(50, min(100, percentage))
                attended = int((percentage / 100) * total_classes)
                
                attendance = Attendance(
                    student_id=student.id,
                    semester=sem,
                    subject_code=subject,
                    month=f"2025-{(sem * 2) % 12 or 12:02d}",
                    total_classes=total_classes,
                    attended_classes=attended,
                    percentage=round(percentage, 2)
                )
                
                db.add(attendance)
                attendance_count += 1
    
    db.commit()
    print(f"✅ Created {attendance_count} attendance records!")

def generate_mentor_notes(db, students):
    """Generate realistic mentor notes"""
    print("\n📝 Generating mentor notes...")
    
    positive_notes = [
        "Great participation in class discussions. Shows genuine interest in the subject matter.",
        "Excellent problem-solving skills demonstrated during lab sessions.",
        "Very engaged and asks thoughtful questions. Natural leadership qualities.",
        "Consistent improvement in assignment quality. Keep up the good work!",
        "Active member of coding club. Regularly participates in hackathons.",
        "Strong analytical thinking. Helps peers understand difficult concepts.",
        "Exceptional project presentation. Clear communication skills.",
        "Passionate about learning new technologies outside curriculum.",
    ]
    
    concern_notes = [
        "Missing classes frequently. When contacted, cited family issues. Needs support.",
        "Appears disengaged during lectures. Sitting isolated in back. May need re-engagement.",
        "Submitting assignments late consistently. Time management concerns noted.",
        "Low participation in class activities. Seems anxious when called upon.",
        "Performance declining over past two semesters. Recommended counseling.",
        "Multiple absences without prior notice. Parent meeting scheduled.",
        "Struggling with programming concepts. Suggested peer tutoring.",
        "Appears stressed and overwhelmed. Discussed workload management strategies.",
        "Social withdrawal observed. Not participating in group activities anymore.",
        "Health concerns affecting attendance. Medical leave documentation provided.",
    ]
    
    neutral_notes = [
        "Regular attendance and submission of assignments on time.",
        "Participates when prompted. Could be more proactive.",
        "Steady performance across subjects. No major concerns.",
        "Attends office hours occasionally for clarifications.",
        "Completed semester requirements satisfactorily.",
        "Active in sports activities. Balancing academics and extracurriculars.",
    ]
    
    note_count = 0
    
    for student in students:
        # Generate 2-5 notes per student
        num_notes = random.randint(2, 5)
        
        for _ in range(num_notes):
            # Determine sentiment based on student performance
            sentiment_choice = random.choices(
                ["positive", "neutral", "negative"],
                weights=[0.4, 0.4, 0.2]
            )[0]
            
            if sentiment_choice == "positive":
                note_text = random.choice(positive_notes)
            elif sentiment_choice == "negative":
                note_text = random.choice(concern_notes)
            else:
                note_text = random.choice(neutral_notes)
            
            days_ago = random.randint(1, 180)
            created_date = datetime.now() - timedelta(days=days_ago)
            
            note = MentorNote(
                student_id=student.id,
                mentor_id=None,
                note_text=note_text,
                created_at=created_date,
                sentiment=sentiment_choice
            )
            
            db.add(note)
            note_count += 1
    
    db.commit()
    print(f"✅ Created {note_count} mentor notes!")

def generate_behavioral_logs(db, students):
    """Generate behavioral observation logs"""
    print("\n🎯 Generating behavioral logs...")
    
    log_count = 0
    
    behavior_notes = {
        "high_engagement": [
            "Very active in class, asks relevant questions regularly",
            "Participates enthusiastically in group discussions",
            "Helps other students understand concepts",
            "Takes initiative in team projects"
        ],
        "moderate_engagement": [
            "Attends classes but quiet during discussions",
            "Completes work but minimal participation",
            "Responds when asked but doesn't volunteer",
            "Average interaction with peers"
        ],
        "low_engagement": [
            "Rarely participates, sits quietly in back",
            "Appears distracted during lectures",
            "Minimal interaction with classmates",
            "Often looking at phone during class"
        ]
    }
    
    for student in students:
        # Generate 3-8 logs per student over time
        num_logs = random.randint(3, 8)
        
        base_engagement = random.uniform(4, 9)
        base_stress = random.uniform(3, 7)
        
        for i in range(num_logs):
            days_ago = random.randint(1, 150)
            log_date = datetime.now() - timedelta(days=days_ago)
            
            # Add some variation over time
            engagement = base_engagement + random.uniform(-1.5, 1.5)
            engagement = max(1, min(10, engagement))
            
            stress = base_stress + random.uniform(-2, 2)
            stress = max(1, min(10, stress))
            
            # Determine note based on engagement level
            if engagement >= 7:
                note = random.choice(behavior_notes["high_engagement"])
            elif engagement >= 5:
                note = random.choice(behavior_notes["moderate_engagement"])
            else:
                note = random.choice(behavior_notes["low_engagement"])
            
            log = BehavioralLog(
                student_id=student.id,
                log_date=log_date,
                engagement_level=round(engagement, 1),
                stress_level=round(stress, 1),
                notes=note
            )
            
            db.add(log)
            log_count += 1
    
    db.commit()
    print(f"✅ Created {log_count} behavioral logs!")

def generate_complete_dataset():
    """Generate complete sample dataset"""
    print("="*60)
    print("🚀 ENHANCED SAMPLE DATA GENERATOR")
    print("="*60)
    
    db = SessionLocal()
    
    try:
        # Clear existing data
        clear_existing_data(db)
        
        # Generate students
        students = generate_students(db, count=20)
        
        # Generate academic data
        generate_grades(db, students)
        generate_attendance(db, students)
        
        # Generate qualitative data
        generate_mentor_notes(db, students)
        generate_behavioral_logs(db, students)
        
        print("\n" + "="*60)
        print("✅ SAMPLE DATA GENERATION COMPLETE!")
        print("="*60)
        print(f"\n📊 Summary:")
        print(f"   - Students: {len(students)}")
        print(f"   - Grades: {db.query(Grade).count()}")
        print(f"   - Attendance Records: {db.query(Attendance).count()}")
        print(f"   - Mentor Notes: {db.query(MentorNote).count()}")
        print(f"   - Behavioral Logs: {db.query(BehavioralLog).count()}")
        print(f"\n🎉 Ready for testing!")
        print("="*60)
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_complete_dataset()
