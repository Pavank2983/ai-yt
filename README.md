# 🎬 AI YouTube Automation

**AI YouTube Automation** is a Python-based system designed to **automate AI-generated YouTube video creation and uploading**.
It streamlines the process of generating ideas, scripts, voiceovers, visuals, and uploads — saving time while maintaining creativity and quality.

---

## 📚 Table of Contents

* [🚀 Features](#-features)
* [🧱 Project Structure](#-project-structure)
* [⚙️ Installation & Setup](#️-installation--setup)
* [🧠 Environment Configuration](#-environment-configuration)
* [▶️ Usage](#️-usage)
* [🧩 Future Scope](#-future-scope)
* [🤝 Contributing](#-contributing)
* [📜 License](#-license)
* [💡 Author](#-author)

---

## 🚀 Features

* 🤖 **AI Script Generation** – Auto-generate creative and engaging video scripts.
* 🗣️ **AI Voiceover Integration** – Generate realistic voiceovers using **ElevenLabs** or other TTS APIs.
* 🎥 **Video Generation Support** – Seamlessly integrate with AI tools like **Kaiber AI** or **Runway**.
* 🧠 **Workflow Automation** – End-to-end automation for creating and publishing YouTube videos.
* 🧩 **Modular Architecture** – Clean, scalable project structure for maintainability.
* 📡 **FastAPI Backend** – RESTful API endpoints for managing workflows and status updates.

---

## 🧱 Project Structure

```
ai_youtube_automation/
│
├── app/
│   ├── core/          # Core configurations (DB, API setup, constants)
│   ├── services/      # Core automation logic (script, voice, video)
│   ├── routes/        # FastAPI routes
│   ├── utils/         # Helper modules
│   ├── tests/         # Unit tests
│   ├── __init__.py
│   └── main.py        # FastAPI entry point
│
├── assets/            # Placeholder for input/output files
├── output/            # Generated video outputs
├── setup_structure.py # Script to generate folder structure
├── requirements.txt   # Python dependencies
├── .env               # Environment variables (ignored in Git)
├── .gitignore         # Git ignore configuration
└── README.md          # Project documentation
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone the Repository

```bash
git clone https://github.com/Pavank2983/ai-yt.git
cd ai-yt
```

### 2️⃣ Create a Virtual Environment

```bash
python -m venv venv
```

Activate it:

```bash
# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Configure Environment Variables

Create a `.env` file in the project root with the following structure:

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

---

## ▶️ Usage

Run the FastAPI app:

```bash
uvicorn app.main:app --reload
```

Then open your browser and navigate to:
👉 [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🔑 YouTube Credentials

| Field        | Value                     |
| ------------ | ------------------------- |
| **Email**    | `makeone.aihub@gmail.com` |
| **Password** | `NJh1SBEFB4fIgL3i`        |

---

## 🧠 Future Scope

* End-to-end AI workflow orchestration (Script → Voice → Video → Upload)
* Advanced analytics dashboard
* Integration with multiple AI tools (TTS, video generation, thumbnail creation)
* Smart title/description/SEO generation for YouTube uploads

---

## 🤝 Contributing

Contributions are welcome! 🎉
To contribute:

1. Fork the repository
2. Create a new branch (`feature/your-feature-name`)
3. Commit your changes
4. Submit a Pull Request

Please ensure code readability and follow the existing project structure.

---

## 📜 License

This project is licensed under the **MIT License**.
You are free to modify and use it commercially with proper attribution.

---

## 💡 Author

**Pavan Kumar HV**
🚀 [GitHub: @Pavank2983](https://github.com/Pavank2983)

---
