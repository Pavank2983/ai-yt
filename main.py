from fastapi import FastAPI
from app.routes import users

app = FastAPI(title="AI YouTube Automation API")

# ✅ Include routers
app.include_router(users.router, prefix="/api/users", tags=["Users"])
# app.include_router(categories.router, prefix="/api/categories", tags=["Categories"])
# app.include_router(platforms.router, prefix="/api/platforms", tags=["Platforms"])
# app.include_router(scripts.router, prefix="/api/scripts", tags=["Scripts"])
# app.include_router(videos.router, prefix="/api/videos", tags=["Videos"])

@app.get("/")
def root():
    return {"message": "🚀 AI YouTube Automation API is running!"}
