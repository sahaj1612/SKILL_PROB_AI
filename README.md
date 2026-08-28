# AI Interview Platform

An AI-powered technical and behavioral interview preparation platform featuring speech recognition, real-time answer analysis, and comprehensive performance feedback.

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

## 📊 Understanding Your Interview Scores

After you submit each answer, the platform gives four scores out of 10. A higher score means the answer was stronger in that area. These scores are coaching feedback to help you practise; they are not an official hiring decision.

| Score | What it means | How to improve it |
| --- | --- | --- |
| **Grammar** | Checks how clear and well-structured your sentences are, including sentence completion and unnecessary filler words. | Use complete sentences, pause instead of saying “um” or “uh”, and quickly review typed answers for punctuation. |
| **Relevance** | Checks whether your answer directly responds to the question and includes the important topic or skills asked about. | Start with a direct answer, then use a relevant example instead of adding unrelated background. |
| **Confidence** | Estimates how clearly and completely you communicate your answer. It considers answer detail, sentence structure, relevance, and filler words. | Speak at a steady pace, give enough detail, and support your point with a specific example. |
| **STAR Method** | Checks whether a behavioural answer follows **S**ituation, **T**ask, **A**ction, and **R**esult. | Explain the context, your responsibility, the actions you personally took, and the measurable result. |

### Score guide

- **8–10:** Strong answer. Keep the same structure and clarity.
- **5–7:** Good foundation, but add clearer detail, stronger examples, or a better structure.
- **1–4:** Needs improvement. Answer the question more directly and use a specific example.

### Other feedback shown after an answer

- **Filler words:** Counts words or phrases such as “um”, “uh”, “like”, and “you know”. A pause is usually better than a filler word.
- **Suggested Better Answer:** Shows one possible way to make your own answer clearer, more relevant, and more structured. Use it as a guide, not a script to memorise word-for-word.
- **Follow-up Question:** Appears when an answer is very short, vague, or lacks depth. It helps you add missing details.
- **Camera Check:** If the camera is enabled, this gives practice suggestions about face visibility, eye visibility, screen focus, multiple faces, and lighting. Video is analysed locally; it is not uploaded or recorded.

---

## 📂 Project Structure

- `app.py` - Flask web application routes and controller logic
- `ai_processor.py` - Gemini AI integration, question generation, and answer analysis
- `database.py` - SQLite database initialization and data access methods
- `report_generator.py` - Detailed performance report generation (HTML/PDF)
- `templates/` - Jinja2 HTML templates
- `static/` - CSS styles and JavaScript logic (`interview.js`, `speech.js`, `camera.js`)
