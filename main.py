from fastapi import FastAPI
from app.routes import auth_route, scripts, script_bulk, voices
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="AI YouTube Automation API")

# ✅ Include Authentication Router
app.include_router(auth_route.router, tags=["Authentication"])

# ✅ Include Script Router
app.include_router(scripts.router, prefix="/scripts", tags=["Script Generation"])

# ✅ Include Bulk Script Router
app.include_router(script_bulk.router, prefix="/scripts", tags=["Bulk Script Generation"])

# ✅ Include TTS Router
app.include_router(voices.router, tags=["TTS Voice Generation"])

@app.get("/")
def root():
    return {"message": "🚀 AI YouTube Automation API is running!"}
