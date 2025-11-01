# 🎬 AI YouTube Automation

**AI YouTube Automation** is a Python-based system designed to **automate AI-generated YouTube video creation and uploading**.  
It streamlines the process of generating ideas, scripts, voiceovers, visuals, and uploads — saving time while maintaining creativity and quality.

---

## 🚀 Features

- 🤖 **AI Script Generation** – Auto-generate creative video scripts.
- 🗣️ **AI Voiceover Integration** – Generate realistic voices via ElevenLabs or other TTS APIs.
- 🎥 **Video Generation Support** – Integrate with tools like Kaiber AI or Runway.
- 🧠 **Workflow Automation** – Automate video creation and publishing to YouTube.
- 🧩 **Modular Architecture** – Organized structure for scalability and maintenance.
- 📡 **FastAPI Backend** – Provides REST APIs for controlling workflows and status updates.

---

## 🧱 Project Structure

```
ai_youtube_automation/
│
├── app/
│ ├── core/ # Core configurations (DB, API setup, constants)
│ ├── services/ # Core automation logic (script, voice, video)
│ ├── routes/ # FastAPI routes
│ ├── utils/ # Helper modules
│ ├── tests/ # Unit tests
│ ├── init.py
│ └── main.py # FastAPI entry point
│
├── assets/ # Placeholder for input/output files
├── output/ # Generated video outputs
├── setup_structure.py # Script to generate folder structure
├── requirements.txt # Python dependencies
├── .env # Environment variables (ignored in Git)
├── .gitignore # Git ignore configuration
└── README.md # Project documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/YOUR_USERNAME/ai-yt.git
cd ai-yt
```

### 2️⃣ Create Virtual Environment

```
python -m venv venv
venv\Scripts\activate   # For Windows
source venv/bin/activate   # For Linux/Mac
```

### 3️⃣ Install Dependencies

```
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

```
# Database configuration
DB_AI_YT_HOST=localhost
DB_AI_YT_PORT=3306
DB_AI_YT_USER=ai_user
DB_AI_YT_PASSWORD=your_password
DB_AI_YT_NAME=ai_youtube_db

# App configuration
APP_NAME=AI YouTube Automation
APP_ENV=development
APP_DEBUG=True

# API keys
ELEVENLABS_API_KEY=
YOUTUBE_API_KEY=
OPENAI_API_KEY=
```

### 5️⃣ Run the App

```
uvicorn app.main:app --reload
```

Then open in browser:
👉 http://127.0.0.1:8000

🧠 Future Scope

Full AI workflow orchestration (Script → Voice → Video → Upload)
Advanced analytics dashboard
Integration with multiple TTS/AI video APIs
Automatic thumbnail generation

🤝 Contributing

Pull requests are welcome! Please ensure code readability and follow the project structure guidelines.

📜 License

This project is licensed under the MIT License – you are free to modify and use it commercially with attribution.

💡 Author

Pavan Kumar HV

🚀 GitHub: @Pavank2983

### Youtube credentials

##### EMAIL - `makeone.aihub@gmail.com`
##### PASSWORD - `NJh1SBEFB4fIgL3i`

