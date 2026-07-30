# ⚡ Energy-Aware Resource Allocation Cloud Simulator

## 📌 Project Overview

The **Energy-Aware Resource Allocation Cloud Simulator** is a full-stack, research-grade cloud datacenter simulation engine. It models physical server hardware, virtual machine (VM) allocation, synthetic big-data workloads, IT power draw dynamics, facility cooling overheads (PUE), thermal dissipation, carbon emissions, and intelligent energy-aware scheduling algorithms.

Modern cloud datacenters consume massive amounts of electrical power. A primary cause of energy waste is server idle power draw, hardware resource fragmentation, and sub-optimal workload placement. This project enables system administrators and researchers to benchmark and compare traditional allocation methods against energy-aware and AI-driven predictive schedulers.

---

## 🏗️ System Architecture

The application is built with a decoupled architecture following modern software design principles:

```
┌─────────────────────────────────────────────────────────┐
│              React Frontend UI (Vite + TS)              │
│      (Data Center Dashboard, Analytics, Real-time)      │
└────────────────────────────┬────────────────────────────┘
                             │ HTTP / REST (JWT Auth)
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 FastAPI Backend Server                  │
│       (Controllers, Services, Repositories, Schemas)    │
└────────────────────────────┬────────────────────────────┘
                             │ In-Memory Synchronization
                             ▼
┌─────────────────────────────────────────────────────────┐
│                 Simulation Core Engine                  │
│   (Physical Hosts, VMs, Workload Queue, Schedulers)     │
└────────────────────────────┬────────────────────────────┘
                             │ Persistence
                             ▼
┌─────────────────────────────────────────────────────────┐
│                    SQLite Database                      │
│ (Servers, VMs, Tasks, Simulation State, Telemetry Logs) │
└────────────────────────────┬────────────────────────────┘
```

---

## ⚙️ Core Concepts & Mathematical Models

### 1. Physical Server Hosts (`PhysicalHost`)
Each physical server node models physical computing hardware:
- **Compute & Memory**: CPU cores, frequency (GHz), RAM (MB), Storage (GB), Bandwidth (Mbps).
- **Power States**:
  - `ACTIVE`: Server is powered on, processing workloads, consuming baseline idle + active dynamic power.
  - `SLEEP`: Server is in low-power standby mode ($\approx 5\text{ W}$ standby draw).
  - `OFF`: Server is completely powered off ($0\text{ W}$ draw).

### 2. Power Consumption Models
Power is calculated dynamically based on CPU utilization ($u \in [0, 1]$):
- **Linear Model** (Default):
  $$P(u) = P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \cdot u$$
- **Square Model**:
  $$P(u) = P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \cdot u^2$$
- **Cube Model**:
  $$P(u) = P_{\text{idle}} + (P_{\text{peak}} - P_{\text{idle}}) \cdot u^3$$

### 3. PUE & Facility Infrastructure
- **PUE (Power Usage Effectiveness)**:
  $$\text{PUE} = \frac{\text{Total Facility Power}}{\text{IT Equipment Power}} = \frac{P_{\text{IT}} + P_{\text{cooling}}}{P_{\text{IT}}}$$
- Default cooling overhead is $35\%$ ($P_{\text{cooling}} = 0.35 \cdot P_{\text{IT}}$), giving a baseline PUE of $1.35$.
- **Carbon Emissions**: Estimated at $0.4\text{ kg CO}_2 / \text{kWh}$.
- **Electricity Cost**: Estimated at $\$0.12 / \text{kWh}$.

---

## 🧠 VM Assignment & Resource Schedulers

The simulator features **4 Resource Allocation Schedulers** that govern how Virtual Machines (VMs) are mapped to Physical Hosts:

### 1. Round-Robin (`RoundRobinScheduler`)
- Rotates VM placement across physical host nodes in circular order.
- Simple baseline; ignores server power draw and resource utilization efficiency.

### 2. Random (`RandomScheduler`)
- Stochastic baseline; randomly picks an active host with sufficient capacity.

