# ⚡ Energy-Aware Resource Allocation Cloud Simulator

A research-grade cloud datacenter simulation engine and interactive management platform designed to model physical server infrastructure, virtual machine (VM) allocation, synthetic big-data workloads, power consumption dynamics, PUE facility efficiency, thermal dissipation, and intelligent energy-aware scheduling algorithms.

---

## 🚀 Quick Start (One-Click Windows Launcher)

The project includes one-click batch launcher scripts for Windows:

```cmd
# Double-click run_app.bat in the project root folder to start both servers & open browser automatically!
run_app.bat
```

- **`run_app.bat`**: Frees port 8000 if occupied, launches the FastAPI backend & Vite frontend in separate windows, and opens your browser to `http://localhost:5173/`.
- **`run_backend.bat`**: Launches only the FastAPI backend server (`http://127.0.0.1:8000`).
- **`run_frontend.bat`**: Launches only the Vite React frontend server (`http://localhost:5173`).

---

## 🎯 Overview

Modern cloud datacenters consume enormous amounts of electrical energy. A significant portion of this power is wasted due to server idle draw, resource fragmentation, and sub-optimal workload placement.

This platform simulates a real-time cloud datacenter environment allowing researchers and system administrators to:
1. **Provision & Manage Physical Servers** (CPU, RAM, Storage, Link Bandwidth, Power States: `ACTIVE`, `SLEEP`, `OFF`).
2. **Deploy & Decommission Virtual Machines** dynamically across physical hosts.
3. **Queue Synthetic Big-Data Workloads** with SLA deadlines and priorities (`HIGH`, `MEDIUM`, `LOW`).
4. **Step Clock Ticks** to simulate real-time thermal build-up, IT power draw, cooling overheads, and PUE.
5. **Compare Resource Schedulers**:
   - **Round-Robin**: Circular baseline allocation.
   - **Random**: Uniform stochastic baseline.
   - **Energy-Aware (BFD)**: Power-Aware Best-Fit Decreasing algorithm that minimizes marginal watt increases and consolidates idle servers into `SLEEP` state.
   - **AI/ML Predictive Model**: Multi-objective feature scoring engine balancing power slope, thermal headroom, and optimal 75% load targets.
6. **Export Executive Reports**: Download raw time-series telemetry as **CSV** or full simulation snapshots as **JSON**.

---

## 🏗 System Architecture & Modules

The system is structured as a decoupled full-stack web application following SOLID software design principles.

```
                  ┌─────────────────────────────────────────┐
                  │          React Frontend UI              │
                  │   (Vite + TypeScript + Recharts)        │
                  └────────────────────┬────────────────────┘
                                       │ HTTP / REST (JWT Auth)
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │           FastAPI Backend               │
                  │  (Controllers, Services, Repositories)  │
                  └────────────────────┬────────────────────┘
                                       │ In-Memory Sync
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │       Simulation Core Engine            │
                  │ (Hosts, VMs, Schedulers, Power Models)  │
                  └────────────────────┬────────────────────┘
                                       │ Persistence
                                       ▼
                  ┌─────────────────────────────────────────┐
                  │           SQLite Database               │
                  │ (Hosts, VMs, Telemetry & History Logs)  │
                  └─────────────────────────────────────────┘
```

### Module Breakdown

| Module | Feature | Description |
|---|---|---|
| **Module 1** | **Authentication & Security** | JWT-based role authentication (`admin`, `operator`) protecting simulation endpoints. |
| **Module 2** | **Physical Infrastructure** | Models physical hosts with core count, frequency, RAM, storage, network interface, and power state controls. |
| **Module 3** | **Virtual Machines** | Manages VM allocation, capacity checks, resource reservation, and decommissioning. |
| **Module 4** | **Workload Generator & Queue** | Generates synthetic cloud tasks with CPU/RAM footprints, execution ticks, and SLA breach deadlines. |
| **Module 5** | **Simulation Clock Loop** | Step-by-step clock ticks updating task progress, host temperatures, and aggregated telemetry logs. |
| **Module 6** | **Power & Thermal Models** | Implements Linear ($P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \cdot u$), Square, and Cube power curves; PUE calculation and carbon emission metrics ($0.4\text{ kg CO}_2/\text{kWh}$). |
| **Module 7** | **Traditional Baseline Schedulers** | Baseline `Round-Robin` and `Random` VM allocation strategies. |
| **Module 8** | **Energy-Aware Scheduler** | Power-Aware Best-Fit Decreasing (BFD) placement and VM consolidation pass (sleep idle hosts). |
| **Module 9** | **AI/ML Predictive Model** | Multi-objective scoring algorithm evaluating power slope, thermal headroom, and optimal 75% load target. |
| **Module 10** | **Interactive Analytics** | Real-time time-series telemetry charts, host thermal breakdown, and power donut visualizations in Recharts. |
| **Module 11** | **Audit Logging** | Granular history log repository recording per-tick global and per-host metrics. |
| **Module 12** | **Glassmorphic UI Polish** | Modern dark-mode UI built with TailwindCSS, Framer Motion micro-animations, and glowing indicators. |
| **Module 13** | **Reports Exporter** | Executive summary cards and 1-click **CSV** / **JSON** telemetry data downloaders. |

