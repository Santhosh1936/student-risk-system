"""
Agentic AI Workflow Engine
Autonomous planning and execution of analytical tasks
Mimics how a human academic counselor thinks and acts
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from openai import OpenAI
import json
from datetime import datetime

from models.student import Student, Grade, Attendance, RiskScore
from services.rag_engine import RAGEngine
from services.risk_calculator import RiskCalculator
from services.explainability_engine import ExplainabilityEngine
from services.career_predictor import CareerPredictor
from services.stress_detector import StressDetector


class AgenticWorkflow:
    """
    Intelligent workflow planner that autonomously decides:
    - What data to retrieve
    - What analysis to perform
    - How to explain findings
    - What interventions to recommend
    """
    
    def __init__(self, db: Session, openai_api_key: str):
        self.db = db
        self.openai_client = OpenAI(api_key=openai_api_key)
        self.rag_engine = RAGEngine(db, openai_api_key)
        self.risk_calculator = RiskCalculator(db)
        self.explainability_engine = ExplainabilityEngine(db)
        self.career_predictor = CareerPredictor(db)
        self.stress_detector = StressDetector(db)
    
    def understand_intent(self, query: str) -> Dict[str, Any]:
        """
        Use LLM to understand user intent and extract structured information
        """
        
        system_prompt = """You are an intent classification system for an academic advisory AI.
Analyze the user query and extract:
1. Primary intent (risk_assessment, performance_analysis, career_guidance, intervention_planning, general_query)
2. Student identifier (if mentioned - roll number, name, ID)
3. Time scope (current, historical, predictive)
4. Specific concerns (attendance, grades, behavior, stress, etc.)
5. Language of query (en, hi, or other)

Respond ONLY with valid JSON."""
        
        user_prompt = f"""Query: "{query}"

