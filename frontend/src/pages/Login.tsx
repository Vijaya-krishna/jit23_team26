import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Server, Shield, Lock, User, Cpu, Activity, AlertCircle, CheckCircle } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export const Login: React.FC = () => {
  const { login, error, clearError, isLoading, isAuthenticated, logout, user } = useAuth();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [formError, setFormError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    clearError();

    if (!username.trim() || !password.trim()) {
      setFormError('Please fill in all credential fields.');
      return;
    }

    try {
      await login(username.trim(), password);
    } catch (err) {
      // Error handled in AuthContext
    }
  };

  return (
    <div className="relative min-h-screen flex items-center justify-center bg-background px-4 overflow-hidden">
      {/* Background radial glow elements */}
      <div className="absolute top-1/4 left-1/4 w-[450px] h-[450px] rounded-full bg-primary/10 blur-[120px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-[500px] h-[500px] rounded-full bg-secondary/10 blur-[130px] pointer-events-none" />

      {/* Decorative floating grids */}
      <div className="absolute inset-0 bg-[linear-gradient(rgba(255,255,255,0.015)_1px,transparent_1px),linear-gradient(90deg,rgba(255,255,255,0.015)_1px,transparent_1px)] bg-[size:32px_32px] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_50%,#000_70%,transparent_100%)] pointer-events-none" />

      <div className="w-full max-w-5xl grid grid-cols-1 md:grid-cols-12 gap-8 items-center z-10">
        
        {/* Left Side: Product Branding & Research Context */}
        <motion.div 
          className="md:col-span-7 text-left space-y-6 hidden md:block pr-6"
          initial={{ opacity: 0, x: -40 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="inline-flex items-center space-x-2 px-3 py-1 rounded-full bg-primary/10 border border-primary/20 text-primary text-xs font-semibold tracking-wider uppercase mb-2">
            <Activity className="w-3.5 h-3.5 animate-pulse" />
            <span>Research Simulation Framework</span>
          </div>
          
          <h1 className="text-4xl lg:text-5xl font-extrabold tracking-tight text-white leading-tight">
            Energy-Aware <span className="text-transparent bg-clip-text bg-gradient-to-r from-primary to-primary-light">Resource Allocation</span> in Big Data Centers
          </h1>
          
          <p className="text-gray-400 text-base leading-relaxed max-w-lg">
            An intelligent AI-powered scheduling and workload management platform designed to orchestrate virtual machine allocation, reduce energy waste, minimize carbon footprint, and maintain performance SLAs.
          </p>

          <div className="grid grid-cols-2 gap-4 pt-4">
            <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-sm">
              <Cpu className="w-6 h-6 text-primary mb-2" />
              <h3 className="text-sm font-semibold text-white">Dynamic Scheduling</h3>
              <p className="text-xs text-gray-500 mt-1">Real-time VM consolidation and active state power scaling.</p>
            </div>
            <div className="p-4 rounded-xl border border-white/5 bg-white/[0.02] backdrop-blur-sm">
              <Server className="w-6 h-6 text-secondary mb-2" />
              <h3 className="text-sm font-semibold text-white">Energy Auditing</h3>
              <p className="text-xs text-gray-500 mt-1">Accurate monitoring of idle power, dynamic loads, and cooling costs.</p>
            </div>
          </div>
        </motion.div>

        {/* Right Side: Authentication Panel */}
        <motion.div 
          className="md:col-span-5 w-full"
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.15 }}
        >
          <div className="glass-panel rounded-2xl p-8 relative shadow-glass overflow-hidden">
            {/* Top decorative glass reflect */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-white/20 to-transparent" />

            <div className="mb-8 text-center md:text-left">
              <div className="h-12 w-12 rounded-xl bg-gradient-to-tr from-primary to-secondary flex items-center justify-center mx-auto md:mx-0 shadow-lg shadow-primary/20 mb-4">
                <Shield className="w-6 h-6 text-white" />
              </div>
              <h2 className="text-2xl font-bold text-white">Control Panel Access</h2>
              <p className="text-sm text-gray-400 mt-1">Authenticate to monitor and control simulation matrices.</p>
            </div>

            {/* Session success state */}
            {isAuthenticated ? (
              <motion.div 
                className="space-y-6 text-center py-4"
                initial={{ scale: 0.95, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
              >
                <div className="flex justify-center">
                  <CheckCircle className="w-16 h-16 text-accent-green" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-lg font-semibold text-white">Welcome back, {user?.username}!</h3>
                  <p className="text-xs text-gray-400">Authenticated as <span className="text-primary font-medium">{user?.role}</span></p>
                </div>
                <div className="p-4 rounded-lg bg-white/[0.02] border border-white/5 text-left text-xs text-gray-400 space-y-2">
                  <p className="font-semibold text-white">Module 1 Authentication Complete!</p>
                  <p>Next modules will implement physical servers, workload task engines, scheduler routines, and telemetry diagnostics.</p>
                </div>
                <button
                  onClick={logout}
                  className="w-full py-2.5 px-4 rounded-xl border border-white/10 text-white font-medium hover:bg-white/5 transition-all text-sm"
                >
                  Log Out Session
                </button>
              </motion.div>
            ) : (
              // Login Form
              <form onSubmit={handleSubmit} className="space-y-5">
                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">Username or Email</label>
                  <div className="relative">
                    <User className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                    <input
                      type="text"
                      value={username}
                      onChange={(e) => setUsername(e.target.value)}
                      placeholder="Enter username"
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-primary/50 transition-colors"
                      disabled={isLoading}
                    />
                  </div>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-semibold text-gray-300 uppercase tracking-wider block">Security Password</label>
                  <div className="relative">
                    <Lock className="absolute left-3.5 top-3 h-4 w-4 text-gray-400" />
                    <input
                      type="password"
                      value={password}
                      onChange={(e) => setPassword(e.target.value)}
                      placeholder="••••••••"
                      className="w-full bg-[#0a0f1d] border border-white/10 rounded-xl py-2.5 pl-10 pr-4 text-white text-sm placeholder-gray-500 focus:outline-none focus:border-primary/50 transition-colors"
                      disabled={isLoading}
                    />
                  </div>
                </div>

                {/* Form feedback warnings */}
                <AnimatePresence mode="wait">
                  {(error || formError) && (
                    <motion.div 
                      className="flex items-start space-x-2.5 p-3 rounded-lg bg-accent-red/10 border border-accent-red/20 text-accent-red text-xs"
                      initial={{ opacity: 0, y: -10 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -10 }}
                    >
                      <AlertCircle className="w-4 h-4 shrink-0 mt-0.5" />
                      <span>{formError || error}</span>
                    </motion.div>
                  )}
                </AnimatePresence>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full bg-gradient-to-r from-primary to-primary-dark hover:from-primary-light hover:to-primary text-background font-bold py-3 rounded-xl transition-all shadow-lg shadow-primary/20 text-sm hover:scale-[1.01] active:scale-[0.99] flex items-center justify-center space-x-2"
                >
                  {isLoading ? (
                    <div className="w-5 h-5 border-2 border-background border-t-transparent rounded-full animate-spin" />
                  ) : (
                    <>
                      <span>Secure Login</span>
                    </>
                  )}
                </button>

                {/* Default Credentials Callout */}
                <div className="mt-6 p-4 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                  <div className="flex items-center space-x-1.5 text-xs text-primary font-semibold">
                    <Server className="w-3.5 h-3.5" />
                    <span>Seeded Account Credentials</span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-2xs text-gray-400">
                    <div>
                      <span className="block text-gray-500 font-medium">Username:</span>
                      <code className="text-white bg-white/5 px-1 py-0.5 rounded">admin</code>
                    </div>
                    <div>
                      <span className="block text-gray-500 font-medium">Password:</span>
                      <code className="text-white bg-white/5 px-1 py-0.5 rounded">AdminPass123!</code>
                    </div>
                  </div>
                </div>
              </form>
            )}
          </div>
        </motion.div>
      </div>
    </div>
  );
};
export default Login;
