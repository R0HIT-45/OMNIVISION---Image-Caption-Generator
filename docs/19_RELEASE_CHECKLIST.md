# 19_RELEASE_CHECKLIST.md
Version 1.0
Status: ACTIVE (OmniVision v1 Release Workflow)

## 1. Introduction
This checklist tracks the Verification Sprint required to graduate OmniVision v1 from "Implementation Complete" to "Placement Ready." No feature additions are permitted during this phase.

## 2. System Modules Checklist

### Backend Infrastructure
- [ ] FastAPI starts without crashing
- [ ] Swagger Docs (`/docs`) load successfully
- [ ] Health Endpoint (`/api/v1/health`) returns 200 OK
- [ ] Upload Endpoint properly validates files and rejects >10MB or non-images
- [ ] Logging outputs structured JSON with latencies

### Core AI Pipeline
- [ ] **BLIP (Captioning)**: Generates detailed, reasonable captions.
- [ ] **CLIP (Embedding)**: Generates 512-dimensional vectors successfully.
- [ ] **FAISS (Retrieval)**: Correctly retrieves Top-1 fact based on vector similarity.
- [ ] **Grounding (Confidence Gate)**: Rejects grounding for generic images (low similarity); Applies grounding for known entities (high similarity).
- [ ] **Translation (IndicTrans2)**: Correctly outputs Hindi and Telugu strings.
- [ ] **XTTS (Speech)**: Successfully generates playable `.wav` files.

### Frontend (Streamlit)
- [ ] UI loads without crashing
- [ ] Uploading an image triggers the spinner correctly
- [ ] Results populate in the correct language tabs
- [ ] Audio player renders and plays the generated `.wav` files
- [ ] **Explainability Panel**: Correctly displays the visual pipeline, similarity score, threshold, and model latencies.

### GPU Memory Management (RTX 3050 - 4GB)
- [ ] `ModelManager` successfully unloads Vision models before loading XTTS
- [ ] Peak VRAM does not exceed 3800MB
- [ ] Repeated requests do not cause a VRAM memory leak

## 3. Documentation & Final Delivery
- [ ] All 19 Architecture/Engineering documents reviewed
- [ ] `README.md` is complete with badges and installation instructions
- [ ] `.gitignore` is properly configured
- [ ] `Dockerfile` and `docker-compose.yml` are ready for v2.0 deployments
- [ ] Clean Git commit history

## 4. Release Approval
When all boxes above are checked `[x]`, OmniVision v1 is officially verified and ready for the GitHub release and Demo Video recording.
