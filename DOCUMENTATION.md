# Energy-Aware Dynamic Task Scheduling Framework for Big Data Processing
## Comprehensive Technical & Architectural Documentation

---

## 1. Executive Summary & Problem Formulation

Modern hyperscale and enterprise cloud data centers hosting big data processing frameworks (such as Apache Spark, Hadoop MapReduce, and Flink) consume immense amounts of electrical power, resulting in high operational expenditures and significant carbon footprints. Traditional task schedulers—such as **First-Come First-Served (FCFS)**, **Round Robin (RR)**, and naive **Load Balancing (LB)**—focus exclusively on throughput, queue fairness, or load distribution. Consequently, they leave physical servers idling at 60–70% of maximum power draw without transitioning unutilized nodes into low-power sleep states, or they introduce severe SLA/deadline violations through uncoordinated consolidation.

This framework implements an **Energy-Aware Dynamic Cost Scheduling (EADCS)** architecture coupled with an event-driven discrete simulation engine, a non-linear power consumption model, sleep-state power management with wake penalty amortization, and a full-stack REST API and interactive dashboard.

```
                              ┌────────────────────────────────────────┐
                              │           Big Data Workload            │
                              │   (Tasks: CPU, RAM, Duration, SLA)     │
                              └──────────────────┬─────────────────────┘
                                                 │
                                                 ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                            EADCS Multi-Objective Scheduler Engine                            │
│                                                                                              │
│   ┌───────────────────────────┐   ┌────────────────────────────┐   ┌─────────────────────┐   │
│   │   Dynamic Power Delta     │   │   Makespan & SLA Impact    │   │ Wake Cost Penalty   │   │
│   │   ΔE(s, t) = ∫ P(u) dt    │ + │   Turnaround & Queuing AFT │ + │ Amortization Model  │   │
│   └─────────────┬─────────────┘   └─────────────┬──────────────┘   └──────────┬──────────┘   │
│                 │                               │                             │              │
│                 └───────────────────────┬───────┴─────────────────────────────┘              │
│                                         ▼                                                    │
│                        Cost Objective: Min C(s, t) = α·E_norm + β·T_norm + Penalty           │
└─────────────────────────────────────────┬────────────────────────────────────────────────────┘
                                          │
                                          ▼
┌──────────────────────────────────────────────────────────────────────────────────────────────┐
│                          Heterogeneous Server Infrastructure Cluster                         │
│                                                                                              │
│   ┌────────────────────┐   ┌────────────────────┐   ┌────────────────────┐                   │
│   │  Server 1 (Active) │   │  Server 2 (Active) │   │  Server 3 (Sleep)  │   ...             │
│   │  [■■■■■■□□] 75%    │   │  [■■■■□□□□] 50%    │   │  [ZZZZZZZZ] 10W    │                   │
│   └────────────────────┘   └────────────────────┘   └────────────────────┘                   │
└──────────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. System Architecture & Repository Structure

The framework is decoupled into a modular **Backend** (core simulation engine, mathematical models, algorithms, and FastAPI service) and an interactive **Frontend** (Streamlit dashboard and Plotly analytics).

```
jit23_team26/
├── api/                                 # Vercel Serverless Function Directory
│   └── index.py                         # Vercel ASGI serverless entrypoint
├── backend/                             # Core Engine & REST API Service
│   ├── config/                          # Cluster & simulation configuration profiles
│   │   └── default_config.json
│   ├── data/                            # Standardized synthetic & empirical workload traces
│   │   ├── bursty_workload.csv          # Spike-heavy arrival workload
│   │   ├── low_load_workload.csv        # Low-utilization sleep-opportunity workload
│   │   ├── medium_load_workload.csv     # Mixed big data batch workload
│   │   └── sample_workload.csv          # Quick smoke test workload
│   ├── reports/                         # Benchmark datasets and auto-generated reports
│   │   ├── bursty_workload_metrics.csv / .json
│   │   ├── low_load_workload_metrics.csv / .json
│   │   ├── medium_load_workload_metrics.csv / .json
│   │   ├── experiment_report.html       # Research report with charts & tables
│   │   └── experiment_report.md
│   ├── src/                             # Production Python Package
│   │   ├── algorithms/                  # Schedulers: EADCS, FCFS, Round Robin, Load Balancing
│   │   ├── energy/                      # Non-linear power model & PUE energy calculator
│   │   ├── metrics/                     # Performance, energy, carbon, and SLA evaluators
│   │   ├── models/                      # Server and Task data models & state machines
│   │   ├── reporting/                   # Exporter & multi-format report generator
│   │   ├── simulation/                  # Discrete-event engine, events, and workload generator
│   │   ├── utils/                       # Configuration loaders, exceptions, and logging
│   │   └── validation/                  # Schema & constraint validators
│   ├── tests/                           # 37 Automated pytest test suites (89% coverage)
│   ├── main.py                          # FastAPI REST API with Swagger documentation
│   ├── run_experiments.py               # CLI benchmark evaluation runner
│   └── requirements.txt                 # Backend Python dependencies
├── frontend/                            # Interactive UI & Analytics Dashboard
│   ├── .streamlit/                      # Dark-theme visual tokens & layout config
│   │   └── config.toml
│   ├── index.html                       # Vercel-ready modern responsive web dashboard
│   ├── style.css                        # Glassmorphism dark mode stylesheet
│   ├── app.js                           # Plotly analytics & live API connector
│   ├── app.py                           # Full-featured Streamlit simulation workbench
│   └── requirements.txt                 # Frontend Python dependencies
├── vercel.json                          # Vercel Serverless & Static routing configuration
├── DOCUMENTATION.md                     # Comprehensive technical documentation (this document)
├── README.md                            # Quick-start guide & repository overview
├── requirements.txt                     # Unified umbrella requirements
├── run_backend.bat                      # 1-click Windows launcher for FastAPI server
├── run_frontend.bat                     # 1-click Windows launcher for Streamlit dashboard
└── .gitignore                           # Excludes environments, caches, and local files
```

---

## 3. Mathematical Models & Formulations

### 3.1 Non-Linear Server Power Model

Physical server power does not scale strictly linearly with CPU utilization ($u$). Real-world CMOS hardware characteristics exhibit dynamic voltage and frequency scaling (DVFS) curve deviations modeled by an exponential factor $\alpha \in [1.2, 1.6]$:

$$P(u) = P_{\text{idle}} + (P_{\text{max}} - P_{\text{idle}}) \cdot u^\alpha$$

Where:
- $u \in [0.0, 1.0]$: Instantaneous processor utilization:
  $$u(t) = \frac{\sum_{i \in \text{RunningTasks}} \text{CPU}_i}{\text{TotalCPU}}$$
- $P_{\text{idle}}$: Static baseload power draw when server is powered on but processing zero tasks (typically 30–45% of $P_{\text{max}}$).
- $P_{\text{max}}$: Peak power draw under 100% computational load.
- $\alpha$: Hardware curvature exponent (default: $1.4$).

### 3.2 Dynamic Energy Integration & Facility Efficiency (PUE)

Total cluster energy is integrated over the execution timeline across all servers $S$, scaled by the facility **Power Usage Effectiveness (PUE)**:

$$E_{\text{total}} = \text{PUE} \cdot \sum_{s \in S} \int_{0}^{\text{Makespan}} P_s(u_s(t)) \, dt$$

Where:
- $\text{PUE} \ge 1.0$ (typically $1.2$ in modern high-efficiency datacenters) accounts for cooling, lighting, and power distribution losses.
- Carbon emission equivalents are calculated using regional carbon grid intensity factors:
  $$\text{Carbon} (\text{kg CO}_2\text{e}) = E_{\text{total}} (\text{kWh}) \times I_{\text{grid}} \quad (I_{\text{grid}} \approx 0.475 \, \text{kg/kWh})$$

### 3.3 Server Sleep State & Wake Penalty Amortization

Servers enter a low-power deep sleep mode ($P_{\text{sleep}} \approx 10\text{ W}$) when idle for longer than the idle sleep threshold ($\tau_{\text{idle}} = 10\text{ s}$). 

Transitioning a server from sleep back to active requires a wake duration ($T_{\text{wake}} = 5\text{ s}$) at peak power ($P_{\text{wake}} = 350\text{ W}$), consuming energy:
$$E_{\text{wake}} = P_{\text{wake}} \times T_{\text{wake}} = 350\text{ W} \times 5\text{ s} = 1750\text{ Joules}$$

To prevent harmful rapid cycling (thrashing), the scheduler only transitions a node to sleep if the projected idle period exceeds the **Break-Even Time ($T_{\text{break-even}}$)**:
$$T_{\text{break-even}} = \frac{E_{\text{wake}}}{P_{\text{idle}} - P_{\text{sleep}}}$$

### 3.4 EADCS Multi-Objective Cost Function

For each pending task $t$, the **Energy-Aware Dynamic Cost Scheduler (EADCS)** calculates a heuristic allocation cost $C(s, t)$ for every candidate server $s$ that satisfies resource constraints ($\text{CPU}_{\text{avail}} \ge \text{CPU}_t$, $\text{RAM}_{\text{avail}} \ge \text{RAM}_t$):

$$C(s, t) = \alpha \cdot \frac{\Delta E(s, t)}{E_{\text{norm}}} + \beta \cdot \frac{\text{AFT}(s, t) - \text{Arrival}(t)}{T_{\text{norm}}} + \text{Penalty}_{\text{wake}}(s)$$

Where:
- $\Delta E(s, t)$: Marginal energy increase resulting from placing task $t$ on server $s$:
  $$\Delta E(s, t) = \int_{t_{\text{start}}}^{t_{\text{finish}}} \left[ P_s(u_{\text{new}}(t)) - P_s(u_{\text{current}}(t)) \right] dt$$
- $\text{AFT}(s, t)$: Actual Finish Time of task $t$ on server $s$.
- $\alpha \in [0, 1]$ and $\beta \in [0, 1]$: User-configurable optimization weights with $\alpha + \beta = 1.0$ (e.g., $\alpha = 0.6$ for energy priority, $\beta = 0.4$ for SLA/makespan balance).
- $\text{Penalty}_{\text{wake}}(s)$: Activation penalty applied if server $s$ is currently in `SLEEP` state, discouraging waking cold servers when already active servers can accommodate the load.

The scheduler assigns task $t$ to:
$$s^* = \arg\min_{s \in S_{\text{valid}}} C(s, t)$$

---

## 4. Scheduling Algorithms Compared

| Algorithm | Paradigm | Energy Consideration | Consolidation Strategy | SLA / Makespan Awareness |
| :--- | :--- | :--- | :--- | :--- |
| **EADCS (Proposed)** | Multi-Objective Dynamic Cost | **Non-linear derivative $P(u)$ minimization** | Dynamic packing into active nodes; sleep preservation | Priority weighting & deadline-aware slack analysis |
| **FCFS** | Sequential FIFO Queue | None | First available server with sufficient resources | None (arrival order only) |
| **Round Robin (RR)** | Cyclic Permutation | None | Disperses load evenly across all hosts, waking all idle nodes | None (cyclic) |
| **Load Balancing (LB)** | Greedy Utilization Balancing | Negative (maximizes idle power on all hosts) | Distributes tasks to host with lowest CPU utilization | Minimal (utilization balance) |

---

## 5. Discrete-Event Simulation Engine

The core simulation is built upon a deterministic **Discrete-Event Simulation (DES)** paradigm:
1. **Clock Progression:** The simulation time advances asynchronously to the timestamp of the next chronological event in the priority queue (`heapq`).
2. **Event Types:**
   - `TASK_ARRIVAL`: A new big data task arrives at the cluster. Placed into the admission queue.
   - `TASK_SCHEDULE`: Scheduler evaluates candidate servers using $C(s, t)$ and dispatches tasks.
   - `TASK_COMPLETION`: A running task finishes. Resources (CPU, RAM) are released back to the host.
   - `SERVER_WAKE`: A server finishes its wake-up phase and transitions from `WAKING` to `ACTIVE`.
   - `SERVER_SLEEP`: A server exceeding idle timeout transitions from `IDLE` to `SLEEP`.
3. **State Machine Integrity:**
   - **Task Lifecycle:** `PENDING` $\to$ `SCHEDULED` $\to$ `RUNNING` $\to$ `COMPLETED` (or `FAILED` if deadline expires without scheduling).
   - **Server Lifecycle:** `ACTIVE` $\rightleftharpoons$ `IDLE` $\to$ `SLEEP` $\to$ `WAKING` $\to$ `ACTIVE`.

---

## 6. Experimental Benchmark Evaluation

Evaluations conducted across **Low**, **Medium**, and **Bursty** big data workloads on an 8-node heterogeneous server cluster (Dual-socket Xeon & AMD EPYC models):

### Comparative Benchmark Results (Medium Workload, 60 Tasks)

| Metric | FCFS | Round Robin | Load Balancing | **EADCS (Proposed)** | Improvement vs FCFS |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Total Energy (kWh)** | 0.8124 | 0.8491 | 0.9102 | **0.5892** | **-27.47%** |
| **Carbon Footprint (kg)** | 0.3859 | 0.4033 | 0.4323 | **0.2799** | **-27.47%** |
| **Makespan (seconds)** | 358.2 | 344.0 | 338.5 | **362.1** | +1.08% (Within 2% SLA) |
| **Avg Waiting Time (s)** | 28.4 | 19.8 | 18.2 | **24.6** | -13.38% |
| **SLA Violations (%)** | 1.6% | 0.0% | 0.0% | **0.0%** | **100% SLA Compliant** |
| **Server Sleep Ratio (%)**| 12.5% | 0.0% | 0.0% | **46.8%** | **3.74x Sleep Opportunity** |

### Key Findings:
1. **Load Balancing has the highest energy consumption:** By spreading tasks evenly across all 8 nodes, it forces every node to remain in active power mode ($P_{\text{idle}} = 95\text{--}140\text{ W}$), eliminating sleep opportunities.
2. **EADCS achieves 25–35% energy savings:** By consolidating tasks into an optimal active subset of power-efficient servers and transitioning idle servers to sleep state (10W), baseload waste is slashed without violating deadline bounds.

---

## 7. Backend REST API Specifications

The FastAPI backend server (`backend/main.py`) exposes complete programmatic endpoints with automatic interactive OpenAPI / Swagger documentation at `http://localhost:8000/docs`:

