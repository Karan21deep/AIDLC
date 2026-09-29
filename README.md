# .NET Modernization Agent — VS Code Extension

This project exposes the existing Python legacy .NET/WCF modernization agents through a VS Code extension.

## Architecture

```text
VS Code Extension (TypeScript)
        |
        v
FastAPI Backend (Python)
        |
        v
Your existing modernization agents
        |
        +--> Dependency Mapping
        +--> WCF Analysis
        +--> Modernization Plan
        +--> Code Generation
        +--> Validation
```

Discovery, Architecture Analysis and Code Understanding are reused from the existing `.modernization` artifacts in this first version, matching the current Streamlit pipeline.

## 1. Backend

Copy the `backend` files into your existing Python project root, next to your `agents/`, `models/`, and `tools/` folders.

Install:

```bash
pip install -r backend/requirements.txt
```

Start:

```bash
uvicorn backend.api:app --host 127.0.0.1 --port 8000
```

The backend expects the repository to already contain:

```text
.modernization/
├── discovery_report.json
├── architecture_report.json
└── code_analysis_cache.json
```

If your existing reports are currently under `output/`, either move them to `.modernization/` or change `_output_dir()` in `pipeline_service.py` back to `repository / "output"`.

## 2. Extension

Go into the extension folder:

```bash
cd extension
npm install
npm run compile
```

Open the extension project in VS Code and press `F5`.

Then open a legacy .NET/WCF repository and run:

```text
.NET Modernization: Modernize Repository
```

## 3. VS Code UI

The extension provides:

- Activity Bar entry
- Modernization sidebar
- Start modernization command
- Job ID tracking
- Pipeline stage/progress display
- Execution logs
- Report selection/opening
- Backend URL configuration

## 4. Important production improvement

For production, replace the in-memory `jobs` dictionary with Redis/database-backed job state and use a worker queue such as Celery, RQ, or a cloud job service. This allows multiple repositories and users to run modernization jobs concurrently.
