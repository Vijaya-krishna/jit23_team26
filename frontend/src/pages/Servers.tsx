import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { 
  Server, Cpu, Database, HardDrive, Wifi,
  Thermometer, Zap, RefreshCw, Power, Plus, Loader2
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { simulationService } from '../services/simulation_service';
import type { PhysicalServer, Telemetry, Task } from '../types/simulation';
import { SchedulerSelector } from '../components/SchedulerSelector';

export const Servers: React.FC = () => {
  const { logout, user } = useAuth();
  const [servers, setServers] = useState<PhysicalServer[]>([]);
  const [telemetry, setTelemetry] = useState<Telemetry | null>(null);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Form Modal States
  const [showAddModal, setShowAddModal] = useState<boolean>(false);
  const [newCpu, setNewCpu] = useState<number>(16);
  const [newFreq, setNewFreq] = useState<number>(3.2);
  const [newRam, setNewRam] = useState<number>(64000);
  const [newStorage, setNewStorage] = useState<number>(2000);
  const [newBandwidth, setNewBandwidth] = useState<number>(10000);

  // VM Modal States
  const [showVmModal, setShowVmModal] = useState<number | null>(null); // holds target server ID
  const [vmCpu, setVmCpu] = useState<number>(4);
  const [vmRam, setVmRam] = useState<number>(8000);
  const [vmStorage, setVmStorage] = useState<number>(100);
  const [vmBandwidth, setVmBandwidth] = useState<number>(1000);

  // Load servers and initial telemetry
  const loadData = async () => {
    try {
      setError(null);
      const serverList = await simulationService.getServers();
      setServers(serverList);
      
      const telemetryData = await simulationService.getTelemetry();
      setTelemetry(telemetryData);

      const taskList = await simulationService.getTasks();
      setTasks(taskList);
    } catch (err: any) {
      setError(err.message || 'Failed to load server configurations.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handlePowerToggle = async (hostId: number, currentState: 'ACTIVE' | 'SLEEP' | 'OFF') => {
    const states: ('ACTIVE' | 'SLEEP' | 'OFF')[] = ['ACTIVE', 'SLEEP', 'OFF'];
    const nextIndex = (states.indexOf(currentState) + 1) % states.length;
    const targetState = states[nextIndex];

    setActionLoading(`power-${hostId}`);
    try {
      await simulationService.updatePowerState(hostId, targetState);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Power transition failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleTriggerTick = async () => {
    setActionLoading('tick');
    try {
      await simulationService.tick();
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Tick transition failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleAddServer = async (e: React.FormEvent) => {
    e.preventDefault();
    setActionLoading('add-server');
    try {
      // Actually we call post /api/simulation/servers
      const token = localStorage.getItem('token');
      const response = await fetch('http://localhost:8000/api/simulation/servers', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token || ''}`,
        },
        body: JSON.stringify({
          cpu_cores: newCpu,
          cpu_frequency_ghz: newFreq,
          ram_mb: newRam,
          storage_gb: newStorage,
          bandwidth_mbps: newBandwidth
        })
      });

      if (!response.ok) {
        throw new Error('Provisioning failed.');
      }
      
      setShowAddModal(false);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to register server.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeployVm = async (e: React.FormEvent) => {
    e.preventDefault();
    if (showVmModal === null) return;
    setActionLoading(`vm-${showVmModal}`);
    try {
      await simulationService.deployVm(showVmModal, {
        cpu_cores: vmCpu,
        ram_mb: vmRam,
        storage_gb: vmStorage,
        bandwidth_mbps: vmBandwidth
      });
      setShowVmModal(null);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'VM deployment failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDecommissionVm = async (vmId: number) => {
    setActionLoading(`destroy-${vmId}`);
    try {
      await simulationService.destroyVm(vmId);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'VM destroy failed.');
    } finally {
      setActionLoading(null);
    }
  };

  const handleGenerateWorkload = async (count: number) => {
    setActionLoading('workload');
    try {
      await simulationService.generateWorkload(count);
      await loadData();
    } catch (err: any) {
      setError(err.message || 'Failed to generate workload.');
    } finally {
      setActionLoading(null);
    }
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background text-white">
        <Loader2 className="w-10 h-10 text-primary animate-spin" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-white pb-12 relative overflow-hidden">
      {/* Background glow graphics */}
      <div className="absolute top-0 right-0 w-[500px] h-[500px] rounded-full bg-primary/5 blur-[150px] pointer-events-none" />
      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] rounded-full bg-secondary/5 blur-[150px] pointer-events-none" />

      {/* Grid lines layout */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:40px_40px] pointer-events-none" />

      {/* Navigation Header */}
      {/* Action Toolbar */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12,
        padding: '16px 24px 0',
        maxWidth: 1280, margin: '0 auto',
      }}>
        <div>
          <h2 style={{ fontSize: 20, fontWeight: 800, color: '#f1f5f9', margin: 0, letterSpacing: '-0.02em' }}>
            🖥️ Data Center Management
          </h2>
          <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>
            Logged in as <strong style={{ color: '#94a3b8' }}>{user?.username}</strong> ({user?.role}) — manage physical hosts, VMs &amp; workloads
          </p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <button
            onClick={handleTriggerTick}
            disabled={actionLoading !== null}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 10, border: 'none',
              background: 'linear-gradient(135deg, #6366f1, #06b6d4)',
              color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer',
              opacity: actionLoading ? 0.6 : 1, transition: 'all 0.2s',
            }}
          >
            {actionLoading === 'tick' ? '⌛' : '▶'} Clock Step (Tick)
          </button>
          <button
            onClick={() => setShowAddModal(true)}
            style={{
              display: 'flex', alignItems: 'center', gap: 6,
              padding: '8px 16px', borderRadius: 10,
              border: '1px solid rgba(255,255,255,0.12)', background: 'rgba(255,255,255,0.05)',
              color: '#e2e8f0', fontWeight: 600, fontSize: 13, cursor: 'pointer',
              transition: 'all 0.2s',
            }}
          >
            + Add Server
          </button>
          <button
            onClick={logout}
            title="Logout session"
            style={{
              padding: '8px 14px', borderRadius: 10,
              border: '1px solid rgba(255,255,255,0.08)', background: 'rgba(255,255,255,0.05)',
              color: '#64748b', cursor: 'pointer', fontSize: 13, transition: 'all 0.2s',
            }}
          >
            ⤴ Logout
          </button>
        </div>
      </div>

      {/* Main Container */}
      <main className="max-w-7xl mx-auto px-4 mt-8 space-y-8 z-10 relative">

        
        {/* Telemetry Cards Banner */}
        {telemetry && (
          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="glass-panel p-4 rounded-xl space-y-1">
              <span className="text-2xs text-gray-400 font-medium uppercase tracking-wider">Clock Ticks</span>
              <div className="text-xl font-bold">{telemetry.tick}</div>
            </div>
            <div className="glass-panel p-4 rounded-xl space-y-1">
              <span className="text-2xs text-gray-400 font-medium uppercase tracking-wider">Total Hosts</span>
              <div className="text-xl font-bold">{telemetry.total_hosts} <span className="text-xs text-gray-500 font-normal">({telemetry.active_hosts} active)</span></div>
            </div>
            <div className="glass-panel p-4 rounded-xl space-y-1">
              <span className="text-2xs text-gray-400 font-medium uppercase tracking-wider">VMs Deployed</span>
              <div className="text-xl font-bold">{telemetry.total_vms}</div>
            </div>
            <div className="glass-panel p-4 rounded-xl space-y-1">
              <span className="text-2xs text-gray-400 font-medium uppercase tracking-wider">Total Power Draw</span>
              <div className="text-xl font-bold text-primary">{telemetry.total_power_w.toFixed(1)} W</div>
            </div>
            <div className="glass-panel p-4 rounded-xl space-y-1 col-span-2 md:col-span-1">
              <span className="text-2xs text-gray-400 font-medium uppercase tracking-wider">Energy Consumed</span>
              <div className="text-xl font-bold text-secondary">{telemetry.total_energy_kwh.toFixed(6)} kWh</div>
            </div>
          </div>
        )}

        {/* Global Error Banner */}
        {error && (
          <div className="p-4 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-sm flex items-center justify-between">
            <span>{error}</span>
            <button onClick={() => setError(null)} className="text-2xs underline">Dismiss</button>
          </div>
        )}

        {/* Resource Scheduler Strategy Selector */}
        <SchedulerSelector onSchedulerChanged={loadData} />

        {/* Physical Server Cards Grid */}
        <div className="space-y-4">
          <h2 className="text-xl font-extrabold tracking-tight">Active Infrastructure Node Manager</h2>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {servers.map((server) => {
              const isSleeping = server.power_state === 'SLEEP';
              const isOff = server.power_state === 'OFF';
              
              // Color variables for styling depending on utilization
              let utilColor = 'bg-accent-green';
              if (server.cpu_utilization > 0.9) utilColor = 'bg-accent-red';
              else if (server.cpu_utilization > 0.6) utilColor = 'bg-accent-yellow';

              return (
                <motion.div
                  key={server.id}
                  layout
                  className={`glass-panel rounded-2xl overflow-hidden shadow-lg border relative flex flex-col justify-between ${
                    isSleeping ? 'opacity-65 border-white/5' : 
                    isOff ? 'opacity-40 border-white/5 bg-black/40' : 'border-white/10'
                  }`}
                >
                  {/* Glowing header strip */}
                  <div className={`h-1.5 w-full ${
                    isSleeping ? 'bg-accent-gray' :
                    isOff ? 'bg-black/50' :
                    server.cpu_utilization > 0.9 ? 'bg-accent-red' : 
                    server.cpu_utilization > 0.6 ? 'bg-accent-yellow' : 'bg-accent-green'
                  }`} />

                  {/* Body Content */}
                  <div className="p-6 space-y-5">
                    <div className="flex items-start justify-between">
                      <div className="flex items-center space-x-2">
                        <Server className={`w-5 h-5 ${isSleeping || isOff ? 'text-gray-500' : 'text-primary'}`} />
                        <div>
                          <h3 className="font-bold text-white">Host Node ID: #{server.id}</h3>
                          <span className={`inline-flex items-center text-3xs font-semibold px-2 py-0.5 rounded-full mt-1 ${
                            isSleeping ? 'bg-white/10 text-gray-400' :
                            isOff ? 'bg-red-500/10 text-red-400' : 'bg-green-500/10 text-green-400'
                          }`}>
                            {server.power_state}
                          </span>
                        </div>
                      </div>

                      {/* State toggle controller */}
                      <button
                        onClick={() => handlePowerToggle(server.id, server.power_state)}
                        disabled={actionLoading !== null}
                        className="p-1.5 rounded-lg border border-white/5 bg-white/5 text-gray-400 hover:text-white hover:bg-white/10 transition-colors"
                        title="Toggle power state"
                      >
                        <Power className="w-4 h-4" />
                      </button>
                    </div>

                    {/* Spec details grid */}
                    <div className="grid grid-cols-3 gap-2 py-2 border-y border-white/5 text-3xs text-gray-400 font-medium">
                      <div>
                        <span className="block text-gray-500">Processing</span>
                        <span className="text-white font-bold">{server.cpu_cores} Cores</span>
                      </div>
                      <div>
                        <span className="block text-gray-500">Memory</span>
                        <span className="text-white font-bold">{(server.ram_mb / 1000).toFixed(0)} GB</span>
                      </div>
                      <div>
                        <span className="block text-gray-500">Storage</span>
                        <span className="text-white font-bold">{(server.storage_gb / 1000).toFixed(1)} TB</span>
                      </div>
                    </div>

                    {/* Dynamics Telemetry Gauges */}
                    {!(isSleeping || isOff) && (
                      <div className="space-y-3.5">
                        <div className="space-y-1.5">
                          <div className="flex justify-between text-3xs font-semibold uppercase tracking-wider text-gray-400">
                            <span>CPU utilization</span>
                            <span className="text-white font-bold">{(server.cpu_utilization * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                            <div className={`h-full ${utilColor} transition-all duration-300`} style={{ width: `${server.cpu_utilization * 100}%` }} />
                          </div>
                        </div>

                        <div className="space-y-1.5">
                          <div className="flex justify-between text-3xs font-semibold uppercase tracking-wider text-gray-400">
                            <span>RAM allocation</span>
                            <span className="text-white font-bold">{(server.ram_utilization * 100).toFixed(1)}%</span>
                          </div>
                          <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                            <div className="h-full bg-secondary transition-all duration-300" style={{ width: `${server.ram_utilization * 100}%` }} />
                          </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4 pt-2">
                          <div className="flex items-center space-x-1.5">
                            <Thermometer className="w-4 h-4 text-accent-red" />
                            <div>
                              <span className="block text-4xs text-gray-500 font-semibold uppercase">Temp</span>
                              <span className="text-xs font-bold">{server.temperature.toFixed(1)} °C</span>
                            </div>
                          </div>

                          <div className="flex items-center space-x-1.5">
                            <Zap className="w-4 h-4 text-accent-yellow" />
                            <div>
                              <span className="block text-4xs text-gray-500 font-semibold uppercase">Power</span>
                              <span className="text-xs font-bold text-accent-yellow">{server.power_consumption.toFixed(1)} W</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>

                  {/* Footer options */}
                  <div className="px-6 py-4 bg-white/[0.02] border-t border-white/5 flex items-center justify-between text-xs">
                    <span className="text-gray-400 font-semibold">
                      VM Allocations: <span className="text-white font-bold">{server.vms.length}</span>
                    </span>
                    
                    {!(isSleeping || isOff) && (
                      <button
                        onClick={() => setShowVmModal(server.id)}
                        className="text-primary hover:text-primary-light font-bold flex items-center space-x-1 transition-colors"
                      >
                        <Plus className="w-3.5 h-3.5" />
                        <span>Deploy VM</span>
                      </button>
                    )}
                  </div>
                </motion.div>
              );
            })}
          </div>
        </div>

        {/* Task Workload Queue Manager */}
        <div className="space-y-4 pt-4 border-t border-white/5">
          <div className="flex items-center justify-between flex-wrap gap-4">
            <div>
              <h2 className="text-xl font-extrabold tracking-tight text-white">Workload Task Queue</h2>
              <p className="text-2xs text-gray-500 font-medium mt-0.5 font-sans">Generate and monitor cloud batch processing payloads</p>
            </div>
            
            <div className="flex items-center space-x-2">
              <button
                onClick={() => handleGenerateWorkload(10)}
                disabled={actionLoading !== null}
                className="bg-white/5 border border-white/10 hover:bg-white/10 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all active:scale-95"
              >
                +10 Tasks
              </button>
              <button
                onClick={() => handleGenerateWorkload(50)}
                disabled={actionLoading !== null}
                className="bg-white/5 border border-white/10 hover:bg-white/10 text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all active:scale-95"
              >
                +50 Tasks
              </button>
            </div>
          </div>

          <div className="glass-panel rounded-2xl overflow-hidden border border-white/10 bg-black/20">
            <div className="overflow-x-auto max-h-[350px]">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-white/5 bg-white/[0.02] text-3xs font-bold uppercase tracking-wider text-gray-400 sticky top-0 z-10 backdrop-blur-md">
                    <th className="p-3">Task ID</th>
                    <th className="p-3">Priority</th>
                    <th className="p-3">Requirements (CPU/RAM/Storage/Net)</th>
                    <th className="p-3">Execution Time</th>
                    <th className="p-3">Deadline Tick</th>
                    <th className="p-3">Target VM</th>
                    <th className="p-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-white/5 text-xs">
                  {tasks.length === 0 ? (
                    <tr>
                      <td colSpan={7} className="p-8 text-center text-gray-500 font-semibold">
                        No active workload tasks. Click a generate button above to queue synthetic big data processing runs.
                      </td>
                    </tr>
                  ) : (
                    [...tasks].reverse().slice(0, 100).map((task) => {
                      let statusBadge = 'bg-gray-500/10 text-gray-400';
                      if (task.status === 'RUNNING') statusBadge = 'bg-accent-green/10 text-accent-green animate-pulse';
                      else if (task.status === 'COMPLETED') statusBadge = 'bg-green-500/10 text-green-400';
                      else if (task.status === 'FAILED') statusBadge = 'bg-accent-red/10 text-accent-red';

                      let priorityBadge = 'bg-blue-500/10 text-blue-400';
                      if (task.priority === 'HIGH') priorityBadge = 'bg-red-500/10 text-red-400 font-bold';
                      else if (task.priority === 'MEDIUM') priorityBadge = 'bg-yellow-500/10 text-yellow-400';

                      return (
                        <tr key={task.id} className="hover:bg-white/[0.01] transition-colors border-b border-white/5">
                          <td className="p-3 font-mono font-bold text-white">#TSK-{task.id}</td>
                          <td className="p-3">
                            <span className={`inline-flex px-2 py-0.5 rounded text-3xs font-bold uppercase ${priorityBadge}`}>
                              {task.priority}
                            </span>
                          </td>
                          <td className="p-3 font-medium text-gray-300">
                            {task.cpu_requirement} Cores / {(task.ram_requirement / 1000).toFixed(1)} GB / {task.storage_requirement} GB / {task.bandwidth_requirement} Mbps
                          </td>
                          <td className="p-3 font-mono font-bold text-white">
                            {task.execution_time} ticks
                          </td>
                          <td className="p-3 font-mono text-gray-400">Tick #{task.deadline}</td>
                          <td className="p-3">
                            {task.vm_id !== null ? (
                              <span className="font-semibold text-primary">VM #{task.vm_id}</span>
                            ) : (
                              <span className="text-gray-600">—</span>
                            )}
                          </td>
                          <td className="p-3">
                            <span className={`inline-flex px-2.5 py-0.5 rounded-full text-3xs font-semibold ${statusBadge}`}>
                              {task.status}
                            </span>
                          </td>
                        </tr>
                      );
                    })
                  )}
                </tbody>
              </table>
            </div>
            {tasks.length > 100 && (
              <div className="p-2.5 text-center border-t border-white/5 text-3xs text-gray-500 font-semibold bg-white/[0.01]">
                Showing first 100 tasks out of {tasks.length} total.
              </div>
            )}
          </div>
        </div>

      </main>

      {/* Modal 1: Provision New Host Server */}
      <AnimatePresence>
        {showAddModal && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div 
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowAddModal(false)}
            />
            
            <motion.div 
              className="glass-panel w-full max-w-md rounded-2xl p-6 relative shadow-glass overflow-hidden z-10 border border-white/10"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
            >
              <h3 className="text-lg font-bold text-white mb-4">Provision Infrastructure Host Node</h3>
              
              <form onSubmit={handleAddServer} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">CPU Cores</label>
                    <input 
                      type="number"
                      value={newCpu}
                      onChange={(e) => setNewCpu(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={2} max={128} required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">Frequency (GHz)</label>
                    <input 
                      type="number" step="0.1"
                      value={newFreq}
                      onChange={(e) => setNewFreq(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={1.0} max={5.0} required
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">Memory Allocation (MB)</label>
                  <input 
                    type="number"
                    value={newRam}
                    onChange={(e) => setNewRam(Number(e.target.value))}
                    className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                    min={4000} required
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">Storage Capacity (GB)</label>
                    <input 
                      type="number"
                      value={newStorage}
                      onChange={(e) => setNewStorage(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={100} required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">Link Bandwidth (Mbps)</label>
                    <input 
                      type="number"
                      value={newBandwidth}
                      onChange={(e) => setNewBandwidth(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={1000} required
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowAddModal(false)}
                    className="w-1/2 py-2 px-4 border border-white/10 hover:bg-white/5 rounded-lg text-sm text-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="w-1/2 py-2 px-4 bg-gradient-to-r from-primary to-primary-dark text-background font-bold rounded-lg text-sm hover:scale-[1.01] active:scale-[0.99] transition-transform"
                  >
                    Provision Node
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>

      {/* Modal 2: Deploy VM on Server */}
      <AnimatePresence>
        {showVmModal !== null && (
          <div className="fixed inset-0 z-50 flex items-center justify-center px-4">
            <motion.div 
              className="absolute inset-0 bg-black/60 backdrop-blur-sm"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              onClick={() => setShowVmModal(null)}
            />

            <motion.div 
              className="glass-panel w-full max-w-md rounded-2xl p-6 relative shadow-glass overflow-hidden z-10 border border-white/10"
              initial={{ scale: 0.95, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 0.95, opacity: 0 }}
            >
              <h3 className="text-lg font-bold text-white mb-4">Deploy Virtual Machine on Node #{showVmModal}</h3>

              <form onSubmit={handleDeployVm} className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">vCPU Cores</label>
                    <input 
                      type="number"
                      value={vmCpu}
                      onChange={(e) => setVmCpu(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={1} required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">vRAM Allocation (MB)</label>
                    <input 
                      type="number"
                      value={vmRam}
                      onChange={(e) => setVmRam(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={512} required
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">vDisk Capacity (GB)</label>
                    <input 
                      type="number"
                      value={vmStorage}
                      onChange={(e) => setVmStorage(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={10} required
                    />
                  </div>
                  <div className="space-y-1.5">
                    <label className="text-3xs text-gray-400 font-bold uppercase tracking-wider">Link Bandwidth (Mbps)</label>
                    <input 
                      type="number"
                      value={vmBandwidth}
                      onChange={(e) => setVmBandwidth(Number(e.target.value))}
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-lg p-2 text-sm text-white"
                      min={100} required
                    />
                  </div>
                </div>

                <div className="flex items-center space-x-3 pt-3">
                  <button
                    type="button"
                    onClick={() => setShowVmModal(null)}
                    className="w-1/2 py-2 px-4 border border-white/10 hover:bg-white/5 rounded-lg text-sm text-gray-400"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="w-1/2 py-2 px-4 bg-gradient-to-r from-primary to-primary-dark text-background font-bold rounded-lg text-sm hover:scale-[1.01] active:scale-[0.99] transition-transform"
                  >
                    Deploy VM Instance
                  </button>
                </div>
              </form>
            </motion.div>
          </div>
        )}
      </AnimatePresence>
    </div>
  );
};
export default Servers;
