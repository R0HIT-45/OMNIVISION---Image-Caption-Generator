# 13_USER_MANUAL.md
Version 1.0
Status: LOCKED

## 1. Introduction
Welcome to OmniVision! This manual provides step-by-step instructions for end-users to operate the Streamlit frontend. OmniVision is designed to be highly accessible and user-friendly, requiring no technical knowledge to operate.

## 2. Interface Overview
When you launch the OmniVision web application, the interface is split into two main sections:
- **Input Column (Left)**: Where you upload images and trigger the AI.
- **Output Column (Right)**: Where the generated captions, translations, and audio are displayed.
- **Explainability Panel (Bottom)**: An expandable section showing how the AI made its decisions.

## 3. Step-by-Step Usage

### Step 1: Uploading an Image
1. Locate the **"Drag and drop file here"** area on the left side of the screen.
2. You can drag an image from your computer directly into this box, or click **"Browse files"** to select an image manually.
3. Supported formats are `.jpg`, `.jpeg`, and `.png`. Maximum size is 10MB.
4. Once uploaded, a preview of your image will appear.

### Step 2: Generating the Caption
1. Click the **"Generate Caption & Narration"** button below the image preview.
2. A spinner will appear with the text *"Analyzing image and retrieving knowledge..."*.
3. Please wait. Because the AI is processing massive neural networks on your local machine, this process may take 10 to 20 seconds.

### Step 3: Viewing Results
Once processing is complete, the right column will populate:
1. **Final Caption**: The large text box displays the most accurate description the AI could generate. If historical or factual context was found, it will be included here seamlessly.
2. **Translations**: Below the English caption, you will see a tabbed menu (`English` | `Hindi` | `Telugu`). Click the tabs to read the translated captions.
3. **Audio Narration**: Below the text, an audio player will appear. Press the **Play** button to hear the caption spoken aloud. Switching language tabs will automatically update the audio player to the correct language.

### Step 4: Exploring AI Explainability
OmniVision is transparent about its decisions. 
1. Scroll down and click the **"View AI Decision Timeline"** expander.
2. You will see:
   - **Raw Caption**: What the vision model (BLIP-2) initially "saw" before any knowledge was added.
   - **Retrieved Knowledge**: What factual information (if any) was found in the database matching your image.
   - **Confidence Score**: A percentage indicating how certain the AI was that the retrieved knowledge matched your image.
   - **Decision**: A green checkmark if the knowledge was added to the final caption, or a red cross if it was rejected to prevent hallucination.

## 4. Troubleshooting
- **Error: "Cannot connect to backend"**: Ensure that the FastAPI backend server is running in your terminal.
- **Image taking too long**: Ensure your GPU has at least 4GB of VRAM available and no other heavy applications (like modern video games) are running simultaneously.
- **Upload fails**: Check that the image is under 10MB and in a valid format.
