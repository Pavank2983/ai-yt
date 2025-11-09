import os

# ✅ Folder structure
folders = [
    "app/routes",
    "app/services",
    "app/utils",
    "app/db",
    "app/config",
    "app/scheduler",
    "app/models",
    "app/schemas",
    "app/core",
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
    # Root
    "main.py",
    "run.py",
    ".env",
    "requirements.txt",
    ".gitignore",

    # Init files
    "app/__init__.py",
    "app/routes/__init__.py",
    "app/services/__init__.py",
    "app/utils/__init__.py",
    # "app/db/__init__.py",
    "app/config/__init__.py",
    "app/scheduler/__init__.py",
    "app/models/__init__.py",
    "app/schemas/__init__.py",

    # DB & Config
    "app/db/database.py",
    "app/db/init_db.py",
    "app/config/settings.py",

    # Utilities
    "app/utils/logger.py",
    "app/utils/file_handler.py",
    "app/utils/decorators.py",

    # Services
    "app/services/script_generator.py",
    "app/services/voice_generator.py",
    "app/services/video_generator.py",
    "app/services/video_editor.py",

    # Scheduler
    "app/scheduler/daily_job.py",
    
    # Authentication
    "app/core/security.py",
    "app/schemas/auth_schema.py",
    "app/services/auth_service.py",
    "app/routes/auth_route.py",
    
    # Unit tests
    "tests/__init__.py",
    "tests/test_auth.py",
    "tests/test_security.py",
    "tests/test_db.py",
]

# ✅ Auto-create base model, schema, route, and service files
modules = ["analytic", "api_usage", "automation_log", "category", "job", "notification", "platform", "script", "user", "video_issue", "video", "webhook"]

for module in modules:
    files.extend([
        f"app/models/{module}.py",
        f"app/schemas/{module}.py",
        f"app/services/{module}_service.py",
        f"app/routes/{'categorie' if module == 'category' else module}s.py" # plural routes (users.py, videos.py)
    ])

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
assets/music/
assets/voices/
assets/images/
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
