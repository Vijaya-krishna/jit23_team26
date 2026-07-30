# ⚡ Energy-Aware Resource Allocation Cloud Simulator

A research-grade cloud datacenter simulation engine and interactive management platform designed to model physical server infrastructure, virtual machine (VM) allocation, synthetic big-data workloads, power consumption dynamics, PUE facility efficiency, thermal dissipation, and intelligent energy-aware scheduling algorithms.

---

## 🎯 Overview

Modern cloud datacenters consume enormous amounts of electrical energy. A significant portion of this power is wasted due to server idle draw, fragmentation, and sub-optimal workload scheduling.

This platform simulates a real-time cloud data center environment allowing researchers and system administrators to:
1. **Provision & Manage Physical Servers** (CPU, RAM, Storage, Link Bandwidth, Power States: `ACTIVE`, `SLEEP`, `OFF`).
2. **Deploy & Decommission Virtual Machines** dynamically across physical hosts.
3. **Queue Synthetic Big-Data Workloads** with SLA deadlines and priorities.
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
                                       │ HTTP / REST
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
| **Module 6** | **Power & Thermal Models** | Implements Linear ($P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \cdot u$), Square, and Cube power curves; PUE calculation and carbon emission metrics ($0.475\text{ kg CO}_2/\text{kWh}$). |
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
- **PyJWT & Passlib**: Secure password hashing and token validation.

### Frontend
- **React 18 (Vite + TypeScript)**
- **TailwindCSS**: Premium dark-mode glassmorphic styling system.
- **Recharts**: Time-series charts, area graphs, and power donut charts.
- **Framer Motion**: Smooth page transitions and modal micro-animations.
- **Lucide Icons**: Clean iconography.

---

## 🚀 Getting Started

### Prerequisites
- **Python 3.10+** installed
- **Node.js 18+** & **npm** installed

---

### 1. Run the Backend API Server

Open a terminal in the project root directory:

```bash
# 1. Activate Python virtual environment
backend\.venv\Scripts\activate   # On Windows
# source backend/.venv/bin/activate  # On Linux/macOS

# 2. Run the FastAPI dev server (with hot reload)
python -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API Base URL**: `http://localhost:8000/api`
- **Swagger Interactive Docs**: `http://localhost:8000/docs`

---

### 2. Run the Frontend UI

Open a second terminal window in the `frontend` folder:

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
3. **Select Scheduler Strategy**: Use the top control card on the Data Center tab to select:
   - `Round-Robin`
   - `Random`
   - `Energy-Aware (BFD)` *(Recommended for lowest power draw)*
   - `AI/ML Predictive`
4. **Queue Workload Tasks**: Click `+10 Tasks` or `+50 Tasks` to add synthetic workloads to the waiting queue.
5. **Step Clock Ticks**: Click `▶ Clock Step (Tick)` to advance the simulation time step. Watch VM task execution times count down, tasks complete, and heat/power draw adjust.
6. **Consolidate VMs**: Click `Consolidate VMs` to pack VMs onto fewer servers and send idle servers to `SLEEP`.
7. **Analyze Metrics**: Switch to the **Analytics** tab to inspect time-series charts, PUE gauges, energy breakdown, and carbon savings.
8. **Export Reports**: Click **Export CSV Telemetry** or **Export JSON Snapshot** to download report files.
