# 12_DEVELOPER_GUIDE.md
Version 1.0
Status: LOCKED

## 1. Introduction
This document serves as the onboarding manual for developers, researchers, or open-source contributors joining the OmniVision project. It enforces strict engineering standards to prevent the codebase from deteriorating into an unmaintainable state.

## 2. Coding Standards
- **Language**: Python 3.10+
- **Style Guide**: PEP-8 enforced via `flake8`.
- **Formatting**: `black` is the strict formatter. Line length is 88 characters.
- **Type Hinting**: Mandatory. Every function signature and class variable must include Python type hints (`List`, `Dict`, `Optional`, `Union`) from the `typing` module.
- **Docstrings**: Google-style docstrings are mandatory for all classes and public methods.

## 3. Git Workflow
OmniVision follows a simplified Feature Branch workflow.
1. **`main`**: Production-ready code only.
2. **`develop`**: Integration branch for new features.
3. **Feature Branches**: Named `feature/short-description` (e.g., `feature/add-qdrant-support`).
4. **Bugfix Branches**: Named `bugfix/issue-description`.

### 3.1 Pull Request (PR) Checklist
Before a PR can be merged into `main`:
- [ ] Code is formatted with `black`.
- [ ] Pytest suite passes locally (`pytest tests/`).
- [ ] Type hints are implemented.
- [ ] Memory utility functions are correctly invoked for any new AI models.
- [ ] Documentation (`.md` files) is updated if architecture changed.

## 4. Naming Conventions
- **Classes**: PascalCase (e.g., `RetrievalService`).
- **Methods/Functions**: snake_case (e.g., `generate_caption`).
- **Variables**: snake_case (e.g., `similarity_score`).
- **Constants**: UPPER_SNAKE_CASE (e.g., `GROUNDING_THRESHOLD`).
- **Filenames**: snake_case (e.g., `model_manager.py`).

## 5. Folder Guidelines
Do not dump code into the root directory.
- `backend/app/services/`: For logic that *does things* (AI, algorithms).
- `backend/app/routes/`: For logic that *receives things* (HTTP endpoints).
- `backend/app/schemas/`: For Pydantic models.
- `knowledge_base/`: For JSON and FAISS data ONLY. No Python scripts.

## 6. Model Update Procedure
If upgrading BLIP-2 to a newer version (e.g., Florence-2 or LLaVA):
1. **Do not modify `caption_service.py` directly at first.**
2. Create a new service (e.g., `florence_service.py`).
3. Implement the new service ensuring it returns the standard `RawCaption` string.
4. Update the `ModelManager` to support the new model ID and its memory footprint logic.
5. Change the dependency injection in `request_coordinator.py` to use the new service.
6. Verify no other components broke.

## 7. Documentation Standards
- Architecture changes must be reflected in `03_ENTERPRISE_SOFTWARE_ARCHITECTURE.md`.
- No architectural decision can be modified without writing a corresponding entry in `18_PROJECT_HISTORY_AND_DECISION_LOG.md`.
