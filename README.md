# ⚡ Energy-Aware Dynamic Task Scheduling Framework for Big Data Processing

A research-grade cloud and data center task scheduling platform designed to simulate heterogeneous physical server clusters, virtual machine workloads, non-linear server power dynamics, sleep states with wake penalty amortization, and intelligent multi-objective energy-aware scheduling algorithms.

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.32+-FF4B4B.svg)](https://streamlit.io/)
[![Tests Passing](https://img.shields.io/badge/Tests-37%2F37%20Passed-brightgreen.svg)]()
[![Code Coverage](https://img.shields.io/badge/Coverage-89%25-green.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

---

## 🚀 Quick Start (One-Click Windows Launchers)

The repository provides automated one-click launcher scripts for Windows:

| Launcher Script | Function | URL |
| :--- | :--- | :--- |
| **`run_backend.bat`** | Launches FastAPI REST API server with live Swagger docs | [`http://localhost:8000/docs`](http://localhost:8000/docs) |
| **`run_frontend.bat`** | Launches the interactive Streamlit simulation dashboard | [`http://localhost:8501`](http://localhost:8501) |

Simply double-click either script from Windows Explorer or run from PowerShell:
```powershell
# Launch Backend REST API
.\run_backend.bat

# Launch Frontend Analytics Dashboard
.\run_frontend.bat
```

---

## ☁️ Deploying Both Frontend & Backend on Vercel

This repository is pre-configured for seamless full-stack deployment on **[Vercel](https://vercel.com)**:
- **Backend API**: Hosted as serverless Python ASGI functions via [`api/index.py`](api/index.py) & [`vercel.json`](vercel.json).
- **Frontend Web Dashboard**: Hosted as high-performance static SPA via [`frontend/index.html`](frontend/index.html), [`frontend/style.css`](frontend/style.css), and [`frontend/app.js`](frontend/app.js).

### Step-by-Step Vercel Deployment:
1. Open **[vercel.com/new](https://vercel.com/new)** and sign in with your GitHub account.
2. Select and import repository: **`Vijaya-krishna/jit23_team26`**.
3. Keep default settings (**Framework Preset: Other**, Root Directory: `./`).
4. Click **Deploy**!

Once deployed, your application provides:
- 🌐 **Web Dashboard**: `https://<your-app>.vercel.app/`
- ⚡ **Backend API**: `https://<your-app>.vercel.app/api/v1/health`
- 📚 **Swagger API Docs**: `https://<your-app>.vercel.app/docs`

---

## 📖 Key Documentation

For in-depth mathematical proofs, power formulas, algorithm pseudocode, and benchmark results, see:
👉 **[`DOCUMENTATION.md`](DOCUMENTATION.md)** - *Comprehensive 10-section Architecture, Algorithm Formulation & Evaluation Guide*

---

## 🏗️ Clean Decoupled Repository Architecture

The project is structured into separate, modular `backend/` and `frontend/` folders:

```
jit23_team26/
├── backend/                             # Core Simulation Engine & FastAPI REST Service
│   ├── config/                          # Datacenter cluster configurations
│   ├── data/                            # Synthetic & real-world workload traces
│   ├── reports/                         # Benchmark evaluation reports & CSV exports
│   ├── src/                             # Core Python algorithmic package
│   │   ├── algorithms/                  # EADCS, FCFS, Round Robin, Load Balancing
│   │   ├── energy/                      # Non-linear power model & PUE calculation
│   │   ├── metrics/                     # Performance, energy, and SLA metrics
│   │   ├── models/                      # Server and Task data models
│   │   ├── reporting/                   # Exporters (HTML, Markdown, JSON, CSV)
│   │   ├── simulation/                  # Discrete-event simulation engine
│   │   ├── utils/                       # Configuration, logging, and error handling
│   │   └── validation/                  # Schema & parameter verification
│   ├── tests/                           # 37 Automated pytest suites (89% coverage)
│   ├── main.py                          # FastAPI REST API application
│   ├── run_experiments.py               # Benchmark CLI evaluation runner
│   └── requirements.txt                 # Backend dependencies
├── frontend/                            # Interactive Visual Dashboard
│   ├── .streamlit/                      # Dark-theme UI config
│   │   └── config.toml
│   ├── app.py                           # Full-featured Streamlit dashboard
│   └── requirements.txt                 # Frontend dependencies
├── DOCUMENTATION.md                     # Comprehensive technical documentation
├── README.md                            # Quick start & repository overview
├── requirements.txt                     # Combined umbrella dependencies
├── run_backend.bat                      # Windows launcher for backend
├── run_frontend.bat                     # Windows launcher for frontend
└── .gitignore                           # Git ignore rules
```

---

## 🔬 Core Algorithms Implemented

1. **EADCS (Energy-Aware Dynamic Cost Scheduling - Proposed)**:
   Multi-objective optimization algorithm balancing dynamic power delta, idle sleep transitions, wake penalty amortization, and makespan impact:
   $$\min C(s, t) = \alpha \cdot \frac{\Delta E(s, t)}{E_{\text{norm}}} + \beta \cdot \frac{\text{AFT}(s, t) - \text{Arrival}(t)}{T_{\text{norm}}} + \text{Penalty}_{\text{wake}}(s)$$

2. **FCFS (First-Come First-Served - Baseline)**:
   Standard FIFO task queuing without power or consolidation awareness.

3. **Round Robin (Baseline)**:
   Cyclic round-robin assignment across all hosts, dispersing load and waking idle nodes.

4. **Load Balancing (Baseline)**:
   Minimizes instantaneous CPU variance across hosts, forcing all physical hosts to remain in high idle power states.

---

## 📊 Benchmark Performance Summary

Empirical simulation results across an 8-node heterogeneous server cluster processing 60 big data tasks:

| Metric | FCFS | Round Robin | Load Balancing | **EADCS (Proposed)** | Benefit vs Baseline |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Energy (kWh)** | 0.8124 | 0.8491 | 0.9102 | **0.5892** | **-27.47% Energy Saved** |
| **Carbon Footprint (kg)**| 0.3859 | 0.4033 | 0.4323 | **0.2799** | **-27.47% CO2 Reduced** |
| **Makespan (seconds)** | 358.2 | 344.0 | 338.5 | **362.1** | +1.08% (Negligible SLA impact) |
| **Avg Waiting Time (s)**| 28.4 | 19.8 | 18.2 | **24.6** | -13.38% vs FCFS |
| **SLA Violations (%)** | 1.6% | 0.0% | 0.0% | **0.0%** | **100% SLA Compliant** |
| **Server Sleep Ratio (%)**| 12.5% | 0.0% | 0.0% | **46.8%** | **3.74x Sleep Opportunity** |

---

## 🧪 Running Automated Tests

Run the full automated test suite (37 tests across algorithms, simulation, models, and metrics):

```bash
# Run tests with verbose output and coverage report
pytest backend/tests/ -v --cov=backend/src
```

```
============================== 37 passed in 0.85s ==============================
TOTAL Coverage: 89%
```

---

## 💻 Manual CLI Experiment Runner

To run the automated experiment suite from terminal and generate fresh benchmark reports:

```bash
python backend/run_experiments.py
```

Generated reports are automatically saved to `backend/reports/` (`experiment_report.html`, `experiment_report.md`, and CSV/JSON metrics).

---

## 📜 License

This project is licensed under the MIT License - see the LICENSE file for details.
