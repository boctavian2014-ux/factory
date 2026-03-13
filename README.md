# AI Content Factory

Production-ready distributed system for generating, scoring, and scheduling large volumes of short-form videos for **TikTok**, **Instagram Reels**, and **YouTube Shorts**.

## Goals

- **Detect trends** from TikTok, YouTube Shorts, Google Trends, Reddit
- **Generate viral ideas** (50–100 per trend)
- **Generate scripts** (3s hook + 10–30s narration + scene breakdown)
- **Generate AI videos** (voiceover, subtitles, 1080×1920 render via FFmpeg)
- **Score virality** with a PyTorch model; filter by threshold
- **Schedule content** and export CSV for posting tools

Designed to scale to **tens of thousands of videos per day** via Celery workers and Redis queues.

## Tech Stack

- **Python 3.11**
- **FastAPI** — API gateway
- **Celery** — task queues
- **Redis** — broker and result backend
- **PostgreSQL** — persistence
- **PyTorch** — virality model
- **Docker** + **FFmpeg** — deployment and video rendering
- **OpenAI API** — ideas, scripts, voiceover (TTS)

## Architecture

Microservices:

| Service           | Role                                      |
|-------------------|-------------------------------------------|
| **trend-service** | Scrape & analyze trends; store in DB      |
| **idea-service**  | Generate 50–100 video ideas per trend      |
| **script-service**| Turn ideas into scripts + scene breakdown |
| **video-service** | Voiceover, subtitles, FFmpeg render; optional Pexels bg, external API |
| **virality-service** | Score videos; set approved flag       |
| **scheduler-service** | Schedule approved; export CSV         |
| **clip-service** | Long-form → vertical shorts (Whisper + FFmpeg, ClippedAI-style) |
| **repo-service** | GitHub repo → idea/script (RepoClip-style) |

Workers communicate through **Redis** queues. Each pipeline step can be scaled independently (e.g. 20 idea workers, 30 script workers, 200 video workers).

## Project Structure

```
ai-content-factory/
├── api/
│   └── main.py                 # FastAPI app, mounts all service routers
├── services/
│   ├── trend_service/         # trend-service
│   │   ├── main.py
│   │   ├── trend_scraper.py
│   │   └── trend_analyzer.py
│   ├── idea_service/          # idea-service
│   │   ├── main.py
│   │   ├── idea_generator.py
│   │   └── hook_generator.py
│   ├── script_service/        # script-service
│   │   ├── main.py
│   │   ├── script_generator.py
│   │   └── scene_generator.py
│   ├── video_service/         # video-service (optional Pexels, external API)
│   │   ├── main.py
│   │   ├── video_renderer.py
│   │   ├── voiceover_generator.py
│   │   ├── subtitle_generator.py
│   │   ├── stock_media.py
│   │   └── external_video_client.py
│   ├── virality_service/      # virality-service
│   │   ├── main.py
│   │   ├── virality_model.py
│   │   └── predict.py
│   └── scheduler_service/    # scheduler-service
│       ├── main.py
│       ├── scheduler.py
│       └── exporter.py
│   ├── clip_service/         # long-form → shorts (ClippedAI-style)
│   │   ├── main.py
│   │   └── longform_to_short.py
│   └── repo_service/        # GitHub repo → idea (RepoClip-style)
│       ├── main.py
│       └── repo_analyzer.py
├── shared/
│   ├── config.py
│   ├── celery_app.py
│   ├── database.py
│   └── models.py
├── ml/
│   ├── trend_model/
│   │   ├── train.py
│   │   └── predict.py
│   └── virality_model/
│       ├── train.py
│       └── predict.py
├── workers/
│   ├── trend_worker.py
│   ├── idea_worker.py
│   ├── script_worker.py
│   ├── video_worker.py
│   └── virality_worker.py
├── outputs/
│   ├── videos/
│   └── csv/
├── docker/
│   ├── Dockerfile.api
│   └── Dockerfile.worker
├── docker-compose.yml
└── requirements.txt
```

## API Endpoints

