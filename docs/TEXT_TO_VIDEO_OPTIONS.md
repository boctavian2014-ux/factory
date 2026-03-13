# Text-to-video: modele open-source și servicii freemium

Ghid pentru alegerea backend-ului de generare video (local, Colab sau cloud freemium) și integrarea cu pipeline-ul AI Content Factory.

---

## 1. Modele open-source (text → video)

Pot fi rulate pe **GPU local** sau **cloud ieftin** (Colab / Paperspace).

| Model | Ce face | Resurse | Link |
|-------|---------|---------|------|
| **Open-Sora** | text → video ~15s, style customization | GPU 8–12 GB VRAM | [GitHub](https://github.com/hpcaitech/Open-Sora) |
| **RunDiffusion Video** | diffusion video, clip 8–12 sec | GPU 12 GB+ | [Hugging Face](https://huggingface.co/runwayml/stable-diffusion-videos) |
| **ModelScope Text2Video** | text → short video 10–15s | GPU 8–12 GB | [ModelScope](https://www.modelscope.cn/models/damo/text2video-text2video) |

⚠️ **Local** rulează doar pe GPU puternic (8–12 GB VRAM minim). Altfel folosește **Google Colab** (gratuit, 6–12 GB GPU, cu limitări).

**Integrare în AI Content Factory:** rulezi modelul ca serviciu (ex. Open-Sora pe Colab cu ngrok, sau pe un server cu GPU) și setezi:

```env
VIDEO_GENERATION_BACKEND=external_api
VIDEO_API_URL=http://<your-server>:port/generate
```

`POST /videos/render` va trimite promptul (hook + script) către acest API și va folosi video-ul returnat.

---

## 2. Servicii freemium / cloud

Nu necesită instalare; oferă câteva clipuri gratuite pe zi/lună.

| Platformă | Tip video | Gratuit / limitări | Link |
|-----------|-----------|---------------------|------|
| **RunwayML** | text → video, green screen, editing | 5–10 video / lună | [runwayml.com](https://runwayml.com) |
| **Kaiber** | text → video, anime / cinematic | 3–5 video / zi | [kaiber.ai](https://www.kaiber.ai) |
| **Pictory.ai** | script / text → short video | 1–3 video / zi | [pictory.ai](https://pictory.ai) |
| **Opus AI** | short video, stock images | ~10 video / lună (plan freemium) | [opus.ai](https://opus.ai) |

**Integrare:** pentru prototip, poți genera scriptul cu pipeline-ul nostru (trends → ideas → scripts), apoi copia scriptul în platforma aleasă și descărca MP4. Pentru automatizare ar fi nevoie de API-uri oficiale (dacă există) și un adapter în `video_service` (ex. client Runway/Kaiber).

---

## 3. Workflow low-cost / gratuit

### Variantă 1: Text2Video open-source + Colab

- Rulezi **Open-Sora** sau **ModelScope** pe **Google Colab**.
- Limitezi clipurile la 10–15 sec.
- Expozi endpoint (ex. ngrok) și pui `VIDEO_API_URL` în `.env`.
- Export MP4 vine direct în pipeline.

### Variantă 2: Freemium cloud pentru prototip

- **Kaiber** sau **RunwayML** pentru testare idei virale fără GPU propriu.
- Idee + script generate cu **GPT** sau **OpenAI API** (credite gratuite) prin `POST /ideas/generate` și `POST /scripts/generate`.
- Scriptul îl trimiți manual în serviciul freemium; descarci video-ul și îl poți post-procesa cu FFmpeg (subtitrări, crop vertical).

### Variantă 3: Post-procesare gratuită (integrată)

- **FFmpeg** (local) pentru subtitrări și crop vertical — deja în pipeline (`/videos/render` cu backend `native`, sau `/clips/from-long-form`).
- Opțional: watermark, normalizare audio etc.

---

## 4. Pipeline complet gratuit / aproape gratuit

```
Trend detection (GPT / API free credits)
         ↓
Idea generation (GPT / LLaMA / OpenAI API)
         ↓
Script generation (GPT / open LLM)
         ↓
Text2Video (Kaiber freemium SAU Open-Sora Colab)
         ↓
FFmpeg processing (subtitrări, crop vertical)
         ↓
Upload TikTok / Instagram
```

- **~5–10 clipuri / zi** gratuit cu freemium (Kaiber, Runway etc.).
- **Mai mult** cu Colab + Open-Sora (limitat de quota Colab).
- **Volum mare (>100 video/zi)** necesită GPU propriu sau abonament cloud.

---

## Raport cu acest proiect

| Pas | În AI Content Factory |
|-----|------------------------|
| Trend detection | `POST /trends/update` |
| Idea generation | `POST /ideas/generate` |
| Script generation | `POST /scripts/generate` |
| Text2Video | `POST /videos/render` (backend `native` = voiceover+FFmpeg; `external_api` = Open-Sora / API custom) sau export manual către Runway/Kaiber |
| FFmpeg | integrat în `/videos/render` și `/clips/from-long-form` |
| Schedule / export | `POST /schedule/create` → CSV |
