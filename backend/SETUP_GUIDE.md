# 🚀 Explainable Agentic RAG System - Setup Guide

## Prerequisites

- Python 3.9 or higher
- 8GB RAM minimum (16GB recommended for full AI features)
- OpenAI API Key (get from https://platform.openai.com/api-keys)

## Step-by-Step Setup

### 1️⃣ Install Python Dependencies

```bash
cd backend
pip install -r requirements.txt
```

**Note:** Installing `torch` and `transformers` may take 5-10 minutes depending on your internet speed.

### 2️⃣ Configure OpenAI API Key

**Option A: Environment Variable (Recommended)**

Windows PowerShell:
```powershell
$env:OPENAI_API_KEY = "sk-your-actual-key-here"
```

Windows CMD:
```cmd
set OPENAI_API_KEY=sk-your-actual-key-here
```

**Option B: Edit .env file**

Edit `backend/.env` and replace:
```
OPENAI_API_KEY=sk-your-actual-key-here
```

### 3️⃣ Initialize Database

```bash
cd backend
python database/init_db.py
```

This creates `student_risk.db` with all required tables.

### 4️⃣ Generate Sample Data (Optional)

```bash
python scripts/generate_sample.py
```

This creates 50 sample students with grades, attendance, mentor notes, and behavioral logs.

### 5️⃣ Run System Tests

```bash
python test_system.py
```

This verifies:
- ✅ Database connectivity
- ✅ RAG Engine initialization
- ✅ Multilingual NLU
- ✅ Agentic Workflow
- ✅ Risk Calculator

### 6️⃣ Start the Backend Server

```bash
python main.py
```

Or with uvicorn directly:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Server will be available at: http://localhost:8000

### 7️⃣ Start the Frontend

```bash
cd ../frontend
npm install
npm run dev
```

Frontend will be available at: http://localhost:5173

## Testing the System

### API Documentation
Visit: http://localhost:8000/docs

Interactive API documentation with all endpoints.

### Test Endpoints

1. **Get all students**: `GET /api/students`
2. **Calculate risk**: `GET /api/risk/{student_id}`
3. **At-risk students**: `GET /api/students/at-risk`

### Test Natural Language Queries (Coming in Phase 9)

```python
# English
"What is the risk score for student CSE2024001?"

# Hindi
"छात्र CSE2024001 का रिस्क स्कोर क्या है?"

# Regional languages supported
```

## Feature Implementation Status

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Enhanced Database Schema | ✅ Complete |
| 2 | RAG Foundation | 🔄 In Progress |
| 3 | Agentic AI Workflow | 🔄 In Progress |
| 4 | Multilingual NLU | 🔄 In Progress |
| 5 | Explainability Engine | ⏳ Pending |
| 6 | Career Prediction | ⏳ Pending |
| 7 | Stress Detection | ⏳ Pending |
| 8 | Authentication & RBAC | ⏳ Pending |
| 9 | Chat Interface | ⏳ Pending |
| 10 | Testing & Documentation | ⏳ Pending |

## Troubleshooting

### Issue: "OpenAI API Key not configured"
**Solution:** Set the API key as shown in Step 2

### Issue: "ModuleNotFoundError"
**Solution:** Run `pip install -r requirements.txt` again

### Issue: "Database connection failed"
**Solution:** Run `python database/init_db.py` to create the database

### Issue: "ChromaDB initialization failed"
**Solution:** Delete `chroma_db` folder and restart. It will be recreated automatically.

### Issue: "Torch installation failed"
**Solution:** Install PyTorch separately:
```bash
pip install torch --index-url https://download.pytorch.org/whl/cpu
```

## Next Steps

Once setup is complete and tests pass:

1. ✅ Run test suite: `python test_system.py`
2. ✅ Generate sample data if needed
3. ✅ Start backend server
4. ✅ Test API endpoints in browser
5. 📱 Start frontend and test UI

## Support

For issues or questions:
- Check the documentation in `/docs`
- Review error logs in terminal
- Ensure all prerequisites are met

---

**Ready to build the future of educational AI! 🎓✨**
