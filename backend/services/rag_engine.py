"""
RAG Engine - Retrieval-Augmented Generation System
Combines vector database retrieval with LLM generation for context-aware responses
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from openai import OpenAI
from sqlalchemy.orm import Session
from models.student import Student, MentorNote, BehavioralLog, Grade, Attendance
import json
from datetime import datetime

class RAGEngine:
    """
    Retrieval-Augmented Generation Engine for Student Analytics
    Combines structured data with unstructured mentor notes using vector similarity
    """
    
    def __init__(self, db: Session, openai_api_key: str):
        self.db = db
        self.openai_client = OpenAI(api_key=openai_api_key)
        
        # Initialize embedding model (local)
        print("🔄 Loading embedding model...")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize ChromaDB
        print("🔄 Initializing vector database...")
        self.chroma_client = chromadb.Client(Settings(
            chroma_db_impl="duckdb+parquet",
            persist_directory="./chroma_db"
        ))
        
        # Collections for different data types
        try:
            self.mentor_notes_collection = self.chroma_client.get_or_create_collection(
                name="mentor_notes",
                metadata={"description": "Mentor observations and notes about students"}
            )
            
            self.academic_knowledge_collection = self.chroma_client.get_or_create_collection(
                name="academic_knowledge",
                metadata={"description": "General academic guidance and best practices"}
            )
        except Exception as e:
            print(f"⚠️  Warning: ChromaDB initialization: {e}")
        
        print("✅ RAG Engine initialized!")
    
    def embed_text(self, text: str) -> List[float]:
        """Generate embedding vector for text"""
        embedding = self.embedding_model.encode(text)
        return embedding.tolist()
    
    def index_mentor_note(self, note_id: int, student_id: int, note_text: str, metadata: Dict):
        """Add mentor note to vector database"""
        try:
            embedding = self.embed_text(note_text)
            
            self.mentor_notes_collection.add(
                embeddings=[embedding],
                documents=[note_text],
                ids=[f"note_{note_id}"],
                metadatas=[{
                    "student_id": student_id,
                    "note_id": note_id,
                    **metadata
                }]
            )
            
            return f"note_{note_id}"
        except Exception as e:
            print(f"Error indexing mentor note: {e}")
            return None
    
    def retrieve_relevant_notes(self, query: str, student_id: Optional[int] = None, top_k: int = 5) -> List[Dict]:
        """Retrieve relevant mentor notes for a query"""
        try:
            query_embedding = self.embed_text(query)
            
            # Build filter
            where_filter = {"student_id": student_id} if student_id else None
            
            results = self.mentor_notes_collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter
            )
            
            # Format results
            retrieved_notes = []
            if results['documents'] and len(results['documents']) > 0:
                for i, doc in enumerate(results['documents'][0]):
                    retrieved_notes.append({
                        "text": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else None
                    })
            
            return retrieved_notes
        except Exception as e:
            print(f"Error retrieving notes: {e}")
            return []
    
    def get_student_context(self, student_id: int) -> Dict[str, Any]:
        """Gather comprehensive context about a student"""
        
        student = self.db.query(Student).filter(Student.id == student_id).first()
        if not student:
            return {}
        
        # Get grades
        grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
        
        # Calculate CGPA
        if grades:
            total_points = sum(g.grade_point * g.credits for g in grades)
            total_credits = sum(g.credits for g in grades)
            cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
        else:
            cgpa = 0.0
        
        # Get attendance
        attendance_records = self.db.query(Attendance).filter(
            Attendance.student_id == student_id
        ).all()
        avg_attendance = (
            sum(a.percentage for a in attendance_records) / len(attendance_records)
            if attendance_records else 0.0
        )
        
        # Get recent behavioral logs
        behavioral_logs = self.db.query(BehavioralLog).filter(
            BehavioralLog.student_id == student_id
        ).order_by(BehavioralLog.log_date.desc()).limit(5).all()
        
        context = {
            "student_info": {
                "id": student.id,
                "name": student.name,
                "roll_number": student.roll_number,
                "branch": student.branch,
                "semester": student.current_semester,
                "batch": student.batch
            },
            "academic_performance": {
                "cgpa": cgpa,
                "total_credits": sum(g.credits for g in grades),
                "grades_count": len(grades)
            },
            "attendance": {
                "average": round(avg_attendance, 2),
                "records_count": len(attendance_records)
            },
            "behavioral_summary": {
                "recent_logs": len(behavioral_logs),
                "avg_stress_level": (
                    sum(b.stress_level for b in behavioral_logs if b.stress_level) / 
                    len([b for b in behavioral_logs if b.stress_level])
                ) if any(b.stress_level for b in behavioral_logs) else None
            }
        }
        
        return context
    
    def generate_response(
        self,
        query: str,
        student_id: Optional[int] = None,
        include_context: bool = True,
        language: str = "en"
    ) -> Dict[str, Any]:
        """
        Generate RAG-enhanced response to a query
        """
        
        # Step 1: Retrieve relevant context
        retrieved_notes = []
        student_context = {}
        
        if student_id and include_context:
            # Get structured student data
            student_context = self.get_student_context(student_id)
            
            # Retrieve relevant mentor notes
            retrieved_notes = self.retrieve_relevant_notes(query, student_id, top_k=3)
        
        # Step 2: Build context-aware prompt
        system_prompt = """You are an expert academic advisor AI assistant for a student risk assessment system.
