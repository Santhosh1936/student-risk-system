# Student Risk System

A collaborative project for predicting and analyzing student risk factors.

## 🚀 Getting Started for Collaborators

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm
- Git
- OpenAI API key (get one at https://platform.openai.com/account/api-keys)

### Setup Instructions

#### 1. Clone the Repository
```bash
git clone https://github.com/Santhosh1936/student-risk-system.git
cd student-risk-system
```

#### 2. Backend Setup

**Navigate to backend folder:**
```bash
cd backend
```

**Create a virtual environment (recommended):**
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

**Install Python dependencies:**
```bash
pip install -r requirements.txt
```

**Set up your environment variables:**
Create a file named `.env` in the `backend` folder with the following content:
```
OPENAI_API_KEY=your_actual_api_key_here
```
⚠️ **IMPORTANT**: Never commit your `.env` file! It's already in `.gitignore`.

**Run the backend:**
```bash
python main.py
```

#### 3. Frontend Setup

**Navigate to frontend folder (in a new terminal):**
```bash
cd frontend
```

**Install dependencies:**
```bash
npm install
```

**Run the development server:**
```bash
npm run dev
```

## 🤝 Collaboration Workflow

### Basic Git Workflow

1. **Before starting work, always pull the latest changes:**
   ```bash
   git pull origin master
   ```

2. **Make your changes and commit them:**
   ```bash
   git add .
   git commit -m "Description of your changes"
   ```

3. **Push your changes:**
   ```bash
   git push origin master
   ```

### Best Practices

- ✅ **Always pull before starting work** to avoid merge conflicts
- ✅ **Commit frequently** with descriptive messages
- ✅ **Test your code** before pushing
- ✅ **Never commit sensitive data** (API keys, passwords, etc.)
- ✅ **Communicate with your partner** about major changes

### If You Get Merge Conflicts

```bash
# Pull the latest changes
git pull origin master

# Git will tell you which files have conflicts
# Open those files and look for conflict markers (<<<<<<<, =======, >>>>>>>)
# Edit the files to resolve conflicts
# Then:
git add .
git commit -m "Resolved merge conflicts"
git push origin master
```

## 📁 Project Structure

```
student-risk-system/
├── backend/
│   ├── main.py              # Backend entry point
│   ├── requirements.txt     # Python dependencies
│   ├── .env                 # Environment variables (DO NOT COMMIT)
│   ├── database/
│   │   └── init_db.py
│   ├── models/
│   │   └── student.py
│   ├── services/
│   │   ├── ml_predictor.py
│   │   └── risk_calculator.py
│   └── scripts/
│       └── generate_sample.py
├── frontend/
│   ├── package.json         # Node.js dependencies
│   ├── src/
│   │   ├── App.jsx
│   │   ├── StudentDashboard.jsx
│   │   └── AdminDashboard.jsx
│   └── public/
└── README.md               # This file
```

## 🔒 Security Notes

- The `.env` file is **never** committed to Git (it's in `.gitignore`)
- Each collaborator must create their own `.env` file with their own API key
- Never share API keys through Git, messaging apps, or public channels
- If you accidentally commit a secret, contact your partner immediately

## 📞 Getting Help

If you encounter issues:
1. Check if you've pulled the latest changes
2. Make sure all dependencies are installed
3. Verify your `.env` file is set up correctly
4. Contact your collaboration partner

## 🛠️ Troubleshooting

### "Module not found" error
```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
```

### Port already in use
- Backend: Check if another Python process is running on port 5000
- Frontend: Check if another dev server is running on port 5173

### Git push rejected
```bash
# Pull first, then push
git pull origin master
git push origin master
```

---

Happy coding! 🎉