| Method | Endpoint              | Description                          |
|--------|------------------------|--------------------------------------|
| POST   | `/trends/update`       | Scrape & store trends                |
| POST   | `/ideas/generate`      | Generate ideas for a trend           |
| POST   | `/scripts/generate`     | Generate script from idea            |
| POST   | `/videos/render`        | Render video from script (native or external API, optional Pexels bg) |
| POST   | `/videos/upload`       | Upload photo (JPG/PNG/WebP/GIF) or video (MP4/MOV/WebM)              |
| POST   | `/videos/from-upload`  | Make video from uploaded file (hook + concept → voice + subs on your media) |
| POST   | `/virality/score`       | Score video; update approved         |
| POST   | `/schedule/create`      | Create schedule; export CSV          |
| POST   | `/clips/from-long-form` | Long-form video → vertical shorts (Whisper + crop + subs) |
| POST   | `/repo/analyze`         | GitHub repo → video idea (JSON)      |
| POST   | `/repo/to-video`        | Repo → trend + idea in DB; returns idea_id for pipeline |
| GET    | `/health`              | Health check                         |
| GET    | `/`, `/dashboard`      | Dashboard (overview + pipeline + links la API) |

## Running with Docker

```bash
# Build and start API, workers, Redis, Postgres
docker-compose up --build

# API: http://localhost:8000
# Dashboard: http://localhost:8000/  (același stil în toată aplicația)
# Run pipeline: http://localhost:8000/run
# Docs (Swagger / ReDoc, theme dark): http://localhost:8000/docs  |  http://localhost:8000/redoc
```

### Environment

- `OPENAI_API_KEY` — optional; used for ideas, scripts, voiceover. Without it, fallbacks (templates, silent WAV) are used.
- `DATABASE_URL` — PostgreSQL (default in compose).
- `REDIS_CELERY_BROKER` / `REDIS_CELERY_RESULT` — Redis for Celery.
- `PEXELS_API_KEY` — optional; enables stock images as video background (ShortsGenerator-style). Set `enable_stock_media=true` in config.
- `VIDEO_GENERATION_BACKEND` — `native` (default) or `external_api`. With `external_api`, set `VIDEO_API_URL` to an Open-Sora / Sora-2-Generator style endpoint.

### Database

- **PostgreSQL** — Tables are created automatically when the API starts (`init_db()` in `api/main.py` lifespan).
- **Standalone init** (e.g. local Postgres before first run):
  ```bash
  set DATABASE_URL=postgresql://postgres:postgres@localhost:5432/ai_content_factory
  python -m scripts.init_db
  ```
- **Local development** — Use `DATABASE_URL=postgresql://user:pass@localhost:5432/ai_content_factory` if Postgres runs on the host instead of Docker.
- **Fără Docker (SQLite)** — Setează `DATABASE_URL=sqlite:///./content_factory.db` în `.env`; aplicația pornește fără Postgres.

### Deploy pe Railway

Proiectul este pregătit pentru **Railway**: folosește `PORT` din mediu și include `Procfile` + `railway.json`.

