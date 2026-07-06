# 05_FRONTEND_DESIGN_SPECIFICATION.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document outlines the architecture, design, and user experience (UX) strategy for the OmniVision frontend. Built with Streamlit, the frontend serves as the Presentation Layer. It is strictly decoupled from AI inference logic, communicating exclusively with the FastAPI backend via REST endpoints. The design focuses on accessibility, explainability, and a professional, responsive UI.

## 2. Streamlit Architecture
The frontend is designed to be lightweight, modular, and maintainable. Instead of a single monolithic `app.py` script, the Streamlit application is organized into reusable components.

### 2.1 Folder Structure
```text
frontend/
├── app.py                 # Main entry point and page router
├── assets/                # Static assets (logos, custom CSS, placeholders)
│   ├── style.css          # Custom styling
│   └── omnivision_logo.png
├── components/            # Reusable UI widgets
│   ├── upload_component.py
│   ├── result_display.py
│   ├── explainability_panel.py
│   └── audio_player.py
├── utils/                 # Frontend utilities
│   ├── api_client.py      # Handles requests to FastAPI backend
│   └── state_manager.py   # Streamlit Session State helpers
└── requirements.txt       # Frontend dependencies
```

## 3. Session State Management
Streamlit reruns the script upon every user interaction. To prevent data loss and redundant API calls, `st.session_state` is rigorously managed via `utils/state_manager.py`.

### 3.1 Tracked State Variables
- `st.session_state.uploaded_file`: Stores the image binary in memory.
- `st.session_state.is_processing`: Boolean flag to disable the upload button and show loading spinners.
- `st.session_state.backend_response`: Caches the JSON response from the API. If present, the app bypasses the API call and renders the results directly.
- `st.session_state.error_message`: Stores user-friendly error strings if the backend returns a failure.

## 4. UI Wireframes & Layout
The application utilizes a wide layout (`layout="wide"`) to accommodate complex explainability data.

### 4.1 Page Layout
```text
+-------------------------------------------------------------+
| [LOGO] OmniVision: AI Image Captioning & Audio Narration    |
+-------------------------------------------------------------+
| +-------------------------+ +-----------------------------+ |
| |       COLUMN 1          | |        COLUMN 2             | |
| |  [ Upload Component ]   | |    [ Final Caption ]        | |
| |  (Drag and drop image)  | |    [ Audio Player ]         | |
| |                         | |    [ Translations ]         | |
| |  [ Generate Button ]    | |                             | |
| +-------------------------+ +-----------------------------+ |
+-------------------------------------------------------------+
|                     [ EXPANDABLE PANEL ]                    |
|                    AI Decision Timeline                     |
|  - Raw Caption                                              |
|  - Retrieved Knowledge                                      |
|  - Confidence Score vs Threshold                            |
|  - Grounding Decision                                       |
+-------------------------------------------------------------+
```

## 5. Component Tree & Responsibilities

### 5.1 Upload Component (`upload_component.py`)
- **UI**: Uses `st.file_uploader`.
- **Validation**: Restricts input to `png`, `jpg`, `jpeg`.
- **Preview**: Displays a thumbnail of the uploaded image.

### 5.2 Result Display (`result_display.py`)
- **Final Caption**: Uses large, readable typography for the grounded caption.
- **Translations**: Uses Streamlit tabs (`st.tabs`) to switch between English, Hindi, and Telugu.
- **Audio Player**: Uses `st.audio` to play the returned audio files. Automatically links the audio to the currently selected language tab if possible.

### 5.3 Explainability Dashboard (`explainability_panel.py`)
This is the core differentiating feature of the UI. It demystifies the AI pipeline.
- Uses `st.expander("View AI Decision Timeline")`.
- Employs `st.metric` or custom HTML to display the **Similarity Score**.
- Uses visual cues (green checks, red crosses) to indicate whether Grounding was applied based on the threshold.
- Displays the **Raw Caption** side-by-side with the **Final Grounded Caption** for direct comparison.

## 6. Progress Indicators and UX
Given that AI inference (especially on a 4GB VRAM GPU) can take 10-20 seconds, user feedback is critical.
- **Spinner**: `st.spinner("Analyzing image and retrieving knowledge...")` wraps the API call.
- **Status Container**: A dynamic `st.empty()` container is updated via HTTP streaming or WebSocket (if implemented in future versions) to show precise stages (e.g., "Generating embeddings...", "Translating to Hindi..."). In v1.0, a standard spinner is sufficient.

## 7. Error Handling
The frontend gracefully handles backend errors without exposing Python tracebacks to the user.
- **API Unreachable**: Displays `st.error("Cannot connect to the AI backend. Please ensure the server is running.")`
- **AI Processing Error**: Parses the HTTP 400/500 JSON response and displays a warning: `st.warning("Failed to generate audio, but captions are available.")` (Example of graceful degradation).

## 8. Accessibility
As an accessibility-focused platform, the UI adheres to best practices:
- **High Contrast**: The custom CSS enforces a high-contrast dark or light theme.
- **Semantic HTML**: Custom markdown components use proper heading hierarchies.
- **Audio Prominence**: The text-to-speech play controls are large and easily accessible.

## 9. Theme Configuration
Streamlit theming is configured in `.streamlit/config.toml` to ensure a professional SaaS look rather than the default Streamlit appearance.
```toml
[theme]
primaryColor = "#2E86C1"
backgroundColor = "#0E1117"
secondaryBackgroundColor = "#262730"
textColor = "#FAFAFA"
font = "sans serif"
```

## 10. API Client
`utils/api_client.py` uses the `requests` library (or `httpx` for async) to communicate with FastAPI.
It includes:
- Configurable base URL reading from environment variables.
- Timeout handling (e.g., `timeout=60` seconds).
- Payload parsing and error normalization.
