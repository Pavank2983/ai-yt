import os

# ✅ Folder structure
folders = [
    "app/routes",
    "app/services",
    "app/utils",
    "app/db",
    "app/config",
    "app/scheduler",
    "assets/music",
    "assets/voices",
    "assets/images",
    "assets/templates",
    "output/shorts",
    "output/logs",
    "output/thumbnails",
    "tests"
]

# ✅ Files to initialize
files = [
    "app/__init__.py",
    "app/routes/__init__.py",
    "app/services/__init__.py",
    "app/utils/__init__.py",
    "app/db/__init__.py",
    "app/config/__init__.py",
    "app/scheduler/__init__.py",
    "app/db/models.py",
    "app/db/database.py",
    "app/utils/logger.py",
    "app/utils/file_handler.py",
    "app/utils/decorators.py",
    "app/services/script_generator.py",
    "app/services/voice_generator.py",
    "app/services/video_generator.py",
    "app/services/video_editor.py",
    "app/scheduler/daily_job.py",
    "app/config/settings.py",
    "main.py",
    "config.py",
    ".env",
    "requirements.txt",
    ".gitignore"
]

# ✅ Default .gitignore content
gitignore_content = """# Virtual environment
venv/

# Python cache
__pycache__/
*.pyc
*.pyo
*.pyd

# Environment & logs
.env
*.log

# Output folders
output/
assets/
"""

# ✅ Create folders
for folder in folders:
    os.makedirs(folder, exist_ok=True)

# ✅ Create files
for file in files:
    if not os.path.exists(file):
        with open(file, "w") as f:
            if file.endswith("__init__.py"):
                f.write("# Package init\n")

# ✅ Write .gitignore
with open(".gitignore", "w") as f:
    f.write(gitignore_content)

print("✅ Project structure created successfully!")
