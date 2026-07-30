import React, { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { Cpu, Zap, Brain, RotateCcw, Minimize2, Check, Sparkles } from 'lucide-react';
import { simulationService } from '../services/simulation_service';

interface SchedulerSelectorProps {
  onSchedulerChanged?: () => void;
}

export const SchedulerSelector: React.FC<SchedulerSelectorProps> = ({ onSchedulerChanged }) => {
  const [activeScheduler, setActiveScheduler] = useState<string>('round_robin');
  const [loading, setLoading] = useState<boolean>(false);
  const [consolidating, setConsolidating] = useState<boolean>(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);

  const schedulers = [
    {
      id: 'round_robin',
      name: 'Round-Robin',
      desc: 'Circular baseline VM distribution',
      icon: RotateCcw,
      color: 'from-blue-500 to-indigo-600',
      badge: 'Baseline',
    },
    {
      id: 'random',
      name: 'Random',
      desc: 'Stochastic uniform random distribution',
      icon: Cpu,
      color: 'from-gray-500 to-slate-600',
      badge: 'Baseline',
    },
    {
      id: 'energy_aware',
      name: 'Energy-Aware (BFD)',
      desc: 'Minimizes power increase & turns idle hosts off',
      icon: Zap,
      color: 'from-emerald-500 to-teal-600',
      badge: 'Recommended',
    },
    {
      id: 'ml',
      name: 'AI/ML Predictive',
      desc: 'Multi-objective thermal & SLA score optimization',
      icon: Brain,
      color: 'from-purple-500 to-cyan-600',
      badge: 'AI Engine',
    },
  ];

  useEffect(() => {
    simulationService.getActiveScheduler().then(res => {
      if (res && res.active_scheduler) {
        setActiveScheduler(res.active_scheduler);
      }
    }).catch(() => {});
  }, []);

  const handleSelect = async (id: string) => {
    if (id === activeScheduler || loading) return;
    setLoading(true);
    setStatusMessage(null);
    try {
      const res = await simulationService.selectScheduler(id);
      setActiveScheduler(id);
      setStatusMessage(res.message);
      if (onSchedulerChanged) onSchedulerChanged();
    } catch (err: any) {
      setStatusMessage(err.message || 'Failed to switch scheduler.');
    } finally {
      setLoading(false);
    }
  };

  const handleConsolidate = async () => {
    setConsolidating(true);
    setStatusMessage(null);
    try {
      const res = await simulationService.consolidateVms();
      setStatusMessage(res.message);
      if (onSchedulerChanged) onSchedulerChanged();
    } catch (err: any) {
      setStatusMessage(err.message || 'Consolidation failed.');
    } finally {
      setConsolidating(false);
    }
  };

  return (
    <div className="glass-panel p-6 rounded-2xl border border-white/10 space-y-4 relative overflow-hidden bg-black/20">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <div className="flex items-center space-x-2">
            <Sparkles className="w-5 h-5 text-primary animate-pulse" />
            <h3 className="text-lg font-extrabold text-white tracking-tight">Resource Scheduler Strategy</h3>
          </div>
          <p className="text-2xs text-gray-400 mt-0.5">
            Select allocation algorithm for VM placement &amp; energy optimization
          </p>
        </div>

        <button
          onClick={handleConsolidate}
          disabled={consolidating}
          className="flex items-center space-x-1.5 px-3.5 py-2 rounded-xl bg-white/5 border border-white/10 text-white font-semibold text-xs hover:bg-white/10 active:scale-95 transition-all disabled:opacity-50 cursor-pointer"
        >
          <Minimize2 className={`w-3.5 h-3.5 ${consolidating ? 'animate-spin' : ''}`} />
          <span>{consolidating ? 'Consolidating...' : 'Consolidate VMs (Sleep Idle Hosts)'}</span>
        </button>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 pt-2">
        {schedulers.map((item) => {
          const isSelected = activeScheduler === item.id;
          const Icon = item.icon;

          return (
            <motion.div
              key={item.id}
              onClick={() => handleSelect(item.id)}
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.98 }}
              className={`p-4 rounded-xl border cursor-pointer transition-all relative overflow-hidden flex flex-col justify-between ${
                isSelected
                  ? 'border-primary bg-primary/10 shadow-lg shadow-primary/10'
                  : 'border-white/5 bg-white/[0.02] hover:border-white/20'
              }`}
            >
              <div>
                <div className="flex items-center justify-between mb-2">
                  <div className={`w-8 h-8 rounded-lg bg-gradient-to-br ${item.color} flex items-center justify-center shadow-md`}>
                    <Icon className="w-4 h-4 text-white" />
                  </div>
                  <span className={`text-4xs font-bold px-2 py-0.5 rounded-full uppercase tracking-wider ${
                    isSelected ? 'bg-primary text-background' : 'bg-white/10 text-gray-400'
                  }`}>
                    {item.badge}
                  </span>
                </div>

                <h4 className="font-bold text-white text-sm flex items-center gap-1.5">
                  {item.name}
                  {isSelected && <Check className="w-3.5 h-3.5 text-primary" />}
                </h4>
                <p className="text-3xs text-gray-400 mt-1 leading-relaxed">
                  {item.desc}
                </p>
              </div>
            </motion.div>
          );
        })}
      </div>

      {statusMessage && (
        <p className="text-3xs text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-3 py-1.5 rounded-lg font-medium">
          {statusMessage}
        </p>
      )}
    </div>
  );
};
export default SchedulerSelector;
