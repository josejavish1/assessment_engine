'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { createClient } from '@/lib/supabase/client';
import { 
  ShieldCheck, 
  Lock, 
  Mail, 
  User, 
  ArrowRight, 
  Loader2, 
  CheckCircle2, 
  AlertCircle,
  Building2,
  Crown,
  KeyRound
} from 'lucide-react';

export default function LoginPage() {
  const [mode, setMode] = useState<'login' | 'register'>('login');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [fullName, setFullName] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const router = useRouter();
  const supabase = createClient();

  const handleQuickLogin = (demoEmail: string, demoPass: string) => {
    setEmail(demoEmail);
    setPassword(demoPass);
    setErrorMsg(null);
    setSuccessMsg(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsSubmitting(true);
    setErrorMsg(null);
    setSuccessMsg(null);

    try {
      if (mode === 'login') {
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email.trim(),
          password,
        });

        if (error) {
          throw new Error(error.message === 'Invalid login credentials' ? 'Invalid credentials. Please verify your email and password.' : error.message);
        }

        if (data.session) {
          const { data: profile } = await supabase
            .from('profiles')
            .select('role')
            .eq('id', data.user.id)
            .single();

          const role = profile?.role;
          if (role === 'superadmin') {
            router.push('/admin');
          } else if (role === 'company_admin') {
            router.push('/company');
          } else {
            router.push('/portal');
          }
        }
      } else {
        // Mode: Register
        const { data, error } = await supabase.auth.signUp({
          email: email.trim(),
          password,
          options: {
            data: {
              full_name: fullName.trim(),
            },
          },
        });

        if (error) {
          throw new Error(error.message);
        }

        if (data.session) {
          setSuccessMsg('Account created and activated successfully! Redirecting...');
          setTimeout(() => {
            router.push('/portal');
          }, 1000);
        } else {
          setSuccessMsg('User registered successfully. You may now sign in.');
          setMode('login');
        }
      }
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error al conectar con el servidor.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen w-full bg-[#05070c] text-white flex flex-col justify-between items-center relative overflow-hidden px-4 py-10 select-none">
      {/* Background Glow */}
      <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[800px] h-[360px] bg-gradient-to-b from-blue-600/15 via-blue-900/5 to-transparent rounded-full blur-[140px] pointer-events-none" />

      {/* Header */}
      <header className="relative z-10 flex flex-col items-center gap-2 pt-4">
        <div className="inline-flex p-3 rounded-2xl bg-blue-500/10 border border-blue-500/20 text-blue-400 shadow-lg shadow-blue-500/10">
          <ShieldCheck className="w-8 h-8" />
        </div>
        <div className="text-center">
          <div className="text-xs font-semibold tracking-[0.25em] text-blue-400 uppercase font-mono">
            Assessment Engine Enterprise
          </div>
          <div className="text-[11px] text-slate-500 tracking-wider uppercase mt-0.5">
            Tier-1 Commercial Portal · Sovereignty & Governance
          </div>
        </div>
      </header>

      {/* Main Card */}
      <main className="w-full max-w-[420px] relative z-10 my-auto py-6">
        <div className="rounded-2xl bg-[#0f141f]/90 border border-white/[0.08] p-7 sm:p-8 shadow-[0_25px_60px_-15px_rgba(0,0,0,0.9)] backdrop-blur-2xl space-y-6">
          
          {/* Mode Switcher */}
          <div className="flex p-1 rounded-xl bg-[#080b12] border border-white/[0.06] text-xs font-medium">
            <button
              type="button"
              onClick={() => { setMode('login'); setErrorMsg(null); setSuccessMsg(null); }}
              className={`flex-1 py-2 rounded-lg transition-all ${
                mode === 'login'
                  ? 'bg-blue-600 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Sign In
            </button>
            <button
              type="button"
              onClick={() => { setMode('register'); setErrorMsg(null); setSuccessMsg(null); }}
              className={`flex-1 py-2 rounded-lg transition-all ${
                mode === 'register'
                  ? 'bg-blue-600 text-white shadow-sm font-semibold'
                  : 'text-slate-400 hover:text-white'
              }`}
            >
              Crear Cuenta
            </button>
          </div>

          {/* Success Message */}
          {successMsg && (
            <div className="p-3.5 rounded-xl bg-emerald-950/40 border border-emerald-800/60 text-emerald-300 text-xs flex items-start gap-2.5">
              <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0 mt-0.5" />
              <span>{successMsg}</span>
            </div>
          )}

          {/* Error Message */}
          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-2.5">
              <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
              <span>{errorMsg}</span>
            </div>
          )}

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {mode === 'register' && (
              <div className="space-y-1.5">
                <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                  Nombre Completo
                </label>
                <div className="relative">
                  <User className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                  <input
                    type="text"
                    aria-label="Full Name"
                    required
                    value={fullName}
                    onChange={(e) => setFullName(e.target.value)}
                    placeholder="Jane Doe"
                    className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                  />
                </div>
              </div>
            )}

            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                Correo Corporativo
              </label>
              <div className="relative">
                <Mail className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="email"
                  aria-label="Corporate Email"
                  required
                  autoFocus
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="usuario@empresa.com"
                  className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-mono"
                />
              </div>
            </div>

            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                Password
              </label>
              <div className="relative">
                <Lock className="w-4 h-4 text-slate-500 absolute left-3.5 top-3" />
                <input
                  type="password"
                  aria-label="Password"
                  required
                  minLength={8}
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl pl-10 pr-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={isSubmitting}
              className="w-full py-3 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white transition-all flex items-center justify-center gap-2 shadow-lg shadow-blue-600/30 disabled:opacity-50 mt-2"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  Conectando con Supabase...
                </>
              ) : (
                <>
                  {mode === 'login' ? 'Entrar al Portal' : 'Crear Cuenta Inmediata'}
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </form>

          {/* Quick Access / Demo Accounts */}
          <div className="pt-4 border-t border-white/[0.08] space-y-2.5">
            <span className="text-[10px] font-mono uppercase text-slate-400 block text-center tracking-wider">
              Quick Access / Demo Accounts
            </span>
            <div className="grid grid-cols-3 gap-2">
              <button
                type="button"
                onClick={() => handleQuickLogin('admin@assessment.engine', 'Admin123456!')}
                className="p-2 rounded-lg bg-[#080b12] border border-white/[0.06] hover:border-amber-500/40 text-left transition-all group"
              >
                <div className="flex items-center gap-1 text-[10px] text-amber-400 font-semibold mb-0.5">
                  <Crown className="w-3 h-3" /> Admin
                </div>
                <div className="text-[9px] text-slate-500 font-mono truncate">Superadmin</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('empresa@nttdata.com', 'Empresa123456!')}
                className="p-2 rounded-lg bg-[#080b12] border border-white/[0.06] hover:border-emerald-500/40 text-left transition-all group"
              >
                <div className="flex items-center gap-1 text-[10px] text-emerald-400 font-semibold mb-0.5">
                  <Building2 className="w-3 h-3" /> Empresa
                </div>
                <div className="text-[9px] text-slate-500 font-mono truncate">NTT DATA</div>
              </button>

              <button
                type="button"
                onClick={() => handleQuickLogin('evaluador@cliente.es', 'User123456!')}
                className="p-2 rounded-lg bg-[#080b12] border border-white/[0.06] hover:border-indigo-500/40 text-left transition-all group"
              >
                <div className="flex items-center gap-1 text-[10px] text-indigo-400 font-semibold mb-0.5">
                  <User className="w-3 h-3" /> Usuario
                </div>
                <div className="text-[9px] text-slate-500 font-mono truncate">Evaluador</div>
              </button>
            </div>
          </div>
        </div>
      </main>

      {/* Footer */}
      <footer className="relative z-10 text-center py-2">
        <p className="text-[10px] text-slate-600 font-mono">
          Sovereign Authentication PostgreSQL 17.6 · Row Level Security (RLS) Active
        </p>
      </footer>
    </div>
  );
}
