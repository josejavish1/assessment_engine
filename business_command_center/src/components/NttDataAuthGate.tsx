'use client';

import React, { useState } from 'react';
import {
  Lock,
  Mail,
  User,
  AlertCircle,
  Loader2,
  ArrowRight,
  ShieldCheck,
  Building2,
  CheckCircle2,
  Crown,
  Briefcase
} from 'lucide-react';
import { authenticateUserProfile } from '@/app/actions/governance';

export interface AuthUser {
  id: string;
  email: string;
  fullName: string;
  role: 'ADMIN' | 'CONSULTANT' | 'CLIENT';
  clientSlug?: string;
}

interface NttDataAuthGateProps {
  onSuccess: (user: AuthUser) => void;
}

export function NttDataAuthGate({ onSuccess }: NttDataAuthGateProps) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const handleManualLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email.trim() || !password.trim()) {
      setErrorMsg('Introduce tus credenciales corporativas');
      return;
    }

    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await authenticateUserProfile(email.trim());
      if (res.success && res.profile) {
        const user: AuthUser = {
          id: res.profile.id,
          email: res.profile.email,
          fullName: res.profile.full_name,
          role: res.profile.role,
          clientSlug: res.profile.client_slug || undefined,
        };
        localStorage.setItem('assessment_auth_user', JSON.stringify(user));
        onSuccess(user);
      } else {
        setErrorMsg(res.error || 'Credenciales no autorizadas');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Connection error');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickDemoLogin = async (profileEmail: string) => {
    setLoading(true);
    setErrorMsg(null);

    try {
      const res = await authenticateUserProfile(profileEmail);
      if (res.success && res.profile) {
        const user: AuthUser = {
          id: res.profile.id,
          email: res.profile.email,
          fullName: res.profile.full_name,
          role: res.profile.role,
          clientSlug: res.profile.client_slug || undefined,
        };
        localStorage.setItem('assessment_auth_user', JSON.stringify(user));
        onSuccess(user);
      } else {
        setErrorMsg(res.error || 'Error accessing demo profile');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Authentication error');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5f5f7] text-[#1d1d1f] flex items-center justify-center p-4 font-sans select-none">
      <div className="w-full max-w-md space-y-6">
        {/* Brand & Identity Header */}
        <div className="text-center space-y-3">
          <div className="inline-flex p-3 rounded-2xl bg-[#0a1120] border border-[#14233e] shadow-md">
            <img src="/ntt_data_brand.svg" alt="NTT DATA" className="h-8 w-auto object-contain" />
          </div>
          <div>
            <h1 className="text-base font-bold text-[#1d1d1f] tracking-wide">
              ASSESSMENT ENGINE · EMEAL
            </h1>
            <p className="text-xs text-stone-500 font-mono mt-0.5">
              Hierarchical HRBAC Access Control (ANSI/INCITS 359-2004)
            </p>
          </div>
        </div>

        {/* Login Card */}
        <div className="p-8 rounded-2xl bg-white border border-stone-200/80 shadow-[0_4px_24px_rgba(0,0,0,0.04)] space-y-5">
          <div className="space-y-1 border-b border-stone-100 pb-3">
            <h2 className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">
              Corporate Authentication
            </h2>
            <p className="text-[11px] text-stone-500">
              Sign in with corporate account or select one of 3 cumulative hierarchical roles.
            </p>
          </div>

          {errorMsg && (
            <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs flex items-start gap-2.5">
              <AlertCircle className="h-4 w-4 text-rose-500 shrink-0 mt-0.5" />
              <span className="leading-snug">{errorMsg}</span>
            </div>
          )}

          <form onSubmit={handleManualLogin} className="space-y-4">
            <div className="space-y-1">
              <label className="text-[10px] font-mono uppercase text-stone-500 font-semibold block">
                Corporate Email
              </label>
              <div className="relative">
                <Mail className="h-4 w-4 absolute left-3 top-2.5 text-stone-400" />
                <input
                  type="email"
                  aria-label="Corporate Email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="usuario@nttdata.com"
                  className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-9 pr-3 py-2 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:bg-white focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/10 transition-all font-mono"
                />
              </div>
            </div>

            <div className="space-y-1">
              <label className="text-[10px] font-mono uppercase text-stone-500 font-semibold block">
                Password
              </label>
              <div className="relative">
                <Lock className="h-4 w-4 absolute left-3 top-2.5 text-stone-400" />
                <input
                  type="password"
                  aria-label="Password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••••••"
                  className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-9 pr-3 py-2 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:bg-white focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/10 transition-all"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-sm shadow-[#0072BC]/20 disabled:opacity-50"
            >
              {loading ? (
                <Loader2 className="h-4 w-4 animate-spin" />
              ) : (
                <>
                  <span>Sign In</span>
                  <ArrowRight className="h-3.5 w-3.5" />
                </>
              )}
            </button>
          </form>

          {/* Quick Demo Access Buttons (3-Tier Hierarchical Roles) */}
          <div className="pt-4 border-t border-stone-100 space-y-2.5">
            <span className="text-[10px] font-mono uppercase text-stone-500 font-bold block text-center">
              One-Click Hierarchical Demo Profiles
            </span>

            <div className="grid grid-cols-1 gap-2">
              {/* Level 3: Admin */}
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('director@nttdata.com')}
                className="w-full p-3 rounded-xl bg-stone-50 hover:bg-purple-50/60 border border-stone-200 hover:border-purple-300 text-left transition-all group flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-stone-800 group-hover:text-purple-700 flex items-center gap-1.5">
                    <Crown className="h-3.5 w-3.5 text-purple-600" />
                    <span>Nivel 3: Socio Administrador NTT DATA</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-purple-100 text-purple-700 font-semibold">
                      ADMIN
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-stone-500">
                    Full Access + User Management, Suspension & Governance
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-stone-400 group-hover:text-purple-600 transition-colors" />
              </button>

              {/* Level 2: Consultant */}
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('consultor@nttdata.com')}
                className="w-full p-3 rounded-xl bg-stone-50 hover:bg-blue-50/60 border border-stone-200 hover:border-blue-300 text-left transition-all group flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-stone-800 group-hover:text-[#0072BC] flex items-center gap-1.5">
                    <Briefcase className="h-3.5 w-3.5 text-[#0072BC]" />
                    <span>Nivel 2: Consultor Senior NTT DATA</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-blue-100 text-[#0072BC] font-semibold">
                      CONSULTOR
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-stone-500">
                    All Tenants, War Room, Synthesis & Actuarial Simulation
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-stone-400 group-hover:text-[#0072BC] transition-colors" />
              </button>

              {/* Level 1: Client */}
              <button
                type="button"
                onClick={() => handleQuickDemoLogin('ciso@nordicgrid.de')}
                className="w-full p-3 rounded-xl bg-stone-50 hover:bg-emerald-50/60 border border-stone-200 hover:border-emerald-300 text-left transition-all group flex items-center justify-between"
              >
                <div className="space-y-0.5">
                  <div className="text-xs font-bold text-stone-800 group-hover:text-emerald-700 flex items-center gap-1.5">
                    <Building2 className="h-3.5 w-3.5 text-emerald-600" />
                    <span>Nivel 1: Cliente Final · Nordic Grid Power</span>
                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-emerald-100 text-emerald-800 font-semibold">
                      CLIENTE
                    </span>
                  </div>
                  <div className="text-[10px] font-mono text-stone-500">
                    Autoservicio acotado: Solo su radar, entregables y evidencias
                  </div>
                </div>
                <ArrowRight className="h-4 w-4 text-stone-400 group-hover:text-emerald-600 transition-colors" />
              </button>
            </div>
          </div>
        </div>

        {/* Security Footer */}
        <div className="text-center font-mono text-[10px] text-stone-400">
          Aislamiento RLS en PostgreSQL 17.6 · Cero Fuga de Information Multinquilino
        </div>
      </div>
    </div>
  );
}
