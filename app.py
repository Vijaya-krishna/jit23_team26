"""
Energy-Aware Dynamic Task Scheduling Framework for Big Data Processing
Interactive Simulation, Optimization, and Evaluation Dashboard.
Built with Streamlit, Plotly, Pandas, and NumPy.
"""

import os
import json
import io
import time
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Internal Framework Imports
from src.models.server import Server, ServerState
from src.models.task import Task, TaskState
from src.algorithms.fcfs import FCFSScheduler
from src.algorithms.round_robin import RoundRobinScheduler
from src.algorithms.load_balancing import LoadBalancingScheduler
from src.algorithms.eadcs import EADCSScheduler
from src.simulation.engine import SimulationEngine, SimulationResult
from src.simulation.workload_generator import WorkloadGenerator, WorkloadCategory
from src.metrics.performance_metrics import PerformanceMetrics
from src.validation.input_validator import InputValidator
from src.reporting.exporter import Exporter
from src.reporting.report_generator import ReportGenerator
from src.utils.logging_config import get_diagnostic_events, clear_diagnostic_events, log_diagnostic_event

# -----------------------------------------------------------------------------
# Streamlit Page Setup & Custom Styling
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Energy-Aware Task Scheduling Framework",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom High-End Styling
st.markdown("""
<style>
    /* Global Background & Typography */
    .stApp {
        background-color: #0b0f19 !important;
        color: #f8fafc !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    }

    /* Remove the glaring white top header bar & decorations */
    header[data-testid="stHeader"],
    .stAppHeader {
        background-color: #0b0f19 !important;
        background: #0b0f19 !important;
        border-bottom: 1px solid #1f2937 !important;
    }
    div[data-testid="stDecoration"] {
        display: none !important;
    }
    div[data-testid="stToolbar"] {
        background: transparent !important;
    }
    div[data-testid="stToolbar"] * {
        color: #94a3b8 !important;
    }
    
    /* Sidebar Styling & Contrast */
    section[data-testid="stSidebar"] {
        background-color: #111827 !important;
        border-right: 1px solid #1f2937 !important;
    }
    section[data-testid="stSidebar"] * {
        color: #e2e8f0 !important;
    }
    div[data-testid="stRadio"] label,
    div[data-testid="stRadio"] p,
    div[data-testid="stRadio"] span {
        color: #f8fafc !important;
        font-weight: 500 !important;
        font-size: 0.95rem !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label {
        padding: 0.4rem 0.6rem !important;
        border-radius: 6px !important;
        transition: background 0.15s ease-in-out !important;
    }
    div[data-testid="stRadio"] div[role="radiogroup"] > label:hover {
        background-color: #1e293b !important;
    }
    
    /* Metrics & Cards */
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 1.3rem;
        box-shadow: 0 8px 16px -4px rgba(0, 0, 0, 0.4);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, border-color 0.2s ease;
    }
    .metric-card:hover {
        transform: translateY(-2px);
        border-color: #38bdf8;
    }
    .metric-title {
        font-size: 0.85rem;
        text-transform: uppercase;
        color: #94a3b8;
        font-weight: 700;
        letter-spacing: 0.06em;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 800;
        color: #38bdf8;
        margin: 0.35rem 0;
        letter-spacing: -0.02em;
    }
    .metric-sub {
        font-size: 0.85rem;
        color: #34d399;
        font-weight: 600;
    }
    
    /* Header Banners */
    .hero-header {
        background: linear-gradient(90deg, #1e293b 0%, #0f172a 100%);
        border-left: 5px solid #38bdf8;
        padding: 1.4rem 1.6rem;
        border-radius: 10px;
        margin-bottom: 1.8rem;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }
    .hero-title {
        font-size: 1.85rem;
        font-weight: 800;
        color: #ffffff;
        margin: 0;
        letter-spacing: -0.02em;
    }
    .hero-desc {
        color: #94a3b8;
        font-size: 0.98rem;
        margin-top: 0.4rem;
        line-height: 1.5;
    }

    /* Badges */
    .badge-pill {
        display: inline-block;
        padding: 0.25rem 0.65rem;
        border-radius: 9999px;
        font-size: 0.78rem;
        font-weight: 700;
        margin-right: 0.4rem;
    }
    .badge-green { background-color: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #059669; }
    .badge-blue { background-color: rgba(56, 189, 248, 0.2); color: #38bdf8; border: 1px solid #0284c7; }
    .badge-amber { background-color: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #d97706; }

    /* High-Contrast Interactive Buttons */
    .stButton > button, .stDownloadButton > button {
        background: linear-gradient(135deg, #1e293b 0%, #253347 100%) !important;
        color: #ffffff !important;
        border: 1px solid #475569 !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 0.92rem !important;
        padding: 0.6rem 1.2rem !important;
        transition: all 0.2s ease-in-out !important;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.3) !important;
    }
    .stButton > button:hover, .stDownloadButton > button:hover {
        background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%) !important;
        color: #ffffff !important;
        border-color: #38bdf8 !important;
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 16px rgba(56, 189, 248, 0.35) !important;
    }
    .stButton > button p, .stDownloadButton > button p {
        color: #ffffff !important;
        font-weight: 700 !important;
    }

    /* Primary Launch Button */
    button[kind="primary"] {
        background: linear-gradient(135deg, #0284c7 0%, #2563eb 100%) !important;
        color: #ffffff !important;
        border: 1px solid #38bdf8 !important;
        font-weight: 800 !important;
        letter-spacing: 0.02em !important;
    }
    button[kind="primary"]:hover {
        background: linear-gradient(135deg, #0369a1 0%, #1d4ed8 100%) !important;
        box-shadow: 0 6px 20px rgba(37, 99, 235, 0.45) !important;
    }

    /* Styled Expander Panels */
    div[data-testid="stExpander"] {
        background-color: #111827 !important;
        border: 1px solid #334155 !important;
        border-radius: 10px !important;
        overflow: hidden !important;
    }
    div[data-testid="stExpander"] details summary {
        background: linear-gradient(90deg, #1e293b 0%, #111827 100%) !important;
        color: #f8fafc !important;
        font-weight: 700 !important;
        padding: 0.8rem 1rem !important;
    }
    div[data-testid="stExpander"] details summary p,
    div[data-testid="stExpander"] details summary span {
        color: #f8fafc !important;
        font-weight: 700 !important;
    }
    div[data-testid="stExpander"] details summary:hover {
        color: #38bdf8 !important;
    }
</style>
""", unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# Helper: Fleet Factory
# -----------------------------------------------------------------------------
def build_servers_from_config(cfg: dict) -> list[Server]:
    servers = []
    n = cfg["num_servers"]
    for i in range(n):
        if i % 2 == 0:
            servers.append(Server(
                server_id=f"Host_{i+1:02d}",
                cpu_capacity=cfg["std_cpu"],
                memory_capacity=cfg["std_mem"],
                idle_power=cfg["std_p_idle"],
                max_power=cfg["std_p_max"],
                sleep_power=cfg["std_p_sleep"],
                wake_up_energy=cfg["std_wake_energy"],
                wake_up_delay=cfg["std_wake_delay"],
                alpha=cfg["std_alpha"],
                idle_timeout_to_sleep=cfg["idle_sleep_timeout"]
            ))
        else:
            # Heterogeneous server: higher capacity node
            servers.append(Server(
                server_id=f"Host_{i+1:02d}",
                cpu_capacity=cfg["std_cpu"] * 2.0,
                memory_capacity=cfg["std_mem"] * 2.0,
                idle_power=cfg["std_p_idle"] * 1.5,
                max_power=cfg["std_p_max"] * 1.5,
                sleep_power=cfg["std_p_sleep"] * 1.5,
                wake_up_energy=cfg["std_wake_energy"] * 1.5,
                wake_up_delay=cfg["std_wake_delay"] + 1.0,
                alpha=cfg["std_alpha"] + 0.1,
                idle_timeout_to_sleep=cfg["idle_sleep_timeout"] + 5.0
            ))
    return servers


# -----------------------------------------------------------------------------
# Session State Initialization
# -----------------------------------------------------------------------------
def init_session_state():
    if "fleet_config" not in st.session_state:
        st.session_state.fleet_config = {
            "num_servers": 8,
            "std_cpu": 16.0,
            "std_mem": 64.0,
            "std_p_idle": 120.0,
            "std_p_max": 300.0,
            "std_p_sleep": 12.0,
            "std_wake_energy": 600.0,
            "std_wake_delay": 4.0,
            "std_alpha": 1.5,
            "idle_sleep_timeout": 15.0,
            "enable_sleep": True,
            "weights": {
                "w_energy": 0.40,
                "w_time": 0.20,
                "w_deadline": 0.15,
                "w_load": 0.10,
                "w_state": 0.10,
                "w_frag": 0.05
            },
            "target_cpu": 0.80,
            "overload_cpu": 0.90
        }

    if "workload_tasks" not in st.session_state:
        tasks = WorkloadGenerator.generate_workload(num_tasks=80, category=WorkloadCategory.MEDIUM, seed=42)
        st.session_state.workload_tasks = tasks
        st.session_state.workload_source = "Preset: Medium Load (80 Tasks, Seed 42)"

    if "simulation_results" not in st.session_state or not st.session_state.simulation_results:
        # Pre-populate simulation results on initial load so Overview & KPIs immediately has real empirical data
        fleet_initial = build_servers_from_config(st.session_state.fleet_config)
        schedulers = [
            FCFSScheduler(),
            RoundRobinScheduler(),
            LoadBalancingScheduler(),
            EADCSScheduler(
                weights=st.session_state.fleet_config["weights"],
                target_cpu_utilization=st.session_state.fleet_config["target_cpu"],
                overload_cpu_threshold=st.session_state.fleet_config["overload_cpu"]
            )
        ]
        initial_results = []
        for sched in schedulers:
            srvs = build_servers_from_config(st.session_state.fleet_config)
            eng = SimulationEngine(
                scheduler=sched,
                servers=srvs,
                tasks=st.session_state.workload_tasks,
                enable_sleep_state=st.session_state.fleet_config["enable_sleep"],
                idle_sleep_timeout=st.session_state.fleet_config["idle_sleep_timeout"]
            )
            initial_results.append(eng.run())
        
        comparison = PerformanceMetrics.compare_multiple_results(initial_results, baseline_name="FCFS")
        st.session_state.simulation_results = initial_results
        st.session_state.metrics_comparison = comparison

init_session_state()


# -----------------------------------------------------------------------------
# Sidebar Navigation
# -----------------------------------------------------------------------------
st.sidebar.markdown("""
<div style='text-align: center; margin-bottom: 1.5rem;'>
    <h2 style='color: #38bdf8; margin: 0;'>⚡ GreenSched</h2>
    <span style='color: #94a3b8; font-size: 0.85rem;'>Big Data Energy Optimization</span>
</div>
""", unsafe_allow_html=True)

nav_page = st.sidebar.radio(
    "Navigation Menu",
    [
        "1. Overview & KPIs",
        "2. Data Center Configuration",
        "3. Workload Management",
        "4. Scheduler Simulation",
        "5. Performance Analytics",
        "6. Results & Reports"
    ]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### Fleet Quick Status")
st.sidebar.info(
    f"🖥️ **Servers:** {st.session_state.fleet_config['num_servers']}\n\n"
    f"📦 **Tasks in Memory:** {len(st.session_state.workload_tasks)}\n\n"
    f"💤 **Sleep Mode:** {'Enabled' if st.session_state.fleet_config['enable_sleep'] else 'Disabled'}\n\n"
    f"📊 **Simulations Run:** {len(st.session_state.simulation_results)}"
)


# =============================================================================
# PAGE 1: OVERVIEW & KPIS
# =============================================================================
if nav_page == "1. Overview & KPIs":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">⚡ Energy-Aware Dynamic Task Scheduling Framework</h1>
        <div class="hero-desc">Intelligent workload consolidation, idle power mitigation, and dynamic sleep transitions for big data data centers.</div>
    </div>
    """, unsafe_allow_html=True)

    metrics = st.session_state.metrics_comparison
    eadcs_metrics = next((m for m in metrics if "EADCS" in m["scheduler"]), None)
    baseline_metrics = next((m for m in metrics if m["scheduler"] == "FCFS"), None) or (metrics[0] if metrics else None)

    # Top KPI Row
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        total_tasks = len(st.session_state.workload_tasks)
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Total Tasks</div>
            <div class="metric-value">{total_tasks}</div>
            <div class="metric-sub">{st.session_state.workload_source.split(':')[0]}</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        num_srv = st.session_state.fleet_config["num_servers"]
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Simulated Fleet</div>
            <div class="metric-value">{num_srv} Hosts</div>
            <div class="metric-sub">Heterogeneous Cluster</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        if eadcs_metrics:
            pwr_val = f"{eadcs_metrics['total_energy_wh']:.2f} Wh"
            sub_val = f"{eadcs_metrics['total_energy_joules']:.0f} Joules"
        else:
            pwr_val = "Not Run"
            sub_val = "Run simulation in Tab 4"
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">EADCS Energy</div>
            <div class="metric-value">{pwr_val}</div>
            <div class="metric-sub">{sub_val}</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        if eadcs_metrics and eadcs_metrics.get("energy_savings_vs_baseline_pct") is not None:
            sav = eadcs_metrics["energy_savings_vs_baseline_pct"]
            sav_color = "#34d399" if sav >= 0 else "#f87171"
            sav_str = f"{sav:+.1f}%"
            sub_str = f"vs {baseline_metrics['scheduler']} Baseline"
        else:
            sav_str = "Pending"
            sav_color = "#94a3b8"
            sub_str = "Awaiting execution"

        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-title">Energy Saved</div>
            <div class="metric-value" style="color: {sav_color};">{sav_str}</div>
            <div class="metric-sub">{sub_str}</div>
        </div>
        """, unsafe_allow_html=True)

    # Executive Summary Card
    st.markdown("### Executive Summary")
    if metrics:
        df_summary = pd.DataFrame(metrics)[[
            "scheduler", "total_energy_wh", "energy_savings_vs_baseline_pct",
            "makespan_seconds", "avg_completion_time_sec", "p95_completion_time_sec",
            "throughput_tasks_per_sec", "deadline_miss_rate_pct", "avg_active_servers"
        ]]
        df_summary.columns = [
            "Algorithm", "Energy (Wh)", "Savings vs Base (%)", "Makespan (s)",
            "Avg Latency (s)", "P95 Latency (s)", "Throughput (t/s)", "Miss Rate (%)", "Avg Active Hosts"
        ]
        st.dataframe(df_summary, use_container_width=True)
    else:
        st.info("💡 No simulation results currently in session memory. Navigate to **4. Scheduler Simulation** to execute a side-by-side comparative run.")

    # High-level architecture and algorithm guide
    col_arch, col_principles = st.columns(2)
    with col_arch:
        st.markdown("#### 🎯 Architectural Objectives")
        st.markdown("""
        - **Idle Power Eradication:** Traditional servers consume 35-50% peak power even while idle. Unneeded servers transition to a 12W sleep state.
        - **Dynamic Workload Consolidation:** Bin-packs incoming big data tasks onto active hosts without exceeding safety thresholds (80% CPU).
        - **Deadline-Aware Multi-Objective Optimization:** Evaluates energy increments against deadline risk and queueing latency.
        - **Hysteresis & Anti-Oscillation:** Incorporates wake-up overhead penalties to prevent erratic sleep/wake cycling.
        """)

    with col_principles:
        st.markdown("#### 📐 Mathematical Energy Model")
        st.latex(r"P(u) = P_{\text{idle}} + (P_{\text{max}} - P_{\text{idle}}) \times u^{\alpha}")
        st.latex(r"E_{\text{fleet}} = \sum_{s \in \text{Servers}} \int_{0}^{T} P_s(t) \, dt + \sum E_{\text{wake}}")
        st.markdown(r"""
        - $u$: Instantaneous normalized server CPU utilization $[0, 1]$.
        - $\alpha$: Non-linear dynamic power exponent ($\alpha \ge 1.0$).
        - $E_{\text{wake}}$: State transition energy cost penalty ($1 \text{ Wh} = 3600 \text{ J}$).
        """)


# =============================================================================
# PAGE 2: DATA CENTER CONFIGURATION
# =============================================================================
elif nav_page == "2. Data Center Configuration":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">⚙️ Data Center & Power Configuration</h1>
        <div class="hero-desc">Tune physical node specifications, power consumption curves, dynamic sleep timeouts, and EADCS multi-objective weights.</div>
    </div>
    """, unsafe_allow_html=True)

    with st.form("datacenter_config_form"):
        col_srv, col_pwr = st.columns(2)

        with col_srv:
            st.markdown("#### 🖥️ Server Hardware Specifications")
            num_srv = st.slider("Number of Servers in Fleet", min_value=2, max_value=32, value=st.session_state.fleet_config["num_servers"], step=2)
            cpu_cap = st.number_input("Standard Node CPU Cores", min_value=4.0, max_value=128.0, value=st.session_state.fleet_config["std_cpu"], step=4.0)
            mem_cap = st.number_input("Standard Node RAM (GB)", min_value=8.0, max_value=512.0, value=st.session_state.fleet_config["std_mem"], step=8.0)
            idle_timeout = st.slider("Idle Inactivity Timeout before Sleep (s)", min_value=5.0, max_value=60.0, value=st.session_state.fleet_config["idle_sleep_timeout"], step=5.0)
            enable_sleep = st.checkbox("Enable Dynamic Low-Power Sleep States", value=st.session_state.fleet_config["enable_sleep"])

        with col_pwr:
            st.markdown("#### ⚡ Power Model Parameters")
            p_idle = st.number_input("Idle Power (Watts)", min_value=10.0, max_value=500.0, value=st.session_state.fleet_config["std_p_idle"], step=10.0)
            p_max = st.number_input("Peak Full-Load Power (Watts)", min_value=50.0, max_value=1500.0, value=st.session_state.fleet_config["std_p_max"], step=25.0)
            p_sleep = st.number_input("Sleep State Power (Watts)", min_value=1.0, max_value=50.0, value=st.session_state.fleet_config["std_p_sleep"], step=1.0)
            wake_energy = st.number_input("Wake-up Energy Penalty (Joules)", min_value=0.0, max_value=5000.0, value=st.session_state.fleet_config["std_wake_energy"], step=50.0)
            wake_delay = st.number_input("Wake-up Hardware Delay (Seconds)", min_value=0.5, max_value=20.0, value=st.session_state.fleet_config["std_wake_delay"], step=0.5)
            alpha = st.slider("Power Exponent (Alpha)", min_value=1.0, max_value=3.0, value=st.session_state.fleet_config["std_alpha"], step=0.1)

        st.markdown("---")
        st.markdown("#### 🎯 EADCS Multi-Objective Weights Configuration")
        st.caption("Weights are normalized automatically to sum to 1.0.")

        w_col1, w_col2, w_col3 = st.columns(3)
        with w_col1:
            w_e = st.slider("Energy Cost Weight (wE)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_energy"], 0.05)
            w_t = st.slider("Completion Time Weight (wT)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_time"], 0.05)
        with w_col2:
            w_d = st.slider("Deadline Risk Weight (wD)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_deadline"], 0.05)
            w_l = st.slider("Consolidation / Load Weight (wL)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_load"], 0.05)
        with w_col3:
            w_s = st.slider("State Transition Penalty Weight (wS)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_state"], 0.05)
            w_f = st.slider("Resource Fragmentation Weight (wF)", 0.0, 1.0, st.session_state.fleet_config["weights"]["w_frag"], 0.05)

        t_col1, t_col2 = st.columns(2)
        with t_col1:
            target_cpu = st.slider("Target Consolidation CPU Utilization", 0.50, 0.90, st.session_state.fleet_config["target_cpu"], 0.05)
        with t_col2:
            overload_cpu = st.slider("Overload Prevention Threshold", 0.70, 0.98, st.session_state.fleet_config["overload_cpu"], 0.02)

        submit_btn = st.form_submit_button("💾 Save and Apply Configuration", use_container_width=True)

        if submit_btn:
            # Validate server parameters
            server_test = {
                "server_id": "ValidationTest",
                "cpu_capacity": cpu_cap,
                "memory_capacity": mem_cap,
                "idle_power": p_idle,
                "max_power": p_max,
                "sleep_power": p_sleep,
                "alpha": alpha
            }
            is_valid, errors = InputValidator.validate_server_config(server_test)
            if not is_valid:
                for err in errors:
                    st.error(f"❌ {err}")
            else:
                st.session_state.fleet_config.update({
                    "num_servers": num_srv,
                    "std_cpu": cpu_cap,
                    "std_mem": mem_cap,
                    "std_p_idle": p_idle,
                    "std_p_max": p_max,
                    "std_p_sleep": p_sleep,
                    "std_wake_energy": wake_energy,
                    "std_wake_delay": wake_delay,
                    "std_alpha": alpha,
                    "idle_sleep_timeout": idle_timeout,
                    "enable_sleep": enable_sleep,
                    "weights": {
                        "w_energy": w_e, "w_time": w_t, "w_deadline": w_d,
                        "w_load": w_l, "w_state": w_s, "w_frag": w_f
                    },
                    "target_cpu": target_cpu,
                    "overload_cpu": overload_cpu
                })
                st.success("✅ Configuration validated and successfully saved to session memory!")


# =============================================================================
# PAGE 3: WORKLOAD MANAGEMENT
# =============================================================================
elif nav_page == "3. Workload Management":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">📦 Big Data Workload Management</h1>
        <div class="hero-desc">Generate synthetic big data batch traces with reproducible seeds or upload custom CSV benchmark workloads.</div>
    </div>
    """, unsafe_allow_html=True)

    tab_gen, tab_upload = st.tabs(["🎲 Synthetic Workload Generator", "📁 Upload Custom CSV Workload"])

    with tab_gen:
        col_preset, col_custom = st.columns([1, 2])
        with col_preset:
            st.markdown("#### Quick Benchmark Presets")
            if st.button("🟢 Low-Load Workload (80 Tasks)", use_container_width=True):
                tasks = WorkloadGenerator.generate_workload(80, WorkloadCategory.LOW, seed=101)
                st.session_state.workload_tasks = tasks
                st.session_state.workload_source = "Preset: Low Load (80 Tasks, Seed 101)"
                st.success("Loaded Low-Load Workload!")

            if st.button("🟡 Medium-Load Workload (120 Tasks)", use_container_width=True):
                tasks = WorkloadGenerator.generate_workload(120, WorkloadCategory.MEDIUM, seed=202)
                st.session_state.workload_tasks = tasks
                st.session_state.workload_source = "Preset: Medium Load (120 Tasks, Seed 202)"
                st.success("Loaded Medium-Load Workload!")

            if st.button("🔴 Bursty Workload (160 Tasks)", use_container_width=True):
                tasks = WorkloadGenerator.generate_workload(160, WorkloadCategory.BURSTY, seed=303)
                st.session_state.workload_tasks = tasks
                st.session_state.workload_source = "Preset: Bursty Peak Load (160 Tasks, Seed 303)"
                st.success("Loaded Bursty Workload!")

        with col_custom:
            st.markdown("#### Custom Synthetic Generator")
            with st.form("custom_workload_form"):
                c_num = st.slider("Task Count", min_value=10, max_value=500, value=100, step=10)
                c_cat = st.selectbox("Arrival Profile", [WorkloadCategory.LOW, WorkloadCategory.MEDIUM, WorkloadCategory.BURSTY])
                c_seed = st.number_input("Deterministic Random Seed", min_value=1, max_value=999999, value=42, step=1)
                gen_btn = st.form_submit_button("⚡ Generate Custom Workload", use_container_width=True)

                if gen_btn:
                    tasks = WorkloadGenerator.generate_workload(c_num, c_cat, seed=int(c_seed))
                    st.session_state.workload_tasks = tasks
                    st.session_state.workload_source = f"Custom: {c_cat.capitalize()} ({c_num} Tasks, Seed {c_seed})"
                    st.success(f"Generated {len(tasks)} tasks!")

    with tab_upload:
        st.markdown("#### Upload CSV Workload File")
        st.markdown("""
        **Required CSV Columns:** `task_id`, `arrival_time`, `cpu_demand`, `memory_demand`, `duration`  
        **Optional Columns:** `name`, `priority`, `deadline`
        """)
        uploaded_file = st.file_uploader("Select Workload CSV", type=["csv"])

        if uploaded_file is not None:
            try:
                df_upload = pd.read_csv(uploaded_file)
                is_valid, errors, warnings = InputValidator.validate_workload_dataframe(df_upload)

                if not is_valid:
                    st.error("❌ Workload validation failed:")
                    for err in errors:
                        st.write(f"- {err}")
                else:
                    if warnings:
                        st.warning("⚠️ Validation warnings:")
                        for w in warnings:
                            st.write(f"- {w}")

                    tasks = WorkloadGenerator.dataframe_to_tasks(df_upload)
                    st.session_state.workload_tasks = tasks
                    st.session_state.workload_source = f"Uploaded CSV: {uploaded_file.name} ({len(tasks)} Tasks)"
                    st.success(f"✅ Successfully loaded and validated {len(tasks)} tasks from {uploaded_file.name}!")
            except Exception as e:
                st.error(f"Error parsing uploaded file: {str(e)}")

    # Workload Preview & Distributions
    st.markdown("---")
    st.markdown(f"### Current Workload: `{st.session_state.workload_source}`")

    if st.session_state.workload_tasks:
        df_tasks = WorkloadGenerator.tasks_to_dataframe(st.session_state.workload_tasks)
        
        col_tbl, col_charts = st.columns([3, 2])
        with col_tbl:
            st.dataframe(df_tasks[[
                "task_id", "name", "arrival_time", "cpu_demand", "memory_demand", "duration", "priority", "deadline"
            ]].head(100), use_container_width=True, height=350)
            st.caption(f"Showing up to first 100 rows of {len(df_tasks)} total tasks.")

        with col_charts:
            fig_dist = px.histogram(
                df_tasks,
                x="duration",
                color="cpu_demand",
                nbins=20,
                title="Task Duration & CPU Demands",
                template="plotly_dark"
            )
            fig_dist.update_layout(margin=dict(l=20, r=20, t=40, b=20), height=350)
            st.plotly_chart(fig_dist, use_container_width=True)


