import { useState, useEffect, useCallback } from 'react';
import {
  AreaChart, Area, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell, RadialBarChart, RadialBar,
} from 'recharts';
import type { GlobalTelemetryLog, HostTelemetryLog, DataCenterPowerProfile } from '../types/monitoring';
import type { PhysicalServer } from '../types/simulation';
import { simulationService } from '../services/simulation_service';
import { ReportsDownloader } from '../components/ReportsDownloader';

// ─── Colour palette ────────────────────────────────────────────────────────────
const P = {
  cpu:      '#6366f1',
  ram:      '#22d3ee',
  storage:  '#f59e0b',
  network:  '#a78bfa',
  it:       '#34d399',
  cooling:  '#f472b6',
  standby:  '#94a3b8',
  total:    '#fb923c',
  carbon:   '#4ade80',
  temp:     '#f87171',
  pue:      '#818cf8',
};

// ─── Custom Tooltip ────────────────────────────────────────────────────────────
const ChartTooltip = ({ active, payload, label }: any) => {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: 'rgba(15,23,42,0.97)',
      border: '1px solid rgba(99,102,241,0.35)',
      borderRadius: 12, padding: '10px 16px',
      boxShadow: '0 8px 32px rgba(0,0,0,0.5)', fontSize: 12,
    }}>
      <p style={{ color: '#94a3b8', marginBottom: 6, fontWeight: 600 }}>Tick {label}</p>
      {payload.map((e: any) => (
        <div key={e.name} style={{ display: 'flex', justifyContent: 'space-between', gap: 24, color: e.color }}>
          <span>{e.name}</span>
          <span style={{ fontWeight: 700 }}>{typeof e.value === 'number' ? e.value.toFixed(3) : e.value}</span>
        </div>
      ))}
    </div>
  );
};

// ─── KPI Card ─────────────────────────────────────────────────────────────────
const KpiCard = ({ label, value, sub, color, icon }: { label: string; value: string; sub?: string; color: string; icon: string }) => (
  <div style={{
    background: 'rgba(15,23,42,0.7)', border: `1px solid ${color}30`,
    borderRadius: 16, padding: '20px 24px',
    display: 'flex', flexDirection: 'column', gap: 8,
    position: 'relative', overflow: 'hidden', backdropFilter: 'blur(12px)',
    flex: '1 1 160px', minWidth: 140,
  }}>
    <div style={{ position: 'absolute', top: -12, right: -12, width: 80, height: 80, borderRadius: '50%', background: `${color}12` }} />
    <span style={{ fontSize: 22 }}>{icon}</span>
    <span style={{ fontSize: 11, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.08em', fontWeight: 600 }}>{label}</span>
    <span style={{ fontSize: 22, fontWeight: 800, color: '#f1f5f9', lineHeight: 1 }}>{value}</span>
    {sub && <span style={{ fontSize: 11, color: '#64748b' }}>{sub}</span>}
    <div style={{ position: 'absolute', bottom: 0, left: 0, right: 0, height: 2, background: `linear-gradient(90deg, ${color}, transparent)` }} />
  </div>
);

// ─── Chart Card wrapper ────────────────────────────────────────────────────────
const ChartCard = ({ title, subtitle, children }: { title: string; subtitle?: string; children: React.ReactNode }) => (
  <div style={{
    background: 'rgba(15,23,42,0.7)', border: '1px solid rgba(99,102,241,0.2)',
    borderRadius: 20, padding: '24px 28px',
    backdropFilter: 'blur(16px)', boxShadow: '0 4px 40px rgba(0,0,0,0.4)',
  }}>
    <div style={{ marginBottom: 20 }}>
      <h3 style={{ fontSize: 16, fontWeight: 700, color: '#e2e8f0', margin: 0 }}>{title}</h3>
      {subtitle && <p style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{subtitle}</p>}
    </div>
    {children}
  </div>
);

// ─── Empty chart placeholder ──────────────────────────────────────────────────
const EmptyChart = () => (
  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: 220, color: '#475569', gap: 8 }}>
    <span style={{ fontSize: 40 }}>📊</span>
    <p style={{ fontSize: 13, fontWeight: 500 }}>No data yet — advance the simulation clock to begin recording telemetry.</p>
  </div>
);

