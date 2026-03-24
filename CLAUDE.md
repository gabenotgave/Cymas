# Cymas - AI Companion Guide (CLAUDE.md)

Welcome to Cymas! This file outlines essential commands, coding conventions, and stylistic rules so you can contribute efficiently to the repository.

## Commands

### Setup
Activate the virtual environment before running any Python scripts:
```bash
source .venv/bin/activate
```

### Running the Application Structure
1. **Background Monitor/Logger:** Starts network testing probes.
```bash
python -m probes.main
```
2. **FastAPI Backend:** Serves data to the frontend and provides LLM diagnostics.
```bash
uvicorn api.main:app --reload --port 8000
```
3. **React Dashboard:** Vite development server.
```bash
cd dashboard && npm run dev
```

### Testing
Run tests seamlessly by utilizing the `pytest` runner, which executes all tests in `tests/` using mocked networking requests.
```bash
pytest
```

## Formatting & Code Style

- **Python:** The workspace follows standard PEP8 conventions natively. Use explicit types for function parameters where appropriate.
- **Cross-Platform Portability:** Cymas is designed to run on macOS, Linux, and Windows. When modifying or adding new features (especially hardware or network probes), always prioritize cross-platform compatibility as a core selling point.
- **React Frontend:**
  - Standard React hook patterns (`useState`, `useEffect`).
  - Styling is handled exclusively with **Tailwind CSS**. Avoid writing custom vanilla CSS unless strictly required.
  - Utilize **Recharts** for time-series charts (`components/TimeSeriesChart.jsx`, `components/DnsChart.jsx`, etc.).
  - Icons are integrated from **lucide-react**.

## Architecture Quick Reference

- **`/probes`**: Scripts for network diagnostics (ping, arp, http resolution).
- **`/api`**: Holds the standard FastAPI app, connecting the raw read CSV to JSON endpoints in `/routers`.
- **`probes/config.py`**: A centralized location mapping intervals, testing hosts, and absolute paths for tools.
- **`lantern_data.csv`**: The primary log database written to by the Python Monitor and read out by the FastAPI.
- **`/dashboard`**: An SPA application built specifically using React fetching data primarily from FastAPI.