# =============================================================================
# PAGE 4: SCHEDULER SIMULATION
# =============================================================================
elif nav_page == "4. Scheduler Simulation":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">🚀 Discrete-Event Scheduler Simulation</h1>
        <div class="hero-desc">Execute event-driven simulations, compare dynamic task dispatching, and observe allocation decisions in real time.</div>
    </div>
    """, unsafe_allow_html=True)

    col_ctrl1, col_ctrl2 = st.columns([2, 1])
    with col_ctrl1:
        st.markdown("#### Select Scheduling Algorithms to Evaluate")
        selected_schedulers = st.multiselect(
            "Algorithms to Include",
            options=["FCFS", "Round Robin", "Load Balancing", "EADCS"],
            default=["FCFS", "Round Robin", "Load Balancing", "EADCS"]
        )

    with col_ctrl2:
        st.markdown("#### Baseline Designation")
        baseline_name = st.selectbox(
            "Reference Baseline Algorithm",
            options=["FCFS", "Round Robin", "Load Balancing"],
            index=0
        )

    if st.button("▶️ Run Simulation Engine", type="primary", use_container_width=True):
        if not selected_schedulers:
            st.warning("Please select at least one algorithm to run.")
        elif not st.session_state.workload_tasks:
            st.warning("No workload tasks available. Please generate or upload a workload in Tab 3.")
        else:
            progress_bar = st.progress(0, text="Initializing simulation environments...")
            results = []
            clear_diagnostic_events()

            sched_instances = {
                "FCFS": FCFSScheduler(),
                "Round Robin": RoundRobinScheduler(),
                "Load Balancing": LoadBalancingScheduler(),
                "EADCS": EADCSScheduler(
                    weights=st.session_state.fleet_config["weights"],
                    target_cpu_utilization=st.session_state.fleet_config["target_cpu"],
                    overload_cpu_threshold=st.session_state.fleet_config["overload_cpu"]
                )
            }

            total_runs = len(selected_schedulers)

            for idx, s_name in enumerate(selected_schedulers):
                progress_bar.progress(
                    int((idx / total_runs) * 100),
                    text=f"Simulating discrete-event engine with '{s_name}'..."
                )
                
                fleet = build_servers_from_config(st.session_state.fleet_config)
                scheduler_obj = sched_instances[s_name]

                engine = SimulationEngine(
                    scheduler=scheduler_obj,
                    servers=fleet,
                    tasks=st.session_state.workload_tasks,
                    enable_sleep_state=st.session_state.fleet_config["enable_sleep"],
                    idle_sleep_timeout=st.session_state.fleet_config["idle_sleep_timeout"]
                )

                sim_res = engine.run()
                results.append(sim_res)

            progress_bar.progress(100, text="Computing metrics and generating comparisons...")
            comparison = PerformanceMetrics.compare_multiple_results(results, baseline_name=baseline_name)

            st.session_state.simulation_results = results
            st.session_state.metrics_comparison = comparison

            st.success("✅ Simulation executed successfully! Results ready for inspection.")

    # Display Current Results if Available
    if st.session_state.simulation_results:
        st.markdown("---")
        st.markdown("### Execution Outcomes")
        
        comp_df = pd.DataFrame(st.session_state.metrics_comparison)
        st.dataframe(
            comp_df[[
                "scheduler", "total_energy_wh", "energy_savings_vs_baseline_pct",
                "makespan_seconds", "avg_completion_time_sec", "p95_completion_time_sec",
                "throughput_tasks_per_sec", "deadline_miss_rate_pct", "avg_active_servers", "total_state_transitions"
            ]],
            use_container_width=True
        )

        # Inspect Task Lifecycle Allocations
        st.markdown("### Detailed Task Lifecycle & Server Allocations")
        sched_to_inspect = st.selectbox(
            "Select Scheduler Result to Inspect",
            [r.scheduler_name for r in st.session_state.simulation_results]
        )
        selected_res = next((r for r in st.session_state.simulation_results if r.scheduler_name == sched_to_inspect), None)

        if selected_res:
            res_df = pd.DataFrame([t.to_dict() for t in selected_res.tasks])
            
            # Allocation filter
            filter_col1, filter_col2 = st.columns(2)
            with filter_col1:
                server_filter = st.multiselect(
                    "Filter by Assigned Server",
                    options=sorted(list(set(res_df["assigned_server_id"].dropna().unique())))
                )
            with filter_col2:
                state_filter = st.multiselect(
                    "Filter by Task State",
                    options=list(res_df["state"].unique()),
                    default=list(res_df["state"].unique())
                )

            filtered_df = res_df.copy()
            if server_filter:
                filtered_df = filtered_df[filtered_df["assigned_server_id"].isin(server_filter)]
            if state_filter:
                filtered_df = filtered_df[filtered_df["state"].isin(state_filter)]

            st.dataframe(filtered_df[[
                "task_id", "name", "arrival_time", "actual_start_time", "actual_completion_time",
                "waiting_time", "turnaround_time", "assigned_server_id", "energy_consumed_wh", "missed_deadline", "state"
            ]], use_container_width=True, height=300)

        # Diagnostics & Fallbacks
        diags = get_diagnostic_events()
        if diags:
            with st.expander("⚠️ Diagnostic & Fallback Log Events", expanded=False):
                st.json(diags)


# =============================================================================
# PAGE 5: PERFORMANCE ANALYTICS
# =============================================================================
elif nav_page == "5. Performance Analytics":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">📊 Multi-Dimensional Performance Analytics</h1>
        <div class="hero-desc">Interactive comparative visualizations of fleet power, energy savings, latency percentiles, and resource utilization.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.simulation_results:
        st.info("💡 No simulation results in memory. Please go to **4. Scheduler Simulation** and click 'Run Simulation Engine'.")
    else:
        results = st.session_state.simulation_results
        metrics = st.session_state.metrics_comparison
        df_metrics = pd.DataFrame(metrics)

        # Row 1: Energy Bars & Energy Savings
        col_e1, col_e2 = st.columns(2)
        with col_e1:
            fig_energy = px.bar(
                df_metrics,
                x="scheduler",
                y="total_energy_wh",
                color="scheduler",
                text="total_energy_wh",
                title="Total Fleet Energy Consumption (Wh)",
                template="plotly_dark"
            )
            fig_energy.update_traces(texttemplate='%{text:.2f} Wh', textposition='outside')
            fig_energy.update_layout(showlegend=False, margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_energy, use_container_width=True)

        with col_e2:
            fig_sav = px.bar(
                df_metrics,
                x="scheduler",
                y="energy_savings_vs_baseline_pct",
                color="energy_savings_vs_baseline_pct",
                color_continuous_scale="Viridis",
                text="energy_savings_vs_baseline_pct",
                title="Energy Savings Relative to Baseline (%)",
                template="plotly_dark"
            )
            fig_sav.update_traces(texttemplate='%{text:+.1f}%', textposition='outside')
            fig_sav.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_sav, use_container_width=True)

        # Row 2: Active Hosts Over Time & Cumulative Energy Over Time
        col_t1, col_t2 = st.columns(2)
        with col_t1:
            fig_active = go.Figure()
            for res in results:
                history = res.energy_calculator.history
                if history:
                    df_h = pd.DataFrame(history)
                    fig_active.add_trace(go.Scatter(
                        x=df_h["timestamp"],
                        y=df_h["active_servers"],
                        mode="lines",
                        name=res.scheduler_name
                    ))
            fig_active.update_layout(
                title="Active Physical Hosts Over Time (Consolidation View)",
                xaxis_title="Simulated Time (Seconds)",
                yaxis_title="Active Server Count",
                template="plotly_dark",
                margin=dict(t=40, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_active, use_container_width=True)

        with col_t2:
            fig_cum = go.Figure()
            for res in results:
                history = res.energy_calculator.history
                if history:
                    df_h = pd.DataFrame(history)
                    fig_cum.add_trace(go.Scatter(
                        x=df_h["timestamp"],
                        y=df_h["fleet_energy_wh"],
                        mode="lines",
                        name=res.scheduler_name
                    ))
            fig_cum.update_layout(
                title="Cumulative Fleet Energy Over Time (Wh)",
                xaxis_title="Simulated Time (Seconds)",
                yaxis_title="Energy (Wh)",
                template="plotly_dark",
                margin=dict(t=40, b=20, l=20, r=20)
            )
            st.plotly_chart(fig_cum, use_container_width=True)

        # Row 3: Latencies & Energy Breakdown
        col_lat, col_break = st.columns(2)
        with col_lat:
            fig_lat = px.bar(
                df_metrics,
                x="scheduler",
                y=["avg_completion_time_sec", "p95_completion_time_sec"],
                barmode="group",
                title="Average vs 95th Percentile Latency (s)",
                template="plotly_dark"
            )
            fig_lat.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_lat, use_container_width=True)

        with col_break:
            fig_breakdown = px.bar(
                df_metrics,
                x="scheduler",
                y=["active_energy_wh", "idle_energy_wh", "sleep_energy_wh", "wakeup_overhead_wh"],
                barmode="stack",
                title="Energy Component Breakdown (Wh)",
                template="plotly_dark"
            )
            fig_breakdown.update_layout(margin=dict(t=40, b=20, l=20, r=20))
            st.plotly_chart(fig_breakdown, use_container_width=True)


# =============================================================================
# PAGE 6: RESULTS AND REPORTS
# =============================================================================
elif nav_page == "6. Results & Reports":
    st.markdown("""
    <div class="hero-header">
        <h1 class="hero-title">📄 Experiment Results, Exports & Reports</h1>
        <div class="hero-desc">Download complete task traces, experiment metrics in CSV/JSON, and generate formal HTML and Markdown reports.</div>
    </div>
    """, unsafe_allow_html=True)

    if not st.session_state.simulation_results:
        st.info("💡 No simulation results in memory. Please execute a simulation in Tab 4 first.")
    else:
        results = st.session_state.simulation_results
        metrics = st.session_state.metrics_comparison

        col_dl1, col_dl2, col_dl3 = st.columns(3)
        with col_dl1:
            st.markdown("#### 📊 Experiment Metrics CSV")
            csv_metrics_buffer = io.StringIO()
            pd.DataFrame(metrics).to_csv(csv_metrics_buffer, index=False)
            st.download_button(
                label="📥 Download Metrics CSV",
                data=csv_metrics_buffer.getvalue(),
                file_name="simulation_metrics.csv",
                mime="text/csv",
                use_container_width=True
            )

        with col_dl2:
            st.markdown("#### 📋 Experiment Metrics JSON")
            json_metrics = json.dumps(metrics, indent=2)
            st.download_button(
                label="📥 Download Metrics JSON",
                data=json_metrics,
                file_name="simulation_metrics.json",
                mime="application/json",
                use_container_width=True
            )

        with col_dl3:
            st.markdown("#### 📑 Task Traces CSV (EADCS)")
            eadcs_res = next((r for r in results if "EADCS" in r.scheduler_name), results[0])
            tasks_csv_buffer = io.StringIO()
            pd.DataFrame([t.to_dict() for t in eadcs_res.tasks]).to_csv(tasks_csv_buffer, index=False)
            st.download_button(
                label="📥 Download Task Traces CSV",
                data=tasks_csv_buffer.getvalue(),
                file_name=f"{eadcs_res.scheduler_name}_task_traces.csv",
                mime="text/csv",
                use_container_width=True
            )

        st.markdown("---")
        st.markdown("### Formal Executive Report Generation")

        col_rep1, col_rep2 = st.columns(2)
        with col_rep1:
            html_path = "reports/experiment_report.html"
            ReportGenerator.generate_html_report(
                metrics_comparison=metrics,
                workload_info={"total_tasks": len(st.session_state.workload_tasks), "source": st.session_state.workload_source},
                datacenter_info=st.session_state.fleet_config,
                output_path=html_path
            )
            with open(html_path, "r", encoding="utf-8") as f:
                html_data = f.read()

            st.download_button(
                label="📥 Download Complete HTML Report",
                data=html_data,
                file_name="energy_scheduler_report.html",
                mime="text/html",
                use_container_width=True
            )

        with col_rep2:
            md_path = "reports/experiment_report.md"
            ReportGenerator.generate_markdown_report(
                metrics_comparison=metrics,
                workload_info={"total_tasks": len(st.session_state.workload_tasks), "source": st.session_state.workload_source},
                datacenter_info=st.session_state.fleet_config,
                output_path=md_path
            )
            with open(md_path, "r", encoding="utf-8") as f:
                md_data = f.read()

            st.download_button(
                label="📥 Download Markdown Report (.md)",
                data=md_data,
                file_name="energy_scheduler_report.md",
                mime="text/markdown",
                use_container_width=True
            )

        # Preview Report in UI
        st.markdown("### Report Live Preview")
        with st.expander("Preview Markdown Experiment Report", expanded=True):
            st.markdown(md_data)