// ─── PUE Arc Gauge ────────────────────────────────────────────────────────────
const PUEGauge = ({ pue, rating }: { pue: number; rating: string }) => {
  const pueMin = 1.0, pueMax = 2.5;
  const pct = Math.min(100, Math.max(0, ((pue - pueMin) / (pueMax - pueMin)) * 100));
  const color = pue <= 1.2 ? '#34d399' : pue <= 1.5 ? '#86efac' : pue <= 1.8 ? '#f59e0b' : '#f87171';
  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 4 }}>
      <div style={{ position: 'relative', width: 200, height: 110 }}>
        <RadialBarChart
          width={200} height={110}
          innerRadius={55} outerRadius={80}
          startAngle={180} endAngle={0}
          data={[{ value: pct }]}
        >
          <RadialBar background={{ fill: 'rgba(255,255,255,0.04)' }} dataKey="value" fill={color} cornerRadius={8} />
        </RadialBarChart>
        <div style={{ position: 'absolute', bottom: 0, left: '50%', transform: 'translateX(-50%)', textAlign: 'center' }}>
          <div style={{ fontSize: 28, fontWeight: 900, color, lineHeight: 1 }}>{pue.toFixed(3)}</div>
          <div style={{ fontSize: 11, color: '#64748b', marginTop: 2 }}>PUE</div>
        </div>
      </div>
      <span style={{ fontSize: 12, fontWeight: 700, color, background: `${color}18`, padding: '4px 12px', borderRadius: 20, border: `1px solid ${color}40` }}>{rating}</span>
      <div style={{ fontSize: 11, color: '#475569', marginTop: 6, textAlign: 'center', lineHeight: 1.7 }}>
        <div>🟢 &le; 1.20 &nbsp;Excellent (Google/Hyperscale)</div>
        <div>🟡 &le; 1.50 &nbsp;Good (Modern DC)</div>
        <div>🟠 &le; 1.80 &nbsp;Average (Industry ~1.58)</div>
        <div>🔴 &gt; 1.80 &nbsp;Poor (Legacy DC)</div>
      </div>
    </div>
  );
};

// ─── Power Donut ──────────────────────────────────────────────────────────────
const PowerDonut = ({ it, cooling, standby }: { it: number; cooling: number; standby: number }) => {
  const total = it + cooling + standby;
  if (total === 0) return <EmptyChart />;
  const data = [
    { name: 'IT Load', value: it, color: P.it },
    { name: 'Cooling', value: cooling, color: P.cooling },
    { name: 'Standby', value: standby, color: P.standby },
  ];
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 24, flexWrap: 'wrap', justifyContent: 'center' }}>
      <PieChart width={180} height={180}>
        <Pie data={data} cx={85} cy={85} innerRadius={50} outerRadius={80} dataKey="value" strokeWidth={0}>
          {data.map((d, i) => <Cell key={i} fill={d.color} />)}
        </Pie>
        <Tooltip formatter={(v: any) => `${v.toFixed(1)} W`} contentStyle={{ background: '#0f172a', border: '1px solid #334155', borderRadius: 8 }} />
      </PieChart>
      <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        {data.map(d => (
          <div key={d.name} style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <div style={{ width: 10, height: 10, borderRadius: '50%', background: d.color, flexShrink: 0 }} />
            <div>
              <div style={{ fontSize: 12, color: '#94a3b8', fontWeight: 600 }}>{d.name}</div>
              <div style={{ fontSize: 14, color: '#f1f5f9', fontWeight: 800 }}>
                {d.value.toFixed(1)} W
                <span style={{ fontSize: 11, color: '#64748b', marginLeft: 6 }}>({((d.value / total) * 100).toFixed(1)}%)</span>
              </div>
            </div>
          </div>
        ))}
        <div style={{ borderTop: '1px solid rgba(255,255,255,0.08)', paddingTop: 8, marginTop: 4 }}>
          <div style={{ fontSize: 11, color: '#64748b' }}>Total Facility</div>
          <div style={{ fontSize: 16, fontWeight: 800, color: P.total }}>{total.toFixed(1)} W</div>
        </div>
      </div>
    </div>
  );
};

