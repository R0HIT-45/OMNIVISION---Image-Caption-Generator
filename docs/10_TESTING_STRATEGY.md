# 10_TESTING_STRATEGY.md
Version 1.0
Status: LOCKED

## 1. Introduction
To ensure OmniVision functions as an enterprise-grade AI platform rather than a fragile academic prototype, a rigorous testing strategy is enforced. This strategy spans from localized code logic validation to end-to-end AI pipeline evaluation.

## 2. Testing Pyramid
OmniVision employs a multi-tiered testing approach using `pytest`.

### 2.1 Unit Testing
Tests individual functions, utilities, and isolated services without invoking heavy AI models.
- **Coverage Goal**: >85% for backend utilities and orchestrator logic.
- **Mocking**: The `ModelManager` and external API dependencies (like FAISS indices) are heavily mocked using `unittest.mock`.
- **Examples**:
  - Validating the Confidence Gate threshold logic (ensuring `0.74` fails and `0.76` passes).
  - Validating Image resizing algorithms (ensuring a `2000x2000` image is correctly scaled down).
  - Pydantic schema validation.

### 2.2 Integration Testing
Tests the interactions between the FastAPI layer and the internal Orchestrator, as well as the database (v2.0) operations.
- **Tools**: `fastapi.testclient.TestClient`.
- **Mocking**: Real HTTP requests are made to the local TestClient, but the actual GPU-bound models (BLIP, XTTS) are mocked to return deterministic strings and byte arrays to ensure fast execution.

### 2.3 End-to-End (E2E) Testing
Validates the entire pipeline from the Streamlit frontend down to the returned Audio files.
- **Execution**: Triggered only in pre-deployment CI pipelines.
- **Tools**: Selenium or Playwright for Streamlit automation.
- **Methodology**: Uploads a standard test image (e.g., `test_dog.jpg`), waits for the UI spinner to complete, and asserts that the Final Caption text box contains the expected keywords and the `<audio>` tags are successfully rendered.

## 4. AI Quality Testing (Offline Evaluation)
Unlike standard deterministic software, AI outputs are probabilistic. OmniVision implements an offline evaluation suite to ensure model upgrades do not degrade performance.

### 4.1 Caption Accuracy Validation
- **Dataset**: A curated subset of 100 images (from COCO or Flickr8k) with ground-truth captions.
- **Metrics**: 
  - **BLEU & METEOR**: Evaluates linguistic overlap between generated captions and ground-truth.
  - **CIDEr**: Evaluates consensus (how human-like the caption is).

### 4.2 Retrieval & Grounding Evaluation
- **Metric: Precision@K**: Evaluates if the FAISS index returns the correct historical fact for 50 benchmark images (e.g., if a photo of the Eiffel Tower correctly retrieves the Eiffel Tower fact in the Top-1 or Top-3 results).
- **Hallucination Check**: Images *not* in the knowledge base are fed to the system. The test asserts that the Grounding Service correctly rejects grounding (Confidence < 0.75).

## 5. Load and Performance Testing
Ensuring the system gracefully handles memory constraints.
- **Tool**: Locust or Apache JMeter.
- **Focus**: 
  - **Concurrency Limits**: The backend is configured to accept a maximum of `1` concurrent heavy processing request to prevent VRAM OOM on the 4GB RTX 3050. Extra requests are queued or return HTTP 429 (Too Many Requests).
  - **Latency Baseline**: Pipeline must complete in < 15 seconds per image.

## 6. Regression Testing
Before any code is merged into the `main` branch, the CI/CD pipeline (GitHub Actions) runs:
1. `flake8` and `black` for styling.
2. The full Pytest Unit/Integration suite.
3. If dependencies change, a test build of the Docker container is executed.