1. **Railway:** [railway.app](https://railway.app) → New Project → Deploy from GitHub (repo-ul tău).
2. **Variabile de mediu** (în Railway dashboard): `OPENAI_API_KEY`, `DATABASE_URL` (Postgres oferit de Railway sau extern), opțional `REDIS_URL` dacă adaugi Redis.
3. **Build:** Railway detectează Python și rulează `pip install -r requirements.txt`; start: `uvicorn api.main:app --host 0.0.0.0 --port $PORT` (din Procfile / railway.json).
4. **Cu Dockerfile:** în Settings poți seta Dockerfile path la `docker/Dockerfile.api`; imaginea folosește `PORT` și include `static/` (dashboard, run).

Fără Postgres/Redis, aplicația pornește (init_db e ignorat la eroare); pentru trends și DB trebuie `DATABASE_URL` setat.

### Obținere video (local, rapid)

1. **FFmpeg** instalat (necesar pentru render). Fără FFmpeg se creează doar un fișier placeholder.
2. Pornește API: `uvicorn api.main:app --host 0.0.0.0 --port 8000`
3. Deschide **http://localhost:8000/run** → secțiunea **Generează video** → completează hook + concept → **Generează video**. Video-ul se redă în pagină și poate fi descărcat.
4. **Voce:** cu `OPENAI_API_KEY` se folosește OpenAI TTS; fără cheie se folosește **gTTS** (gratuit); dacă gTTS e indisponibil, se folosește WAV silențios.
5. Endpoint direct: `POST /videos/quick` cu `{ "hook": "...", "concept": "...", "duration_seconds": 30 }` → răspuns cu `video_url` (ex: `/videos/file/quick_xxx.mp4`). Fișierele se servesc la `GET /videos/file/{filename}`.
6. **Video din upload:** pe **Run** → **Upload photo/video** → încarcă o imagine sau un clip (JPG, PNG, WebP, GIF, MP4, MOV, WebM) → completează hook + concept → **Generează video din fișier**. Video-ul tău devine fundal (imagine) sau sursă video (clip) cu voce și subtitrări generate.

### Scaling workers

```bash
# More generic workers (all queues)
docker-compose up -d --scale worker=10

# Dedicated workers: add services in docker-compose that override CMD, e.g.:
# worker_idea:
#   ... same build as worker ...
#   command: celery -A shared.celery_app worker -Q idea -l info -c 20 -n idea@%h
# worker_video:
#   command: celery -A shared.celery_app worker -Q video -l info -c 200 -n video@%h
```

## Celery queues

- `trend` — trend scraping/analysis
- `idea` — idea generation
- `script` — script generation
- `video` — video rendering (CPU/FFmpeg heavy)
- `virality` — virality scoring

Task names:

- `workers.trend_worker.update_trends`
- `workers.idea_worker.generate_ideas`
- `workers.script_worker.generate_script`
- `workers.video_worker.render_video`
- `workers.virality_worker.score_video`

## Pipeline overview

1. **Trends** — `POST /trends/update` or enqueue `update_trends`; trends stored in PostgreSQL.
2. **Ideas** — For each trend, `POST /ideas/generate` (or `generate_ideas`) → many ideas per trend.
3. **Scripts** — For each idea, `POST /scripts/generate` (or `generate_script`) → hook, narration, scene breakdown.
4. **Videos** — For each script, `POST /videos/render` (or `render_video_task`) → 1080×1920 MP4.
5. **Virality** — `POST /virality/score` (or `score_video_task`) → score and `approved` flag.
6. **Schedule** — `POST /schedule/create` for approved videos → CSV in `outputs/csv/`.

### Alternative pipelines (integrated)

- **Text-to-video API** — Set `VIDEO_GENERATION_BACKEND=external_api` and `VIDEO_API_URL` to an Open-Sora or Sora-2-Generator style server; `/videos/render` will call the API instead of native voiceover+FFmpeg.
- **Stock media (ShortsGenerator-style)** — Set `PEXELS_API_KEY` and `enable_stock_media=true` to use Pexels images as video backgrounds per script.
- **Long-form → shorts (ClippedAI-style)** — `POST /clips/from-long-form` with a video URL or file: Whisper transcription, highlight detection, vertical crop, burn-in subtitles.
- **Repo → video (RepoClip-style)** — `POST /repo/analyze` or `POST /repo/to-video` with a GitHub URL: README + LLM → one video idea (or trend+idea in DB) for the rest of the pipeline.

## Text-to-video: modele și servicii (low-cost / gratuit)

Pentru generare video din text, poți folosi:

- **Modele open-source** (GPU 8–12 GB sau Colab): [Open-Sora](https://github.com/hpcaitech/Open-Sora), RunDiffusion Video, ModelScope Text2Video — rulezi ca serviciu și pui `VIDEO_API_URL` în `.env`.
- **Servicii freemium**: RunwayML, Kaiber, Pictory.ai, Opus AI — câteva clipuri gratis/zi; scriptul îl generezi cu pipeline-ul, video-ul îl faci în platformă (sau prin API dacă există).

Pipeline complet gratuit/aproape gratuit: trend + idei + script (GPT/API) → text2video (Colab/Open-Sora sau freemium) → FFmpeg (integrat) → export. Detalii, tabele și workflow: **[docs/TEXT_TO_VIDEO_OPTIONS.md](docs/TEXT_TO_VIDEO_OPTIONS.md)**.

## License

MIT.
#   f a c t o r y  
 