Analyze and respond with JSON in this exact format:
{{
    "intent": "one of: risk_assessment, performance_analysis, career_guidance, intervention_planning, general_query",
    "student_identifier": "extracted roll number, name, or ID, or null",
    "time_scope": "current, historical, or predictive",
    "concerns": ["list", "of", "specific", "concerns"],
    "language": "en, hi, or other",
    "confidence": 0.0-1.0
}}"""
        
        try:
            completion = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            intent_data = json.loads(completion.choices[0].message.content)
            return intent_data
            
        except Exception as e:
            print(f"Error understanding intent: {e}")
            return {
                "intent": "general_query",
                "student_identifier": None,
                "time_scope": "current",
                "concerns": [],
                "language": "en",
                "confidence": 0.5
            }
    
    def plan_workflow(self, intent_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Autonomously plan the steps needed to answer the query
        Returns a list of tasks to execute
        """
        
        intent = intent_data.get("intent", "general_query")
        concerns = intent_data.get("concerns", [])
        
        workflow_plan = []
        
        # Task 1: Always identify student if mentioned
        if intent_data.get("student_identifier"):
            workflow_plan.append({
                "task": "identify_student",
                "params": {"identifier": intent_data["student_identifier"]}
            })
        
        # Task 2: Retrieve relevant data based on intent
        if intent == "risk_assessment":
            workflow_plan.extend([
                {"task": "fetch_academic_data", "params": {}},
                {"task": "fetch_attendance_data", "params": {}},
                {"task": "fetch_behavioral_logs", "params": {}},
                {"task": "calculate_risk_score", "params": {}},
                {"task": "generate_risk_explanation", "params": {}},  # NEW: Explainability
                {"task": "analyze_wellbeing", "params": {}},  # NEW: Stress detection
                {"task": "retrieve_similar_cases", "params": {"concern": "high_risk"}}
            ])
        
        elif intent == "performance_analysis":
            workflow_plan.extend([
                {"task": "fetch_academic_data", "params": {}},
                {"task": "analyze_gpa_trend", "params": {}},
                {"task": "identify_weak_subjects", "params": {}},
                {"task": "retrieve_mentor_notes", "params": {"category": "academic"}}
            ])
        
        elif intent == "career_guidance":
            workflow_plan.extend([
                {"task": "fetch_academic_data", "params": {}},
                {"task": "identify_strong_subjects", "params": {}},
                {"task": "predict_career_paths", "params": {}},  # Integrated
                {"task": "retrieve_career_knowledge", "params": {}}
            ])
        
        elif intent == "intervention_planning":
            workflow_plan.extend([
                {"task": "calculate_risk_score", "params": {}},
                {"task": "retrieve_past_interventions", "params": {}},
                {"task": "retrieve_best_practices", "params": {}},
                {"task": "generate_intervention_plan", "params": {}}
            ])
        
        # Add concern-specific tasks
        if "attendance" in concerns:
            workflow_plan.append({"task": "fetch_attendance_data", "params": {}})
        
        if "stress" in concerns or "wellbeing" in concerns:
            workflow_plan.append({"task": "fetch_behavioral_logs", "params": {"focus": "stress"}})
        
        # Final task: Generate explanation
        workflow_plan.append({
            "task": "generate_explanation",
            "params": {"language": intent_data.get("language", "en")}
        })
        
        return workflow_plan
    
    def execute_task(self, task: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single task in the workflow
        """
        
        task_name = task["task"]
        params = task.get("params", {})
        student_id = context.get("student_id")
        
        result = {}
        
        try:
            if task_name == "identify_student":
                # Find student by identifier
                identifier = params["identifier"]
                student = (
                    self.db.query(Student)
                    .filter(
                        (Student.roll_number == identifier) |
                        (Student.name.ilike(f"%{identifier}%"))
                    )
                    .first()
                )
                
                if student:
                    result = {
                        "success": True,
                        "student_id": student.id,
                        "student_name": student.name,
                        "roll_number": student.roll_number
                    }
                    context["student_id"] = student.id
                else:
                    result = {"success": False, "error": "Student not found"}
            
            elif task_name == "fetch_academic_data":
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                grades = self.db.query(Grade).filter(Grade.student_id == student_id).all()
                
                # Calculate CGPA
                if grades:
                    total_points = sum(g.grade_point * g.credits for g in grades)
                    total_credits = sum(g.credits for g in grades)
                    cgpa = round(total_points / total_credits, 2) if total_credits > 0 else 0.0
                else:
                    cgpa = 0.0
                
                result = {
                    "success": True,
                    "cgpa": cgpa,
                    "total_subjects": len(grades),
                    "grades": [
                        {
                            "semester": g.semester,
                            "subject": g.subject_name,
                            "grade": g.grade_point
                        }
                        for g in grades
                    ]
                }
                context["academic_data"] = result
            
            elif task_name == "fetch_attendance_data":
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                attendance = self.db.query(Attendance).filter(
                    Attendance.student_id == student_id
                ).all()
                
                avg_attendance = (
                    sum(a.percentage for a in attendance) / len(attendance)
                    if attendance else 0.0
                )
                
                result = {
                    "success": True,
                    "average_attendance": round(avg_attendance, 2),
                    "below_threshold": avg_attendance < 75,
                    "records": [
                        {
                            "semester": a.semester,
                            "subject": a.subject_code,
                            "percentage": a.percentage
                        }
                        for a in attendance
                    ]
                }
                context["attendance_data"] = result
            
            elif task_name == "fetch_behavioral_logs":
                # Fetch behavioral and stress logs
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                from models.student import BehavioralLog
                logs = self.db.query(BehavioralLog).filter(
                    BehavioralLog.student_id == student_id
                ).order_by(BehavioralLog.log_date.desc()).limit(10).all()
                
                result = {
                    "success": True,
                    "logs_count": len(logs),
                    "logs": [
                        {
                            "date": log.log_date.isoformat(),
                            "engagement": log.engagement_level,
                            "stress": log.stress_level,
                            "notes": log.notes
                        }
                        for log in logs
                    ]
                }
                context["behavioral_logs"] = result
            
            elif task_name == "identify_strong_subjects":
                # Identify subjects where student excels
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                grades = self.db.query(Grade).filter(
                    Grade.student_id == student_id,
                    Grade.grade_point >= 8.0
                ).all()
                
                result = {
                    "success": True,
                    "strong_subjects": [
                        {
                            "subject": g.subject_name,
                            "code": g.subject_code,
                            "grade": g.grade_point
                        }
                        for g in grades
                    ]
                }
                context["strong_subjects"] = result
            
            elif task_name == "calculate_risk_score":
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                risk_data = self.risk_calculator.calculate_risk_score(student_id)
                
                if risk_data:
                    result = {"success": True, **risk_data}
                    context["risk_score"] = risk_data
                else:
                    result = {"success": False, "error": "Could not calculate risk"}
            
            elif task_name == "generate_risk_explanation":
                # NEW: Generate explainable risk assessment
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                risk_data = context.get("risk_score")
                if not risk_data:
                    # Calculate if not already done
                    risk_data = self.risk_calculator.calculate_risk_score(student_id)
                
                explanation = self.explainability_engine.explain_risk_score(student_id, risk_data)
                
                result = {
                    "success": True,
                    "explanation": explanation
                }
                context["risk_explanation"] = explanation
            
            elif task_name == "analyze_wellbeing":
                # NEW: Analyze stress and wellbeing
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                wellbeing_analysis = self.stress_detector.analyze_student_wellbeing(student_id)
                
                result = {
                    "success": True,
                    "wellbeing": wellbeing_analysis
                }
                context["wellbeing_analysis"] = wellbeing_analysis
            
            elif task_name == "predict_career_paths":
                # NEW: Career prediction
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                career_predictions = self.career_predictor.predict_career_paths(student_id, top_n=5)
                
                result = {
                    "success": True,
                    "careers": career_predictions
                }
                context["career_predictions"] = career_predictions
            
            elif task_name == "retrieve_career_knowledge":
                # Retrieve career guidance from RAG knowledge base
                knowledge = self.rag_engine.retrieve_relevant_notes(
                    query="career guidance best practices",
                    student_id=None,
                    top_k=3
                )
                
                result = {
                    "success": True,
                    "knowledge": knowledge
                }
                context["career_knowledge"] = knowledge
            
            elif task_name == "retrieve_similar_cases":
                # Retrieve similar student cases from RAG
                concern = params.get("concern", "general")
                notes = self.rag_engine.retrieve_relevant_notes(
                    query=f"similar cases {concern}",
                    student_id=None,
                    top_k=5
                )
                
                result = {
                    "success": True,
                    "similar_cases": notes
                }
                context["similar_cases"] = notes
            
            elif task_name == "retrieve_best_practices":
                # Retrieve intervention best practices
                practices = self.rag_engine.retrieve_relevant_notes(
                    query="intervention strategies academic support",
                    student_id=None,
                    top_k=5
                )
                
                result = {
                    "success": True,
                    "best_practices": practices
                }
                context["best_practices"] = practices
            
            elif task_name == "retrieve_past_interventions":
                # Retrieve past intervention records
                from models.student import InterventionHistory
                if student_id:
                    interventions = self.db.query(InterventionHistory).filter(
                        InterventionHistory.student_id == student_id
                    ).order_by(InterventionHistory.intervention_date.desc()).limit(5).all()
                    
                    result = {
                        "success": True,
                        "interventions": [
                            {
                                "date": i.intervention_date.isoformat(),
                                "type": i.intervention_type,
                                "outcome": i.outcome_status
                            }
                            for i in interventions
                        ]
                    }
                else:
                    result = {"success": False, "error": "No student ID"}
                
                context["past_interventions"] = result
            
            elif task_name == "generate_intervention_plan":
                # Generate personalized intervention plan using RAG
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                # Gather context
                risk_data = context.get("risk_score", {})
                best_practices = context.get("best_practices", [])
                
                query = f"""Generate a personalized intervention plan for a student with:
                - Risk Score: {risk_data.get('risk_score', 'unknown')}
                - Key Factors: {risk_data.get('factors', {})}
                
                Consider best practices and create actionable steps."""
                
                plan = self.rag_engine.generate_response(
                    query=query,
                    student_id=student_id,
                    include_context=True
                )
                
                result = {
                    "success": True,
                    "intervention_plan": plan
                }
                context["intervention_plan"] = plan
            
            elif task_name == "retrieve_mentor_notes":
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                # Use RAG to retrieve relevant notes
                notes = self.rag_engine.retrieve_relevant_notes(
                    query="academic performance concerns",
                    student_id=student_id,
                    top_k=3
                )
                
                result = {
                    "success": True,
                    "notes_count": len(notes),
                    "notes": notes
                }
                context["mentor_notes"] = notes
            
            elif task_name == "analyze_gpa_trend":
                if not student_id:
                    return {"success": False, "error": "No student ID"}
                
                trend = self.risk_calculator.calculate_gpa_trend(student_id)
                
                result = {
                    "success": True,
                    "trend": trend
                }
                context["gpa_trend"] = trend
            
            elif task_name == "generate_explanation":
                # Use RAG to generate final explanation
                language = params.get("language", "en")
                
                # Build summary of all collected data
                summary = context.copy()
                summary.pop("student_id", None)
                
                explanation = self.rag_engine.generate_response(
                    query=f"Based on the collected data, provide a comprehensive analysis and recommendations: {json.dumps(summary, indent=2)}",
                    student_id=student_id,
                    include_context=True,
                    language=language
                )
                
                result = {
                    "success": True,
                    "explanation": explanation
                }
                context["final_explanation"] = explanation
            
            else:
                result = {"success": False, "error": f"Unknown task: {task_name}"}
        
        except Exception as e:
            result = {"success": False, "error": str(e)}
        
        return result
    
    def execute_workflow(self, query: str) -> Dict[str, Any]:
        """
        Main entry point: Understand intent, plan workflow, execute tasks
        """
        
        print(f"\n🤖 Processing query: {query}")
        print("="*60)
        
        # Step 1: Understand intent
        print("📝 Step 1: Understanding intent...")
        intent_data = self.understand_intent(query)
        print(f"   Intent: {intent_data.get('intent')}")
        print(f"   Confidence: {intent_data.get('confidence', 0):.2f}")
        
        # Step 2: Plan workflow
        print("\n🗺️  Step 2: Planning workflow...")
        workflow_plan = self.plan_workflow(intent_data)
        print(f"   Planned {len(workflow_plan)} tasks")
        for i, task in enumerate(workflow_plan, 1):
            print(f"   {i}. {task['task']}")
        
        # Step 3: Execute workflow
        print("\n⚙️  Step 3: Executing workflow...")
        context = {}
        execution_log = []
        
        for i, task in enumerate(workflow_plan, 1):
            print(f"   Executing {i}/{len(workflow_plan)}: {task['task']}...")
            result = self.execute_task(task, context)
            
            execution_log.append({
                "task": task["task"],
                "result": result,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            if not result.get("success"):
                print(f"   ⚠️  Task failed: {result.get('error')}")
        
        print("\n✅ Workflow execution complete!")
        print("="*60)
        
        # Return comprehensive result
        return {
            "query": query,
            "intent": intent_data,
            "workflow_plan": workflow_plan,
            "execution_log": execution_log,
            "context": context,
            "final_response": context.get("final_explanation", {})
        }


# Example usage
if __name__ == "__main__":
    from dotenv import load_dotenv
    from database.init_db import SessionLocal
    
    load_dotenv()
    
    db = SessionLocal()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if api_key:
        agent = AgenticWorkflow(db, api_key)
        
        # Test query
        result = agent.execute_workflow(
            "What is the risk level for student CS101?"
        )
        
        print("\n" + "="*60)
        print("FINAL RESPONSE:")
        print("="*60)
        if 'response' in result.get('final_response', {}):
            print(result['final_response']['response'])
        else:
            print("No response generated")
    else:
        print("❌ OPENAI_API_KEY not found!")
    
    db.close()
