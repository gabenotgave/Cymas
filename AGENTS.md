# LANtern AI Agent Instructions

This document provides specific operational context for coding agents editing or exploring the LANtern project.

## 1. Architecture Philosophy 
LANtern operates on a **decoupled** architecture.
- **The System Monitor:** A background process configured in `main.py` runs platform-specific (mostly macOS-based) probes and logs output directly to a flat CSV file (`lantern_data.csv`).
- **The Backend API:** A FastAPI instance (`api/main.py`) reads from the CSV to expose endpoints for the dashboard and interfaces with `LiteLLM` for AI-powered diagnostics.
- **The Frontend:** A React/Vite web application built to visualize data metrics using charts.

When updating data flow, never couple the frontend directly to the system probes, and never couple the background monitor to FastAPI logic. The CSV acts as the singular source of truth linking the backend API and monitor.

## 2. Tech Stack and Boundaries
- **Backend:** Python + FastAPI. Do not introduce new web frameworks.
- **LLM Integration:** Diagnostics pass through `LiteLLM`, allowing vendor-agnostic use (OpenAI, Anthropic, Google, etc.). Only update vendor-specific logic through `LiteLLM` parameters.
- **Frontend:** React + Vite + Tailwind CSS + Recharts + lucide-react. The frontend maintains a local health dashboard aesthetic; avoid straying from the clean, native, and responsive Tailwind styling.

## 3. Editing Guidelines

### Working on Probes (`probes/`)
- **Cross-Platform Compatibility is a Priority:** Probes must be portable across macOS, Linux, and Windows. Cross-platform support is a main selling point of LANtern.
- *Note on Linux:* WiFi stats retrieval currently has known limitations on Linux (e.g., SNR & Channel metrics are absent). When modifying probes, aim to improve or maintain broad compatibility.
- When asked to add or modify probes, check `config.py` for target configurations.
- Ensure any breaking changes do not corrupt the formatting of the `lantern_data.csv` structure without appropriately migrating the FastAPI routing scripts (`api/routers/metrics.py`).

### Writing and Updating Tests (`tests/`)
- LANtern uses `pytest` and `pytest-mock`.
- Ensure tests verify functionality by stubbing subprocess and network calls rather than generating actual network traffic that might cause flakiness.

### AI Model Management
- The AI context in LANtern utilizes flexible keys and model identifiers from `.env`. Do not hardcode specific model strings in `router/analysis.py` except as configurable defaults if the environment variables are unset.