Your role is to provide clear, evidence-based, and empathetic guidance to students and faculty.

Key principles:
- Be transparent about reasoning
- Support claims with specific data
- Never make deterministic predictions (avoid "will fail")
- Focus on growth and improvement opportunities
- Maintain encouraging and supportive tone
- Respect student privacy and agency
"""
        
        # Build context section
        context_parts = []
        
        if student_context:
            context_parts.append("=== Student Data ===")
            context_parts.append(json.dumps(student_context, indent=2))
        
        if retrieved_notes:
            context_parts.append("\n=== Relevant Mentor Notes ===")
            for i, note in enumerate(retrieved_notes, 1):
                context_parts.append(f"\nNote {i}: {note['text']}")
        
        context_text = "\n".join(context_parts) if context_parts else "No specific student context available."
        
        user_prompt = f"""Context:
{context_text}

Query: {query}

Please provide a comprehensive, evidence-based response that:
1. Directly addresses the query
2. References specific data from the context
3. Explains reasoning clearly
4. Provides actionable recommendations if applicable
5. Maintains a supportive, growth-oriented tone
"""
        
        # Add language instruction if not English
        if language != "en":
            if language == "hi":
                user_prompt += "\n\nPlease provide the response in Hindi (Devanagari script)."
            else:
                user_prompt += f"\n\nPlease provide the response in {language} language."
        
        # Step 3: Generate response with GPT
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=1000
            )
            
            response_text = completion.choices[0].message.content
            tokens_used = completion.usage.total_tokens
            
            return {
                "success": True,
                "response": response_text,
                "context_used": {
                    "student_context": bool(student_context),
                    "mentor_notes_count": len(retrieved_notes),
                    "retrieved_notes": retrieved_notes
                },
                "tokens_used": tokens_used,
                "language": language
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "response": "I apologize, but I encountered an error generating the response."
            }
    
    def index_knowledge_base(self):
        """
        Index static academic knowledge for RAG
        This can include best practices, intervention strategies, etc.
        """
        
        knowledge_items = [
            {
                "id": "kb_001",
                "text": "Students with CGPA below 6.0 should receive academic counseling and tutoring support. Early intervention in the first two semesters is most effective.",
                "category": "intervention"
            },
            {
                "id": "kb_002",
                "text": "Attendance below 75% correlates with 45% higher risk of academic failure. Immediate parent notification and mandatory counseling recommended.",
                "category": "attendance"
            },
            {
                "id": "kb_003",
                "text": "Declining GPA trend over 2 consecutive semesters requires personalized study plan and weekly mentor check-ins.",
                "category": "performance"
            },
            {
                "id": "kb_004",
                "text": "High stress levels combined with low peer interaction indicate need for mental health support and peer mentoring programs.",
                "category": "wellbeing"
            },
            {
                "id": "kb_005",
                "text": "Students showing disengagement (low class participation, missed deadlines) benefit from reengagement workshops and career counseling.",
                "category": "engagement"
            }
        ]
        
        try:
            for item in knowledge_items:
                embedding = self.embed_text(item["text"])
                
                self.academic_knowledge_collection.add(
                    embeddings=[embedding],
                    documents=[item["text"]],
                    ids=[item["id"]],
                    metadatas=[{"category": item["category"]}]
                )
            
            print(f"✅ Indexed {len(knowledge_items)} knowledge base items")
            return True
            
        except Exception as e:
            print(f"Error indexing knowledge base: {e}")
            return False


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from database.init_db import SessionLocal
    
    load_dotenv()
    
    db = SessionLocal()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        rag = RAGEngine(db, api_key)
        rag.index_knowledge_base()
        
        # Test query
        response = rag.generate_response(
            "What are the key risk factors for academic failure?",
            student_id=None,
            include_context=False
        )
        
        print("\n" + "="*50)
        print("Test Response:")
        print("="*50)
        print(response['response'])
    else:
        print("❌ OPENAI_API_KEY not found!")
    
    db.close()
