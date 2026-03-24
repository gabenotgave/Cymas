![Cymas](dashboard/src/assets/Cymas-logo-banner.gif)

A local WiFi network health monitor with LLM-powered diagnostics.

[![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

---

## Overview

Cymas runs as a cross-platform background agent, sampling network health at any set frequency and writing results to a local CSV. It tracks gateway ping, external ping, DNS resolution latency, HTTP time-to-first-byte, WiFi radio stats, and active device count. A FastAPI backend and React dashboard sit on top of this data, providing per-metric visualizations and an LLM-powered root cause analysis designed to explain home network degradation in the context of household usage patterns. The probes and scheduler are written for macOS but should be portable to Linux and Windows, although those platforms are currently untested.

## Features

- Per-metric time-series charts  
- Device count correlation view  
- DNS cache hit/miss visualization  
- WiFi radio health tracking  
- Anomaly detection (2σ spike detection)  
- LLM-powered diagnosis via any frontier model  
- CSV export for ML or custom analysis  
- native scheduling

## Tech stack

| Backend                             | Frontend                                 |
| ----------------------------------- | ---------------------------------------- |
| Python                              | React                                    |
| FastAPI                             | Vite                                     |
| pandas                              | Recharts                                 |
| LiteLLM                             | Tailwind CSS                             |
| python-dotenv                       | lucide-react                             |

## Project structure

```text
Cymas/
├── api/                        # FastAPI application (main app + routers)
│   ├── __init__.py
│   ├── main.py                 # FastAPI app entrypoint
│   └── routers/
│       ├── __init__.py
│       ├── metrics.py          # CSV-backed metrics endpoints
│       └── analysis.py         # LLM-powered analysis endpoint
├── probes/                     # Platform-specific probes, logger, and configuration
│   ├── __init__.py             # Package init
│   ├── config.py               # Global configuration (intervals, hosts, CSV path)
│   ├── main.py                 # Logger loop: orchestrates probes and CSV writes
│   ├── gateway.py              # Default gateway discovery
│   ├── ping_probe.py           # Gateway/external ping sampling
│   ├── dns_probe.py            # DNS resolution timing
│   ├── http_probe.py           # HTTP TTFB probe
│   ├── wifi_probe.py           # WiFi radio stats (RSSI, noise, SNR, channel, rate)
│   └── arp_probe.py            # Active device count via ARP table
├── io/                         # Persistence and structured I/O helpers
│   └── writer.py               # CSV writer for normalized metric rows
├── dashboard/                  # React + Vite dashboard
│   ├── index.html              # SPA HTML shell
│   ├── vite.config.js          # Dev server and proxy config
│   └── src/
│       ├── main.jsx            # React root
│       ├── App.jsx             # Top-level layout and routing
│       ├── constants/          # Frontend constants (thresholds, etc.)
│       │   └── thresholds.js
│       ├── hooks/              # Data-fetching hooks
│       │   └── useMetrics.js
│       ├── components/         # UI components and charts
│       │   ├── NavBar.jsx
│       │   ├── StatCards.jsx
│       │   ├── TimeSeriesChart.jsx
│       │   ├── DnsChart.jsx
│       │   ├── WiFiRadioChart.jsx
│       │   ├── DeviceCorrelationChart.jsx
│       │   ├── RawTable.jsx
│       │   └── AnalysisResultModal.jsx
│       └── assets/             # Logo and favicon assets
├── tests/                      # pytest test suite (probes, IO, API)
│   ├── __init__.py
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_gateway.py
│   ├── test_ping_probe.py
│   ├── test_dns_probe.py
│   ├── test_http_probe.py
│   ├── test_wifi_probe.py
│   ├── test_arp_probe.py
│   └── test_writer.py
├── .env.example                # Example environment config for LLM keys and model
├── requirements.txt            # Python dependencies
├── run_lantern.sh              # Helper script to start logger, API, and dashboard
└── LICENSE                     # MIT license
```

## Getting started

### Prerequisites

- Python 3.10+  
- Node.js 18+  
- Google AI Studio API key (for Gemini) or Anthropic API key  

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/gabenotgave/Cymas.git
   cd Cymas
   ```

2. **Create and activate a Python virtual environment**

   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Python dependencies**

   ```bash
   pip install -r requirements.txt
   ```

4. **Install dashboard dependencies**

   ```bash
   cd dashboard
   npm install
   cd ..
   ```

5. **Configure environment**

   ```bash
   cp .env.example .env
   ```

   Edit `.env` and set **`CYMAS_MODEL`** to the LiteLLM model ID you want (e.g. `gemini/gemini-2.5-flash-lite`, `anthropic/claude-3-5-sonnet`, `openai/gpt-4o-mini`) and the corresponding provider API key. LiteLLM supports many providers (Google, Anthropic, OpenAI, Azure, Groq, Together, Cohere, Mistral, OpenRouter, etc.); see `.env.example` for placeholder variable names and the [Configuration](#configuration) table below.

6. **Run the monitor (logger + probes)**

   ```bash
   source .venv/bin/activate
   python -m probes.main
   ```

7. **Run the API**

   ```bash
   source .venv/bin/activate
   uvicorn api.main:app --reload --port 8000
   ```

8. **Run the dashboard**

   ```bash
   cd dashboard
   npm run dev
   ```

9. **Open the dashboard**

   Visit:

   ```text
   http://localhost:5173
   ```

## Configuration

Endpoints (e.g. ping/HTTP targets) and sampling frequency are defined in **`probes/config.py`**; edit that file to change probe intervals or which hosts are used for health checks.

| Variable            | Required                    | Default                     | Description                                                                                  |
| ------------------- | --------------------------- | --------------------------- | -------------------------------------------------------------------------------------------- |
| `CYMAS_MODEL`       | Yes (for LLM diagnostics)   | _none_                      | Full LiteLLM model ID (e.g. `gemini/gemini-2.5-flash-lite`, `anthropic/claude-3-5-sonnet`, `openai/gpt-4o-mini`, `groq/llama-3.1-70b-versatile`). |
| Provider API keys   | One matching your model     | _none_                      | Set the key for your chosen provider. `.env.example` lists placeholders: `GOOGLE_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `AZURE_API_KEY`, `GROQ_API_KEY`, `TOGETHER_API_KEY`, `COHERE_API_KEY`, `MISTRAL_API_KEY`, `OPENROUTER_API_KEY`. See [LiteLLM providers](https://docs.litellm.ai/docs/providers) for more. |
| `INTERVAL_SECONDS`  | No                          | `10`                        | Probe sampling interval in seconds. Controls how frequently Cymas logs a new CSV row.     |
| `CSV_PATH`          | No                          | `lantern_data.csv` in repo  | Absolute or relative path to the metrics CSV file used by the logger and API.               |

You only need **one** provider API key—the one that matches the provider prefix in `CYMAS_MODEL`.

## Running as a background service (macOS)

To keep Cymas running without an open terminal, you can use `launchd`:

1. Copy the provided `.plist` file (for example `com.cymas.monitor.plist`) into:

   ```text
   ~/Library/LaunchAgents/
   ```

2. Load the job with `launchctl`:

   ```bash
   launchctl load -w ~/Library/LaunchAgents/com.cymas.monitor.plist
   ```

3. The logger will now start automatically on boot and run in the background. You can unload it with:

   ```bash
   launchctl unload -w ~/Library/LaunchAgents/com.cymas.monitor.plist
   ```

## Running tests

```bash
pytest
```

All tests use `pytest-mock` to stub network and subprocess calls, so no real network traffic is generated during the test run.

## Contributing

We love contributions! Please see our [CONTRIBUTING.md](CONTRIBUTING.md) guide for details on how to get started, our architectural philosophy, and our coding standards.

### Areas that would benefit from contributions

- Linux and Windows probe testing  
- Additional ML model integrations (forecasting, clustering)  
- nmap-based active device scanning for more accurate device counts  
- Raspberry Pi deployment guide  

## Roadmap

- [x] probe suite
- [x] CSV logging
- [x] FastAPI backend
- [x] React dashboard
- [x] LLM diagnostics
- [ ] ML degradation prediction model
- [ ] nmap integration for accurate device counting
- [ ] Dark mode dashboard
- [ ] Multi-network support

## License

Cymas is open source software licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Acknowledgements

Cymas’s LLM integration is built on top of [LiteLLM](https://github.com/BerriAI/litellm), which provides a unified interface over multiple LLM providers.
