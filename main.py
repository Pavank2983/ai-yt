from fastapi import FastAPI
from app.routes import auth_route

app = FastAPI(title="AI YouTube Automation API")

# ✅ Include Authentication Router
app.include_router(auth_route.router, tags=["Authentication"])

@app.get("/")
def root():
    return {"message": "🚀 AI YouTube Automation API is running!"}