// ─── Power progress bar ───────────────────────────────────────────────────────
const PowerBar = ({ value, max, color }: { value: number; max: number; color: string }) => (
  <div style={{ background: 'rgba(255,255,255,0.06)', borderRadius: 4, height: 6, width: '100%' }}>
    <div style={{ width: `${Math.min(100, (value / max) * 100)}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.4s ease' }} />
  </div>
);

const stateColors: Record<string, string> = { ACTIVE: '#34d399', SLEEP: '#f59e0b', OFF: '#94a3b8' };

// ─── Main Analytics Component ─────────────────────────────────────────────────
export default function Analytics() {
  const [subTab, setSubTab] = useState<'monitor' | 'power'>('monitor');
  const [globalLogs, setGlobalLogs] = useState<GlobalTelemetryLog[]>([]);
  const [servers, setServers] = useState<PhysicalServer[]>([]);
  const [selectedHostId, setSelectedHostId] = useState<number | null>(null);
  const [hostLogs, setHostLogs] = useState<HostTelemetryLog[]>([]);
  const [powerProfile, setPowerProfile] = useState<DataCenterPowerProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [lastRefresh, setLastRefresh] = useState<string>('');

  const fetchMonitorData = useCallback(async () => {
    try {
      const [logs, srvs] = await Promise.all([
        simulationService.getGlobalLogs(200),
        simulationService.getServers(),
      ]);
      setGlobalLogs(logs);
      setServers(srvs);
      if (!selectedHostId && srvs.length > 0) setSelectedHostId(srvs[0].id);
      setLastRefresh(new Date().toLocaleTimeString());
    } catch (err) { console.error('Analytics fetch error:', err); }
    finally { setLoading(false); }
  }, [selectedHostId]);

  const fetchPowerData = useCallback(async () => {
    try {
      const profile = await simulationService.getPowerProfile();
      setPowerProfile(profile);
    } catch (err) { console.error('Power profile fetch error:', err); }
  }, []);

  const fetchHostLogs = useCallback(async (id: number) => {
    try {
      const logs = await simulationService.getHostLogs(id, 200);
      setHostLogs(logs);
    } catch (err) { console.error('Host log fetch error:', err); }
  }, []);

  useEffect(() => { fetchMonitorData(); fetchPowerData(); }, []);
  useEffect(() => { if (selectedHostId !== null) fetchHostLogs(selectedHostId); }, [selectedHostId]);

  const handleRefresh = async () => {
    setLoading(true);
    await Promise.all([fetchMonitorData(), fetchPowerData()]);
    if (selectedHostId !== null) await fetchHostLogs(selectedHostId);
  };

  const latest = globalLogs.length > 0 ? globalLogs[globalLogs.length - 1] : null;

  if (loading && globalLogs.length === 0) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center', background: '#020817', color: '#fff' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: 40, marginBottom: 12 }}>📡</div>
          <div style={{ fontSize: 16, color: '#94a3b8' }}>Loading telemetry…</div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ minHeight: '100vh', background: '#020817', color: '#f1f5f9', fontFamily: "'Inter', sans-serif", paddingBottom: 80 }}>
      <div style={{ position: 'fixed', top: 0, right: 0, width: 600, height: 600, borderRadius: '50%', background: 'radial-gradient(circle, rgba(99,102,241,0.05) 0%, transparent 70%)', pointerEvents: 'none', zIndex: 0 }} />

      <div style={{ maxWidth: 1400, margin: '0 auto', padding: '28px 24px', position: 'relative', zIndex: 1 }}>

        {/* Page header */}
        <div style={{ display: 'flex', alignItems: 'flex-end', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, marginBottom: 32 }}>
          <div>
            <h2 style={{ fontSize: 26, fontWeight: 900, color: '#f1f5f9', margin: 0, letterSpacing: '-0.03em' }}>
              Analytics &amp; Power Intelligence
            </h2>
            <p style={{ fontSize: 13, color: '#64748b', marginTop: 6 }}>
              Energy-proportional monitoring &mdash; {globalLogs.length} telemetry snapshots recorded
            </p>
          </div>
          <button onClick={handleRefresh} style={{ padding: '8px 18px', borderRadius: 10, border: '1px solid rgba(99,102,241,0.3)', background: 'rgba(99,102,241,0.1)', color: '#a5b4fc', fontSize: 13, fontWeight: 600, cursor: 'pointer' }}>
            &#8635; Refresh {lastRefresh && <span style={{ color: '#475569' }}> &middot; {lastRefresh}</span>}
          </button>
        </div>

        {/* Executive Summary & Reports Downloader Widget */}
        <div style={{ marginBottom: 28 }}>
          <ReportsDownloader />
        </div>

        {/* Sub-tab pills */}
        <div style={{ display: 'flex', gap: 4, background: 'rgba(255,255,255,0.04)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 14, padding: 4, marginBottom: 32, width: 'fit-content' }}>
          {([
            { id: 'monitor', label: '📊  Resource Monitor' },
            { id: 'power',   label: '⚡  Power Engine' },
          ] as { id: 'monitor'|'power'; label: string }[]).map(t => (
            <button key={t.id} onClick={() => setSubTab(t.id)} style={{
              padding: '8px 20px', borderRadius: 10, border: 'none', cursor: 'pointer', fontSize: 13,
              background: subTab === t.id ? 'rgba(99,102,241,0.25)' : 'transparent',
              color: subTab === t.id ? '#c7d2fe' : '#64748b',
              fontWeight: subTab === t.id ? 700 : 500, transition: 'all 0.2s',
              boxShadow: subTab === t.id ? '0 0 0 1px rgba(99,102,241,0.35)' : 'none',
            }}>{t.label}</button>
          ))}
        </div>

        {/* ── RESOURCE MONITOR ─────────────────────────────────────────────────── */}
        {subTab === 'monitor' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            {/* KPI row */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: 14 }}>
              <KpiCard icon="🕐" label="Simulation Ticks"   value={String(latest?.tick ?? 0)}                               color={P.cpu}     />
              <KpiCard icon="⚡" label="Total Energy"       value={`${(latest?.total_energy_kwh ?? 0).toFixed(5)} kWh`}     color={P.total}   />
              <KpiCard icon="💡" label="IT Power Draw"      value={`${(latest?.it_power_w ?? 0).toFixed(1)} W`}             color={P.it}      />
              <KpiCard icon="❄️" label="Cooling Power"      value={`${(latest?.cooling_power_w ?? 0).toFixed(1)} W`}        color={P.cooling} />
              <KpiCard icon="🌍" label="Carbon Emissions"   value={`${(latest?.carbon_emissions_kg ?? 0).toFixed(6)} kg`}   sub="CO₂ equiv." color={P.carbon} />
              <KpiCard icon="📈" label="PUE"                value={latest?.pue ? latest.pue.toFixed(3) : '—'}                sub="Facility efficiency" color={P.pue} />
            </div>

            <ChartCard title="Resource Utilisation Over Time" subtitle="Averaged across all active hosts per simulation tick">
              {globalLogs.length === 0 ? <EmptyChart /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={globalLogs} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                    <defs>
                      {([['cpu', P.cpu], ['ram', P.ram], ['storage', P.storage], ['network', P.network]] as [string,string][]).map(([k, c]) => (
                        <linearGradient key={k} id={`g-${k}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={c} stopOpacity={0.35} />
                          <stop offset="95%" stopColor={c} stopOpacity={0.02} />
                        </linearGradient>
                      ))}
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                    <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} domain={[0, 1]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
                    <Tooltip content={<ChartTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                    <Area type="monotone" dataKey="cpu_utilization"       name="CPU %"       stroke={P.cpu}     fill="url(#g-cpu)"     strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="ram_utilization"       name="RAM %"       stroke={P.ram}     fill="url(#g-ram)"     strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="storage_utilization"   name="Storage %"   stroke={P.storage} fill="url(#g-storage)" strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="bandwidth_utilization" name="Bandwidth %"  stroke={P.network} fill="url(#g-network)" strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <ChartCard title="Power Consumption Breakdown" subtitle="IT power, cooling overhead, and total facility draw (Watts)">
              {globalLogs.length === 0 ? <EmptyChart /> : (
                <ResponsiveContainer width="100%" height={240}>
                  <AreaChart data={globalLogs} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                    <defs>
                      {([['it', P.it], ['cooling', P.cooling], ['total', P.total]] as [string,string][]).map(([k, c]) => (
                        <linearGradient key={k} id={`gp-${k}`} x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor={c} stopOpacity={0.4} />
                          <stop offset="95%" stopColor={c} stopOpacity={0.02} />
                        </linearGradient>
                      ))}
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                    <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                    <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v: number) => `${v}W`} />
                    <Tooltip content={<ChartTooltip />} />
                    <Legend wrapperStyle={{ fontSize: 12, color: '#94a3b8' }} />
                    <Area type="monotone" dataKey="it_power_w"     name="IT Power (W)"  stroke={P.it}     fill="url(#gp-it)"     strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="cooling_power_w" name="Cooling (W)"   stroke={P.cooling} fill="url(#gp-cooling)" strokeWidth={2} dot={false} />
                    <Area type="monotone" dataKey="total_power_w"   name="Total (W)"     stroke={P.total}  fill="url(#gp-total)"  strokeWidth={2} dot={false} />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </ChartCard>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(380px, 1fr))', gap: 24 }}>
              <ChartCard title="Cumulative Energy Consumption" subtitle="Total kWh accumulated since simulation start">
                {globalLogs.length === 0 ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={globalLogs} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                      <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(5)} />
                      <Tooltip content={<ChartTooltip />} />
                      <Line type="monotone" dataKey="total_energy_kwh" name="Energy (kWh)" stroke={P.total} strokeWidth={2.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
              <ChartCard title="Carbon Emissions" subtitle="CO₂ equivalent (kg) · 0.4 kg CO₂/kWh grid factor">
                {globalLogs.length === 0 ? <EmptyChart /> : (
                  <ResponsiveContainer width="100%" height={220}>
                    <LineChart data={globalLogs} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                      <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                      <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} tickFormatter={(v: number) => v.toFixed(6)} />
                      <Tooltip content={<ChartTooltip />} />
                      <Line type="monotone" dataKey="carbon_emissions_kg" name="Carbon (kg CO₂)" stroke={P.carbon} strokeWidth={2.5} dot={false} />
                    </LineChart>
                  </ResponsiveContainer>
                )}
              </ChartCard>
            </div>

            {/* Per-host drilldown */}
            <ChartCard title="Per-Server Telemetry Drilldown" subtitle="Select a host to inspect its CPU/RAM load, temperature and power draw over time">
              {servers.length === 0 ? <EmptyChart /> : (
                <>
                  <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', marginBottom: 24 }}>
                    {servers.map(s => (
                      <button key={s.id} onClick={() => { setSelectedHostId(s.id); fetchHostLogs(s.id); }} style={{
                        padding: '6px 14px', borderRadius: 8, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                        background: selectedHostId === s.id ? 'rgba(99,102,241,0.25)' : 'rgba(255,255,255,0.05)',
                        color: selectedHostId === s.id ? '#c7d2fe' : '#94a3b8',
                        boxShadow: selectedHostId === s.id ? '0 0 0 1px rgba(99,102,241,0.4)' : 'none', transition: 'all 0.15s',
                      }}>
                        Host #{s.id} <span style={{ fontSize: 10, opacity: 0.6 }}>· {s.power_state}</span>
                      </button>
                    ))}
                  </div>
                  {hostLogs.length === 0 ? <EmptyChart /> : (
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(360px, 1fr))', gap: 24 }}>
                      <div>
                        <p style={{ fontSize: 12, color: '#64748b', marginBottom: 12, fontWeight: 600 }}>CPU &amp; RAM Utilisation</p>
                        <ResponsiveContainer width="100%" height={180}>
                          <AreaChart data={hostLogs} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} />
                            <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} domain={[0, 1]} tickFormatter={(v: number) => `${(v * 100).toFixed(0)}%`} />
                            <Tooltip content={<ChartTooltip />} />
                            <Area type="monotone" dataKey="cpu_utilization" name="CPU %" stroke={P.cpu} fill={`${P.cpu}22`} strokeWidth={2} dot={false} />
                            <Area type="monotone" dataKey="ram_utilization" name="RAM %" stroke={P.ram} fill={`${P.ram}22`} strokeWidth={2} dot={false} />
                          </AreaChart>
                        </ResponsiveContainer>
                      </div>
                      <div>
                        <p style={{ fontSize: 12, color: '#64748b', marginBottom: 12, fontWeight: 600 }}>Temperature &amp; Power Draw</p>
                        <ResponsiveContainer width="100%" height={180}>
                          <LineChart data={hostLogs} margin={{ top: 4, right: 8, left: 0, bottom: 0 }}>
                            <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                            <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} />
                            <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 10 }} />
                            <Tooltip content={<ChartTooltip />} />
                            <Legend wrapperStyle={{ fontSize: 11, color: '#94a3b8' }} />
                            <Line type="monotone" dataKey="temperature"         name="Temp (°C)" stroke={P.temp}  strokeWidth={2} dot={false} />
                            <Line type="monotone" dataKey="power_consumption_w" name="Power (W)"  stroke={P.total} strokeWidth={2} dot={false} />
                          </LineChart>
                        </ResponsiveContainer>
                      </div>
                    </div>
                  )}
                </>
              )}
            </ChartCard>
          </div>
        )}

        {/* ── POWER ENGINE TAB ─────────────────────────────────────────────────── */}
        {subTab === 'power' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 28 }}>
            {!powerProfile ? (
              <div style={{ textAlign: 'center', paddingTop: 80, color: '#475569' }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>⚡</div>
                <p>No power profile data yet. Advance the simulation clock then refresh.</p>
              </div>
            ) : (
              <>
                {/* PUE Gauge + Donut */}
                <div style={{ display: 'grid', gridTemplateColumns: 'minmax(240px,320px) 1fr', gap: 24, alignItems: 'start' }}>
                  <ChartCard title="PUE Gauge" subtitle="Power Usage Effectiveness (facility ÷ IT power)">
                    <PUEGauge pue={powerProfile.summary.pue} rating={powerProfile.summary.pue_rating} />
                  </ChartCard>
                  <ChartCard title="Facility Power Breakdown" subtitle="Real-time distribution across IT load, cooling, and standby">
                    <PowerDonut
                      it={powerProfile.summary.it_power_w}
                      cooling={powerProfile.summary.cooling_power_w}
                      standby={powerProfile.summary.standby_power_w}
                    />
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 10, marginTop: 20 }}>
                      {[
                        { label: 'Total Facility', value: `${powerProfile.summary.total_facility_w.toFixed(1)} W`, color: P.total },
                        { label: 'Cooling Overhead', value: `${powerProfile.summary.cooling_overhead_pct.toFixed(0)}%`, color: P.cooling },
                        { label: 'IT Power',  value: `${powerProfile.summary.it_power_w.toFixed(1)} W`,  color: P.it },
                        { label: 'Standby',   value: `${powerProfile.summary.standby_power_w.toFixed(1)} W`, color: P.standby },
                      ].map(item => (
                        <div key={item.label} style={{ flex: '1 1 120px', background: `${item.color}12`, border: `1px solid ${item.color}30`, borderRadius: 12, padding: '12px 16px' }}>
                          <div style={{ fontSize: 10, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.06em', fontWeight: 600 }}>{item.label}</div>
                          <div style={{ fontSize: 18, fontWeight: 800, color: item.color, marginTop: 4 }}>{item.value}</div>
                        </div>
                      ))}
                    </div>
                  </ChartCard>
                </div>

                {/* PUE Trend */}
                <ChartCard title="PUE Trend Over Time" subtitle="Power Usage Effectiveness per simulation tick — industry benchmark: 1.58 average, 1.10 hyperscale">
                  {powerProfile.pue_history.length === 0 ? <EmptyChart /> : (
                    <ResponsiveContainer width="100%" height={220}>
                      <LineChart data={powerProfile.pue_history} margin={{ top: 4, right: 12, left: 0, bottom: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                        <XAxis dataKey="tick" stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} />
                        <YAxis stroke="#334155" tick={{ fill: '#64748b', fontSize: 11 }} domain={[1.0, 'auto']} tickFormatter={(v: number) => v.toFixed(2)} />
                        <Tooltip content={<ChartTooltip />} />
                        <Line type="monotone" dataKey="pue" name="PUE" stroke={P.pue} strokeWidth={2.5} dot={false} />
                      </LineChart>
                    </ResponsiveContainer>
                  )}
                </ChartCard>

                {/* Per-server profile table */}
                <ChartCard title="Per-Server Power Profiles" subtitle="Real-time power draw per host with model metadata and efficiency rating">
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)' }}>
                          {['Host', 'State', 'Power Model', 'Idle (W)', 'Peak (W)', 'Current (W)', 'CPU Load', 'Efficiency'].map(h => (
                            <th key={h} style={{ padding: '10px 14px', textAlign: 'left', color: '#64748b', fontWeight: 600, fontSize: 11, letterSpacing: '0.05em', textTransform: 'uppercase' }}>{h}</th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {powerProfile.hosts.map((h, i) => {
                          const effColor = h.efficiency_pct > 70 ? P.it : h.efficiency_pct > 40 ? P.total : P.standby;
                          return (
                            <tr key={h.host_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)', background: i % 2 === 0 ? 'transparent' : 'rgba(255,255,255,0.02)' }}>
                              <td style={{ padding: '12px 14px', fontWeight: 700, color: '#e2e8f0' }}>Host #{h.host_id}</td>
                              <td style={{ padding: '12px 14px' }}>
                                <span style={{ fontSize: 11, fontWeight: 700, padding: '3px 10px', borderRadius: 20, background: `${stateColors[h.power_state] || '#94a3b8'}18`, color: stateColors[h.power_state] || '#94a3b8', border: `1px solid ${stateColors[h.power_state] || '#94a3b8'}30` }}>
                                  {h.power_state}
                                </span>
                              </td>
                              <td style={{ padding: '12px 14px', color: '#a5b4fc', fontStyle: 'italic' }}>{h.model_name}</td>
                              <td style={{ padding: '12px 14px', color: '#94a3b8' }}>{h.idle_power_w.toFixed(1)}</td>
                              <td style={{ padding: '12px 14px', color: '#94a3b8' }}>{h.peak_power_w.toFixed(1)}</td>
                              <td style={{ padding: '12px 14px' }}>
                                <div style={{ fontWeight: 800, color: '#f1f5f9', marginBottom: 4 }}>{h.current_power_w.toFixed(1)} W</div>
                                <PowerBar value={h.current_power_w} max={h.peak_power_w} color={P.it} />
                              </td>
                              <td style={{ padding: '12px 14px', color: '#94a3b8' }}>{(h.cpu_utilization * 100).toFixed(1)}%</td>
                              <td style={{ padding: '12px 14px' }}>
                                <span style={{ fontWeight: 700, color: effColor }}>{h.efficiency_pct.toFixed(1)}%</span>
                                <div style={{ fontSize: 10, color: '#475569', marginTop: 2 }}>of peak</div>
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </ChartCard>

                {/* Model reference panel */}
                <ChartCard title="Power Model Reference" subtitle="Research citations for the models implemented in this simulation engine">
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: 16 }}>
                    {[
                      { name: 'Linear', formula: 'P(u) = P_idle + (P_peak \u2212 P_idle) \u00d7 u', ref: 'Standard simulation baseline', color: P.cpu, icon: '📏', desc: 'Simple linear model. Underestimates power at medium loads but useful as a baseline for comparison.' },
                      { name: 'Cubic (Barroso-Hölzle)', formula: 'P(u) = P_idle + (P_peak \u2212 P_idle) \u00d7 u^2.5', ref: 'IEEE Computer, 40(12), 2007', color: P.pue, icon: '🔬', desc: 'Validated super-linear model. At 50% CPU load, servers typically consume ~70% of peak power.' },
                      { name: 'SPECpower (piecewise)', formula: 'P = peak \u00d7 SPEC_table_interp(u)', ref: 'SPECpower_ssj2008 benchmark avg', color: P.carbon, icon: '🏭', desc: 'Derived from real hardware measurements across 200+ submissions. Most accurate for production workloads.' },
                    ].map(m => (
                      <div key={m.name} style={{ background: `${m.color}08`, border: `1px solid ${m.color}25`, borderRadius: 14, padding: '16px 20px' }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
                          <span style={{ fontSize: 20 }}>{m.icon}</span>
                          <div>
                            <div style={{ fontWeight: 700, color: m.color, fontSize: 14 }}>{m.name}</div>
                            <div style={{ fontSize: 10, color: '#475569' }}>{m.ref}</div>
                          </div>
                        </div>
                        <code style={{ fontSize: 11, color: '#94a3b8', display: 'block', background: 'rgba(0,0,0,0.3)', padding: '6px 10px', borderRadius: 8, marginBottom: 10 }}>
                          {m.formula}
                        </code>
                        <p style={{ fontSize: 12, color: '#64748b', margin: 0, lineHeight: 1.6 }}>{m.desc}</p>
                      </div>
                    ))}
                  </div>
                </ChartCard>
              </>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
