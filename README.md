# AI Interview Platform

An intelligent AI-powered technical and behavioral interview preparation platform featuring speech recognition, real-time AI answer analysis, live coding challenges, and comprehensive performance feedback.

---

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+ (A virtual environment `venv` is included in this directory)
- Google Gemini API Key configured in `.env` (optional, fallback responses are provided if missing)

---

## 💻 Running the Application

### ⚡ Quickest Method (Works in ANY Terminal - No activation needed)
```powershell
.\venv\Scripts\python.exe app.py
```

---

### Option 1: PowerShell (Default Terminal `PS`)
> **Note:** In PowerShell, `.bat` files do not activate the environment. Use `.ps1` instead:

```powershell
# 1. (If script execution is blocked on your system)
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Activate the virtual environment (.ps1)
.\venv\Scripts\Activate.ps1

# 3. Run the app
python app.py
```

---

### Option 2: Command Prompt (Classic `cmd.exe`)
```cmd
# 1. Activate the virtual environment (.bat)
venv\Scripts\activate.bat

# 2. Run the app
python app.py
```

---

### Option 3: Run Outside the IDE (Stays running even if IDE is closed)
1. Open an external **Command Prompt** or **PowerShell** window (`Win + R` -> type `cmd` or `powershell` -> Enter).
2. Execute:
   ```cmd
   cd C:\Users\Sahaj\Desktop\AI-Interview-Platform
   venv\Scripts\activate
   python app.py
   ```
3. Keep that window open. You can now safely close your IDE without stopping the server.

---

### Option 4: Run Silently in Background
To run the server in the background without any terminal window:
```powershell
Start-Process pythonw -ArgumentList "app.py" -WorkingDirectory "C:\Users\Sahaj\Desktop\AI-Interview-Platform"
```
To stop the background process later:
```powershell
taskkill /F /IM pythonw.exe
```

---

## 🌐 Accessing the App

Once the server is running, open your browser and go to:
👉 **[http://127.0.0.1:5000](http://127.0.0.1:5000)**

---

## 📂 Project Structure

- `app.py` - Flask web application routes and controller logic
- `ai_processor.py` - Gemini AI integration, question generation, and answer analysis
- `code_sandbox.py` - Python code execution sandbox for coding challenges
- `database.py` - SQLite database initialization and data access methods
- `report_generator.py` - Detailed performance report generation (HTML/PDF)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS styles and JavaScript logic (`interview.js`, `speech.js`, `camera.js`)