### 3. Energy-Aware Best-Fit Decreasing (`EnergyAwareScheduler`)
- Sorts VMs by resource demand in descending order (largest VMs first).
- Places each VM on the host that yields the **minimal incremental power increase** ($\Delta P$).
- **Dynamic Consolidation**: Automatically migrates VMs away from lightly loaded hosts and transitions emptied hosts into `SLEEP` state to eliminate idle power draw.

### 4. AI/ML Predictive Model (`MLScheduler`)
- Evaluates candidate hosts using a multi-objective feature scoring function:
  $$\text{Score} = w_{\text{power}} \cdot S_{\text{power}} + w_{\text{thermal}} \cdot S_{\text{thermal}} + w_{\text{load}} \cdot S_{\text{load}}$$
  - $S_{\text{power}}$: Normalized power efficiency score.
  - $S_{\text{thermal}}$: Temperature headroom score ($22^\circ\text{C}$ to $80^\circ\text{C}$).
  - $S_{\text{load}}$: Target load score (penalizes deviation from optimal $75\%$ CPU utilization).

---

## 🔄 Task Lifecycle & Execution Flow

Workload tasks represent synthetic big-data processing payloads queued for execution.

```
       ┌────────────────┐
       │   WAITING      │ (Generated in task queue)
       └───────┬────────┘
               │ Clock Step (Dispatched to active VM)
               ▼
       ┌────────────────┐
       │   RUNNING      │ (Decrements execution_time each tick)
       └───┬────────┬───┘
           │        │
Execution  │        │ Exceeds deadline tick
ticks = 0  │        │ (SLA Breach)
           ▼        ▼
┌──────────────┐ ┌──────────────┐
│  COMPLETED   │ │   FAILED     │
└──────────────┘ └──────────────┘
```

1. **Generation (`WAITING`)**:
   - Tasks specify CPU cores, RAM, storage, network bandwidth, execution time (in ticks), priority (`HIGH`, `MEDIUM`, `LOW`), and a **Deadline Tick**.
2. **Dispatch & Assignment (`RUNNING`)**:
   - On each clock step (`▶ Clock Step (Tick)`), the task dispatcher scans for active VMs deployed on active physical hosts.
   - `WAITING` tasks are assigned to target VMs (`Target VM: VM #X`), entering the **`RUNNING`** state.
3. **Execution**:
   - Each clock tick decrements `execution_time` by 1 tick for all `RUNNING` tasks.
4. **Completion (`COMPLETED`)**:
   - When `execution_time` reaches 0 ticks before breaching its deadline, the task succeeds, releases VM capacity, and marks as **`COMPLETED`**.
5. **SLA Failure (`FAILED`)**:
   - If the global simulation tick counter advances past a task's **Deadline Tick** before completion, the task triggers an SLA Breach and turns **`FAILED`**.

---

## 🛠️ Step-by-Step Operating Guide

### 1. Launch the Application
- **Backend API**: Running at [http://localhost:8000](http://localhost:8000) (Swagger Docs: [http://localhost:8000/docs](http://localhost:8000/docs))
- **Frontend UI**: Running at [http://localhost:5173/](http://localhost:5173/)

### 2. Log In
- **Username**: `admin`
- **Password**: `AdminPass123!`

### 3. Workflow to Run a Full Simulation:
1. **Inspect Host Nodes**: View physical servers, CPU/RAM utilization, temperature, and power states.
2. **Deploy Virtual Machines**: Click **`+ Deploy VM`** on any active server node to provision virtual machine capacity.
3. **Select Scheduler Strategy**: Choose between `Round-Robin`, `Random`, `Energy-Aware (BFD)`, or `AI/ML Predictive`.
4. **Queue Workload Tasks**: Click **`+10 Tasks`** or **`+50 Tasks`** to generate synthetic batch processing tasks.
5. **Step Clock Ticks**: Click **`▶ Clock Step (Tick)`** to advance the simulation clock step-by-step:
   - Tasks transition from `WAITING` $\rightarrow$ `RUNNING` on target VMs $\rightarrow$ `COMPLETED`.
   - Power consumption, energy (kWh), and thermal updates adjust live.
6. **Analytics & Reports**: Switch to the **Analytics** page to view time-series graphs, PUE gauges, and export CSV/JSON telemetry logs.
