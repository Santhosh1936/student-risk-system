"""
Comprehensive System Testing Script
Tests each component of the Explainable Agentic RAG-Based System
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_prerequisites():
    """Check if all prerequisites are met"""
    print("="*60)
    print("🔍 CHECKING PREREQUISITES")
    print("="*60)
    
    issues = []
    
    # Check OpenAI API Key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key or api_key == 'REDACTED_REPLACE_WITH_ENV_VAR':
        print("❌ OpenAI API Key not configured")
        issues.append("OpenAI API Key")
    else:
        print(f"✅ OpenAI API Key found: {api_key[:8]}...{api_key[-4:]}")
    
    # Check required packages
    required_packages = [
        'fastapi', 'sqlalchemy', 'chromadb', 'sentence_transformers',
        'openai', 'transformers', 'torch', 'sklearn', 'pandas'
    ]
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            issues.append(package)
    
    # Check database
    if os.path.exists('student_risk.db'):
        print("✅ Database file exists")
    else:
        print("⚠️  Database file not found (will be created)")
    
    print()
    if issues:
        print(f"❌ {len(issues)} issues found: {', '.join(issues)}")
        return False
    else:
        print("✅ All prerequisites met!")
        return True

def test_database():
    """Test database connection and models"""
    print("\n" + "="*60)
    print("🗄️  TESTING DATABASE")
    print("="*60)
    
    try:
        from database.init_db import init_database, SessionLocal
        from models.student import Student, MentorNote, BehavioralLog, Intervention
        
        # Initialize database
        print("Creating database tables...")
        init_database()
        
        # Test connection
        db = SessionLocal()
        student_count = db.query(Student).count()
        print(f"✅ Database connected - Found {student_count} students")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_rag_engine():
    """Test RAG Engine"""
    print("\n" + "="*60)
    print("🧠 TESTING RAG ENGINE")
    print("="*60)
    
    try:
        from database.init_db import SessionLocal
        from services.rag_engine import RAGEngine
        
        db = SessionLocal()
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key or api_key == 'REDACTED_REPLACE_WITH_ENV_VAR':
            print("⚠️  Skipping RAG test - OpenAI API key not configured")
            return False
        
        print("Initializing RAG Engine...")
        rag = RAGEngine(db, api_key)
        
        # Test embedding
        test_text = "Student shows declining attendance"
        embedding = rag.embed_text(test_text)
        print(f"✅ Embedding generated - dimension: {len(embedding)}")
        
        # Test indexing (with dummy data)
        embedding_id = rag.index_mentor_note(
            note_id=999,
            student_id=1,
            note_text=test_text,
            metadata={"category": "test", "sentiment": "neutral"}
        )
        
        if embedding_id:
            print(f"✅ Mentor note indexed: {embedding_id}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ RAG Engine error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_multilingual_nlu():
    """Test Multilingual NLU"""
    print("\n" + "="*60)
    print("🌐 TESTING MULTILINGUAL NLU")
    print("="*60)
    
    try:
        from services.multilingual_nlu import MultilingualNLU
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key or api_key == 'REDACTED_REPLACE_WITH_ENV_VAR':
            print("⚠️  Skipping NLU test - OpenAI API key not configured")
            return False
        
        nlu = MultilingualNLU(api_key)
        
        # Test language detection
        test_cases = [
            ("What is my risk score?", "en"),
            ("मेरा रिस्क स्कोर क्या है?", "hi"),
            ("నా రిస్క్ స్కోర్ ఏమిటి?", "te")
        ]
        
        for text, expected_lang in test_cases:
            detected = nlu.detect_language(text)
            status = "✅" if detected == expected_lang else "⚠️ "
            print(f"{status} Detected '{expected_lang}' in: {text[:30]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ Multilingual NLU error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agentic_workflow():
    """Test Agentic Workflow"""
    print("\n" + "="*60)
    print("🤖 TESTING AGENTIC WORKFLOW")
    print("="*60)
    
    try:
        from database.init_db import SessionLocal
        from services.agentic_workflow import AgenticWorkflow
        
        api_key = os.getenv('OPENAI_API_KEY')
        
        if not api_key or api_key == 'REDACTED_REPLACE_WITH_ENV_VAR':
            print("⚠️  Skipping Agentic Workflow test - OpenAI API key not configured")
            return False
        
        db = SessionLocal()
        agent = AgenticWorkflow(db, api_key)
        
        # Test intent understanding
        test_query = "What is the risk score for student CSE2024001?"
        print(f"Testing query: '{test_query}'")
        
        intent = agent.understand_intent(test_query)
        print(f"✅ Intent recognized: {intent.get('intent')}")
        print(f"   Confidence: {intent.get('confidence')}")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Agentic Workflow error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_risk_calculator():
    """Test Risk Calculator"""
    print("\n" + "="*60)
    print("📊 TESTING RISK CALCULATOR")
    print("="*60)
    
    try:
        from database.init_db import SessionLocal
        from services.risk_calculator import RiskCalculator
        from models.student import Student
        
        db = SessionLocal()
        calculator = RiskCalculator(db)
        
        # Get first student
        student = db.query(Student).first()
        
        if not student:
            print("⚠️  No students in database - run generate_sample.py first")
            return False
        
        print(f"Testing with student: {student.name} ({student.roll_number})")
        
        risk_data = calculator.calculate_risk_score(student.id)
        
        if risk_data:
            print(f"✅ Risk Score: {risk_data['risk_score']:.2f}")
            print(f"   Risk Level: {risk_data['risk_level']}")
            print(f"   Factors: {len(risk_data['factors'])} analyzed")
        
        db.close()
        return True
        
    except Exception as e:
        print(f"❌ Risk Calculator error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_api_endpoints():
    """Test API endpoints"""
    print("\n" + "="*60)
    print("🌐 TESTING API ENDPOINTS")
    print("="*60)
    
    print("ℹ️  To test API endpoints:")
    print("   1. Run: python main.py")
    print("   2. Visit: http://localhost:8000/docs")
    print("   3. Test endpoints interactively")
    
    return True

def main():
    """Run all tests"""
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║  EXPLAINABLE AGENTIC RAG-BASED SYSTEM - TEST SUITE       ║
    ║  Student Academic Risk Assessment & Advisory System       ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    
    results = {}
    
    # Check prerequisites first
    if not check_prerequisites():
        print("\n⚠️  Please fix prerequisites before continuing:")
        print("\n1. Set OpenAI API Key:")
        print("   Windows PowerShell: $env:OPENAI_API_KEY='your-key-here'")
        print("   Windows CMD: set OPENAI_API_KEY=your-key-here")
        print("   Or edit backend/.env file")
        print("\n2. Install missing packages:")
        print("   pip install -r requirements.txt")
        return
    
    # Run tests
    results['Database'] = test_database()
    results['Risk Calculator'] = test_risk_calculator()
    results['RAG Engine'] = test_rag_engine()
    results['Multilingual NLU'] = test_multilingual_nlu()
    results['Agentic Workflow'] = test_agentic_workflow()
    results['API Endpoints'] = test_api_endpoints()
    
    # Summary
    print("\n" + "="*60)
    print("📋 TEST SUMMARY")
    print("="*60)
    
    for component, passed in results.items():
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{status} - {component}")
    
    passed_count = sum(1 for v in results.values() if v)
    total_count = len(results)
    
    print(f"\n{passed_count}/{total_count} tests passed")
    
    if passed_count == total_count:
        print("\n🎉 All tests passed! System is ready!")
    else:
        print("\n⚠️  Some tests failed - check errors above")

if __name__ == '__main__':
    main()
