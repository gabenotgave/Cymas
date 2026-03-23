# Contributing to LANtern

First off, thank you for considering contributing to LANtern! It's people like you who make open-source projects such a great place to learn, inspire, and create.

This guide will help you get started with contributing to LANtern. Whether you're fixing a bug, adding a new probe, or improving the dashboard, we appreciate your help.

---

## Code of Conduct

By participating in this project, you agree to abide by our Code of Conduct. Please be respectful and professional in all interactions.

## Getting Started

### Prerequisites

- **Python 3.10+**
- **Node.js 18+**
- **npm** (usually comes with Node.js)

### Local Development Setup

1.  **Clone the Repository**
    ```bash
    git clone https://github.com/gabenotgave/LANtern.git
    cd LANtern
    ```

2.  **Backend Setup**
    Create and activate a virtual environment, then install dependencies:
    ```bash
    python3 -m venv .venv
    source .venv/bin/activate  # On Windows use `.venv\Scripts\activate`
    pip install -r requirements.txt
    ```

3.  **Frontend Setup**
    Install dashboard dependencies:
    ```bash
    cd dashboard
    npm install
    cd ..
    ```

4.  **Environment Configuration**
    Copy the example environment file and set your API keys:
    ```bash
    cp .env.example .env
    ```
    Edit `.env` to include your `LANTERN_MODEL` and the corresponding provider key (e.g., `GOOGLE_API_KEY`).

## Architecture & Philosophy

LANtern is built on a **decoupled architecture**:

1.  **The System Monitor (`probes/`)**: A background process that runs platform-specific probes. The main entry point is `probes/main.py` and configuration is in `probes/config.py`.
2.  **The Persistence Layer (`lantern_data.csv`)**: A flat CSV file acting as the singular source of truth.
3.  **The Backend API (`api/`)**: A FastAPI instance that reads the CSV and provides endpoints for the dashboard and AI diagnostics.
4.  **The Frontend (`dashboard/`)**: A React/Vite application for data visualization.

**Key Rule**: Never couple the frontend directly to the system probes, and never couple the background monitor to FastAPI logic. The CSV links everything.

## Contribution Workflow

1.  **Find an Issue**: Check the [GitHub Issues](https://github.com/gabenotgave/LANtern/issues) for something to work on. If you want to propose a new feature, open an issue first.
2.  **Fork and Branch**: Fork the repo and create a branch for your work:
    -   `feature/your-feature-name` for new features.
    -   `fix/your-fix-name` for bug fixes.
3.  **Implement and Test**: Write your code and ensure all tests pass.
4.  **Submit a Pull Request**: Provide a clear description of the changes and why they are needed.

## Coding Guidelines

### Backend (Python)
- Follow **PEP 8** style guidelines.
- Use type hints wherever possible.
- Keep the `probes/` cross-platform. Ensure changes work on macOS, Linux, and Windows.
    - If you cannot test on a specific platform, please create a linked GitHub issue to request testing.

### Frontend (React)
- Use functional components and hooks.
- Styling should be done with **Tailwind CSS**.
- Keep components focused and reusable.

### Testing
- We use `pytest` and `pytest-mock`.
- **Important**: Do not generate actual network traffic in tests. Always stub subprocess and network calls.
- Run tests before submitting:
  ```bash
  pytest
  ```

## Areas for Contribution

We are especially looking for help in:
- **Cross-platform testing**: Verifying and improving probes on Linux and Windows.
- **New Probes**: Adding more ways to measure network health (e.g., nmap integration).
- **ML Integrations**: Forecasting and anomaly detection improvements.
- **Documentation**: Improving guides and adding deployment examples (e.g., Raspberry Pi).

## Questions?

If you have questions, feel free to open a discussion or an issue. Happy coding!