### Endpoints Overview

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/` | API service status and supported algorithms |
| `GET` | `/api/v1/health` | Service health and engine readiness probe |
| `GET` | `/api/v1/algorithms` | List metadata and parameters for all 4 schedulers |
| `GET` | `/api/v1/workloads` | Retrieve available workload categories and task specs |
| `POST` | `/api/v1/simulate` | Execute discrete simulation with custom servers and tasks |
| `POST` | `/api/v1/benchmark` | Run comparative multi-algorithm benchmark on a workload |

### Example Request (`POST /api/v1/simulate`)
```json
{
  "algorithm": "eadcs",
  "alpha_energy_weight": 0.6,
  "beta_makespan_weight": 0.4,
  "workload_type": "medium",
  "workload_tasks_count": 60
}
```

---

## 8. Frontend Dashboard Features

The Streamlit dashboard (`frontend/app.py`) provides an intuitive GUI with:
1. **Overview & Real-Time KPIs:** Live metric cards showing Total Energy (kWh), Energy Savings (%), Carbon Reduction (kg), Makespan, and SLA Compliance.
2. **Algorithm Comparison Matrix:** Side-by-side grouped bar charts for energy, makespan, waiting times, and server utilization.
3. **Cluster Infrastructure Topology:** Interactive visual representation of each physical server showing current state (`ACTIVE`, `IDLE`, `SLEEP`), CPU gauges, RAM meters, and power draw.
4. **Timeline & Gantt Chart:** High-resolution scheduling timeline displaying task start/completion times across all cluster nodes.
5. **Dynamic Simulation Sandbox:** Real-time parameter sliders allowing users to adjust $\alpha$ (energy priority) vs $\beta$ (makespan priority), inject bursty tasks, and observe the scheduler adapt.
6. **Report Generator:** One-click downloads for research reports in CSV, JSON, Markdown, and HTML formats.

---

## 9. Verification & Automated Testing

The framework includes a comprehensive test suite in `backend/tests/`:
- **37 Unit and Integration Tests**:
  - `test_schedulers.py`: Verifies EADCS cost optimization, FCFS FIFO ordering, Round Robin cycle, and Load Balancing dispersion.
  - `test_energy.py`: Validates power curve mathematics, idle/sleep transitions, and wake penalty models.
  - `test_simulation.py`: Validates discrete event queue order, clock advancement, and deadlock avoidance.
  - `test_models.py`: Validates Server and Task capacity tracking, state changes, and boundary checks.
  - `test_validation.py`: Tests input sanitization and schema constraint enforcement.
  - `test_reporting.py`: Tests export accuracy in JSON, CSV, Markdown, and HTML formats.
- **Code Coverage**: 89% total statement coverage.

To run the test suite:
```bash
pytest backend/tests/ -v --cov=backend/src
```

---

## 10. Summary & Defense Highlights

- **Original Contribution:** Formulation of the EADCS dynamic cost heuristic with non-linear power models and wake penalty amortization.
- **Measurable Result:** 27.5% average energy reduction on realistic big data workloads with zero SLA deadline violations.
- **Production Standard:** Clean decoupling into `backend/` and `frontend/`, REST API, 37 automated tests, and interactive visualization.
