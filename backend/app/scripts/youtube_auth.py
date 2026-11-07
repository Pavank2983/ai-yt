# Run this script to authenticate with the YouTube API and obtain an access token and refresh token. Make sure you have the `client_secret.json` file in the same directory as this script, which you can obtain from the Google Cloud Console when you create OAuth 2.0 credentials for your project.

# python app/scripts/youtube_auth.py

import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube"
]

TOKEN_PATH = "credentials/youtube_token.json"

def get_or_create_credentials():
    credentials = None

    # -------------------------------------------------
    # ✅ STEP 1 — Load existing token if present
    # -------------------------------------------------
    if os.path.exists(TOKEN_PATH):
        with open(TOKEN_PATH, "r") as f:
            credentials = Credentials.from_authorized_user_info(
                json.load(f),
                scopes=SCOPES
            )

    # -------------------------------------------------
    # 🔄 STEP 2 — Refresh if expired
    # -------------------------------------------------
    if credentials and credentials.expired and credentials.refresh_token:
        print("🔄 Refreshing existing token...")
        credentials.refresh(Request())

    # -------------------------------------------------
    # 🚀 STEP 3 — Create new if not available
    # -------------------------------------------------
    if not credentials or not credentials.valid:
        print("⚠️ No valid token found. Creating new one...")

        flow = InstalledAppFlow.from_client_secrets_file(
            "client_secret.json",
            scopes=SCOPES
        )

        credentials = flow.run_local_server(
            port=8080,
            prompt="consent",
            access_type="offline"
        )

    # -------------------------------------------------
    # 💾 STEP 4 — Save token (IMPORTANT)
    # -------------------------------------------------
    os.makedirs("credentials", exist_ok=True)

    with open(TOKEN_PATH, "w") as f:
        f.write(credentials.to_json())

    print("✅ Token ready and saved")

    return credentials


if __name__ == "__main__":
    creds = get_or_create_credentials()

    # print("\n🔐 ACCESS TOKEN:", creds.token)
    # print("\n🔥 REFRESH TOKEN:", creds.refresh_token)