---

## 🛠 Tech Stack

### Backend
- **Python 3.12**
- **FastAPI**: High-performance RESTful API framework.
- **SQLAlchemy 2.0**: ORM for SQLite database persistence.
- **Pytest**: Comprehensive test suite (63 unit tests).
- **PyJWT & Passlib / bcrypt**: Secure password hashing and token validation.

### Frontend
- **React 18 (Vite + TypeScript)**
- **TailwindCSS**: Premium dark-mode glassmorphic styling system.
- **Recharts**: Time-series charts, area graphs, and power donut charts.
- **Framer Motion**: Smooth page transitions and modal micro-animations.
- **Lucide Icons**: Clean iconography.

---

## 💻 Manual Setup & Execution

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+** & **npm** installed

---

### 1. Run the Backend API Server

```bash
# 1. Activate Python virtual environment
backend\.venv\Scripts\activate   # On Windows
# source backend/.venv/bin/activate  # On Linux/macOS

# 2. Install requirements (if needed)
pip install -r backend/requirements.txt

# 3. Run the FastAPI dev server (with hot reload)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: `http://localhost:8000/api`
- **Swagger Interactive Docs**: `http://localhost:8000/docs`

---

### 2. Run the Frontend UI

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Install dependencies (if needed)
npm install

# 3. Launch Vite development server
npm run dev
```

Open your browser and navigate to:
```
http://localhost:5173/
```

---

## 🔑 Default Login Credentials

Upon startup, the database automatically seeds a default administrator account:

| Field | Value |
|---|---|
| **Username** | `admin` |
| **Password** | `AdminPass123!` |
| **Role** | `admin` |

---

## 🧪 Running Automated Unit Tests

To run the complete Python backend test suite (63 unit tests):

```bash
# From project root directory
backend\.venv\Scripts\python.exe -m pytest backend\tests
```

To run TypeScript frontend type checking:

```bash
cd frontend
npx tsc --noEmit
```

---

## 📊 How the Simulation Works (Step-by-Step)

1. **Log in** with `admin` / `AdminPass123!`.
2. **View Physical Servers**: See live server nodes, CPU cores, memory utilization, operating temperature, and active power state (`ACTIVE`, `SLEEP`, `OFF`).
3. **Deploy Virtual Machines**: Click **`+ Deploy VM`** on an active host node.
4. **Select Scheduler Strategy**: Use the top control card on the Data Center tab to select:
   - `Round-Robin`
   - `Random`
   - `Energy-Aware (BFD)` *(Recommended for lowest power draw)*
   - `AI/ML Predictive`
5. **Queue Workload Tasks**: Click `+10 Tasks` or `+50 Tasks` to add synthetic workloads to the waiting queue.
6. **Step Clock Ticks**: Click `▶ Clock Step (Tick)` to advance the simulation time step:
   - `WAITING` tasks get dispatched to active deployed VMs (`Target VM: VM #X`) and enter `RUNNING` status.
   - Execution times count down to zero tick by tick until task becomes `COMPLETED`.
   - If clock ticks pass a task's deadline tick before completion, it triggers an SLA breach (`FAILED`).
7. **Analyze Metrics**: Switch to the **Analytics** tab to inspect time-series charts, PUE gauges, energy breakdown, and carbon savings.
8. **Export Reports**: Click **Export CSV Telemetry** or **Export JSON Snapshot** to download report files.

---

## 🔗 Repository

- **GitHub Repository**: [https://github.com/Vijaya-krishna/jit23_026.git](https://github.com/Vijaya-krishna/jit23_026.git)
