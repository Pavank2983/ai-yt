# Environment Setup & Runtime Assumptions

This document defines the **locked environment assumptions** for the AI YouTube Automation System.

Its purpose is to:

* Prevent environment drift
* Make redeployment predictable
* Prepare the system for Docker *later* (without using Docker now)

This file should be updated **only when a real environment change is intentionally made**.

---

## 1. Operating System

**Primary target:**

* Linux (**Ubuntu 22.04**)

**Development support:**

* Windows 10/11 (development only)

**Notes:**

* Production deployments are assumed to run on **Ubuntu 22.04**
* FFmpeg behavior and file permissions are Linux-oriented

---

## 2. Python Runtime

**Required Python version:**

```
Python 3.11.x
```

**Not supported:**

* Python 3.12+ (audio + ML dependency instability)
* Python 3.10 or below

**Virtual environment:**

* Strongly recommended (venv or virtualenv)

---

## 3. System-Level Dependencies

The following system packages **must be installed** before running the backend:

```
ffmpeg (>= 6.x)
libsndfile1
build-essential
```

**Why this matters:**

* FFmpeg is required for video merge, trimming, and audio processing
* libsndfile is required for audio decoding (librosa / soundfile)

---

## 4. Python Dependencies

**Installation method:**

```
pip install -r requirements.txt
```

**Rules:**

* Do not install Python packages globally
* requirements.txt is the source of truth
* Any new dependency must be added explicitly

---

## 5. Environment Variables

The backend **will not start correctly** unless these variables are defined.

### Core

```
DATABASE_URL
JWT_SECRET
```

### Authentication / Cookies

```
COOKIE_DOMAIN
COOKIE_SECURE   (true/false)
```

### AI Providers

```
MINIMAX_API_KEY
SILICONFLOW_API_KEY
```

### AI Providers

```
MINIMAX_API_KEY
SILICONFLOW_API_KEY
OPENAI_API_KEY
```

**Notes:**

* OpenAI is actively used for script generation in production
* Secrets are never committed to the repository
* .env files are local-only and ignored by git

**Notes:**
- Secrets are never committed to the repository
- .env files are local-only and ignored by git

---

## 6. File System & Paths

**All paths must be absolute at runtime.**

**Asset root:**
```

assets/output/

```

**Per-script structure:**
```

assets/output/script_<script_id>/
├─ tts/
├─ scenes/
├─ merged/
└─ final/

```

**Rules:**
- No relative path assumptions
- No hardcoded OS-specific separators
- FFmpeg reads/writes must target absolute paths

---

## 7. Background Scheduler

**Scheduler:**
- APScheduler

**Current mode:**
- Runs in the same backend process
- No external queue system yet

**Execution guarantees:**
- TTS jobs must complete before scene jobs start
- Scene jobs run with concurrency limits
- Merge job runs only after all scenes succeed

---

## 8. Video Job & Failure Rules (LOCKED)

- If any TTS job fails → Video is marked FAILED → Scene jobs are blocked
- Scene-level partial retry is NOT supported in v1
- Full-video retry only (future feature)

These rules must remain consistent across environments.

---

## 9. Deployment Assumptions (Current)

- Single-node deployment
- One backend process
- No worker separation
- No containerization yet

These assumptions will change **only when Docker or workers are introduced**.

---

## 10. Change Policy

This file is considered **locked**.

Update it ONLY when:
- A dependency version is intentionally upgraded
- A runtime assumption changes
- Infrastructure design changes (e.g., Docker, workers)

---

## Open Questions / To Be Confirmed

- [ ] Exact Ubuntu version used in production
- [x] GPU acceleration may be introduced later (decision deferred)
- [ ] Whether Redis or external queue will be added in v2

---

**Status:** ACTIVE
**Last updated:** Feb 2026

```
