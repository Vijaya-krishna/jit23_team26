import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Download, FileText, FileSpreadsheet, ShieldCheck, Leaf, Gauge, Award } from 'lucide-react';
import { simulationService } from '../services/simulation_service';

export const ReportsDownloader: React.FC = () => {
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [downloadingCsv, setDownloadingCsv] = useState<boolean>(false);
  const [downloadingJson, setDownloadingJson] = useState<boolean>(false);

  const loadSummary = async () => {
    try {
      const data = await simulationService.getSummaryReport();
      setSummary(data);
    } catch (e) {
      // ignore
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadSummary();
  }, []);

  const handleDownloadCsv = async () => {
    setDownloadingCsv(true);
    try {
      await simulationService.downloadCsvReport();
    } catch (e) {
      // ignore
    } finally {
      setDownloadingCsv(false);
    }
  };

  const handleDownloadJson = async () => {
    setDownloadingJson(true);
    try {
      await simulationService.downloadJsonReport();
    } catch (e) {
      // ignore
    } finally {
      setDownloadingJson(false);
    }
  };

  if (loading || !summary) {
    return null;
  }

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-6 relative overflow-hidden bg-black/20">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Award className="w-5 h-5 text-secondary" />
            <h3 className="text-lg font-extrabold text-white tracking-tight">Executive Simulation Report &amp; Data Exporter</h3>
          </div>
          <p className="text-2xs text-gray-400 mt-0.5">
            Audit energy efficiency, PUE score ratings, carbon offset, and export raw logs
          </p>
        </div>

        <div className="flex items-center space-x-2">
          <button
            onClick={handleDownloadCsv}
            disabled={downloadingCsv}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 font-bold text-xs hover:bg-emerald-500/20 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
          >
            <FileSpreadsheet className="w-3.5 h-3.5" />
            <span>{downloadingCsv ? 'Exporting...' : 'Export CSV Telemetry'}</span>
          </button>

          <button
            onClick={handleDownloadJson}
            disabled={downloadingJson}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-cyan-500/10 border border-cyan-500/20 text-cyan-400 font-bold text-xs hover:bg-cyan-500/20 active:scale-95 transition-all cursor-pointer disabled:opacity-50"
          >
            <FileText className="w-3.5 h-3.5" />
            <span>{downloadingJson ? 'Exporting...' : 'Export JSON Snapshot'}</span>
          </button>
        </div>
      </div>

      {/* Summary KPI Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
          <div className="flex items-center space-x-2 text-2xs text-gray-400 font-bold uppercase tracking-wider mb-1">
            <Gauge className="w-4 h-4 text-primary" />
            <span>Average PUE Rating</span>
          </div>
          <div className="text-2xl font-extrabold text-white">{summary.average_pue}</div>
          <span className="text-4xs text-emerald-400 font-semibold mt-1 inline-block">
            {summary.average_pue < 1.4 ? 'Green Efficient' : 'Standard'}
          </span>
        </div>

        <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
          <div className="flex items-center space-x-2 text-2xs text-gray-400 font-bold uppercase tracking-wider mb-1">
            <Leaf className="w-4 h-4 text-emerald-400" />
            <span>Carbon Avoided</span>
          </div>
          <div className="text-2xl font-extrabold text-emerald-400">{summary.carbon_avoided_kg} kg</div>
          <span className="text-4xs text-gray-500 font-medium mt-1 inline-block">
            CO₂ emissions offset
          </span>
        </div>

        <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
          <div className="flex items-center space-x-2 text-2xs text-gray-400 font-bold uppercase tracking-wider mb-1">
            <ShieldCheck className="w-4 h-4 text-cyan-400" />
            <span>SLA Compliance</span>
          </div>
          <div className="text-2xl font-extrabold text-white">
            {summary.task_metrics?.completion_rate_pct || 100}%
          </div>
          <span className="text-4xs text-cyan-400 font-semibold mt-1 inline-block">
            {summary.task_metrics?.failed || 0} Breaches
          </span>
        </div>

        <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02]">
          <div className="flex items-center space-x-2 text-2xs text-gray-400 font-bold uppercase tracking-wider mb-1">
            <Download className="w-4 h-4 text-yellow-400" />
            <span>Energy Consumed</span>
          </div>
          <div className="text-2xl font-extrabold text-yellow-400">
            {summary.total_energy_kwh} kWh
          </div>
          <span className="text-4xs text-gray-500 font-medium mt-1 inline-block">
            Over {summary.clock_ticks} clock ticks
          </span>
        </div>
      </div>
    </div>
  );
};
export default ReportsDownloader;
