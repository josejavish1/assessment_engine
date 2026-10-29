'use client';

import React, { useEffect, useState } from 'react';
import { 
  Building2, 
  Users, 
  ShieldCheck, 
  FileText, 
  Plus, 
  TrendingUp,
  Cpu,
  CheckCircle2
} from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

type Organization = {
  id: string;
  name: string;
  slug: string;
  created_at: string;
};

export default function AdminDashboardPage() {
  const [organizations, setOrganizations] = useState<Organization[]>([]);
  const [newOrgName, setNewOrgName] = useState('');
  const [newOrgSlug, setNewOrgSlug] = useState('');
  const [isCreating, setIsCreating] = useState(false);
  const [statusMsg, setStatusMsg] = useState<string | null>(null);
  const supabase = createClient();

  const fetchOrganizations = async () => {
    const { data } = await supabase
      .from('organizations')
      .select('*')
      .order('created_at', { ascending: false });

    if (data) {
      setOrganizations(data);
    }
  };

  useEffect(() => {
    fetchOrganizations();
  }, []);

  const handleCreateOrg = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newOrgName || !newOrgSlug) return;
    setIsCreating(true);
    setStatusMsg(null);

    const { error } = await supabase
      .from('organizations')
      .insert([{ name: newOrgName, slug: newOrgSlug.toLowerCase().trim() }]);

    if (error) {
      setStatusMsg(`Error: ${error.message}`);
    } else {
      setStatusMsg('Enterprise registered successfully in Supabase.');
      setNewOrgName('');
      setNewOrgSlug('');
      fetchOrganizations();
    }
    setIsCreating(false);
  };

  const metrics = [
    { label: 'Empresas Registradas', value: organizations.length.toString(), icon: Building2, change: '+100% este mes' },
    { label: 'Motor Bayesiano FAIR', value: '10.000 iter.', icon: Cpu, change: 'Semilla SHA-256 fija' },
    { label: 'Expedientes Actives', value: '14 Entregables', icon: FileText, change: 'Torres T1-T10 activas' },
    { label: 'Barreras de Gobernanza', value: '100% Green', icon: ShieldCheck, change: 'Zero-Lockin verificado' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Panel de Control Global (Superadmin)</h1>
        <p className="text-sm text-slate-400 mt-1">
          Comprehensive supervision of commercial tenants, actuarial policies, and neurosymbolic audits.
        </p>
      </div>

      {/* Metrics Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {metrics.map((m) => {
          const Icon = m.icon;
          return (
            <div key={m.label} className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-3">
              <div className="flex items-center justify-between text-slate-400">
                <span className="text-xs font-medium uppercase tracking-wider">{m.label}</span>
                <div className="p-2 rounded-lg bg-slate-800/80 text-blue-400">
                  <Icon className="h-4 w-4" />
                </div>
              </div>
              <div className="text-2xl font-bold text-white tracking-tight">{m.value}</div>
              <div className="text-[11px] text-emerald-400 flex items-center gap-1">
                <TrendingUp className="h-3 w-3" />
                {m.change}
              </div>
            </div>
          );
        })}
      </div>

      {/* Section: Organizations Management */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Left: Organization List */}
        <div className="lg:col-span-2 bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
            <h2 className="text-base font-semibold text-white">Tenants Comerciales Registrados</h2>
            <span className="text-xs text-slate-400 font-mono">{organizations.length} activos</span>
          </div>

          <div className="divide-y divide-slate-800">
            {organizations.length === 0 ? (
              <div className="p-8 text-center text-slate-500 text-sm">
                No enterprises registered yet. Register the first enterprise using the side form.
              </div>
            ) : (
              organizations.map((org) => (
                <div key={org.id} className="p-4 px-6 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
                  <div className="flex items-center gap-3">
                    <div className="h-9 w-9 rounded-lg bg-blue-500/10 border border-blue-500/20 flex items-center justify-center text-blue-400">
                      <Building2 className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-medium text-sm text-white block">{org.name}</span>
                      <span className="text-xs text-slate-500 font-mono block">slug: {org.slug}</span>
                    </div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-[11px] font-mono text-slate-400">
                      {new Date(org.created_at).toLocaleDateString()}
                    </span>
                    <span className="px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                      Soberano
                    </span>
                  </div>
                </div>
              ))
            )}
          </div>
        </div>

        {/* Right: Quick Register Form */}
        <div className="bg-slate-900 border border-slate-800 p-6 rounded-xl space-y-5">
          <div>
            <h3 className="text-base font-semibold text-white">High de Nueva Empresa</h3>
            <p className="text-xs text-slate-400 mt-1">
              Create a new isolated tenant in Supabase with dedicated Row Level Security.
            </p>
          </div>

          {statusMsg && (
            <div className={`p-3 rounded-lg text-xs ${statusMsg.startsWith('Error') ? 'bg-rose-500/10 text-rose-400 border border-rose-500/20' : 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-2'}`}>
              {!statusMsg.startsWith('Error') && <CheckCircle2 className="h-4 w-4" />}
              {statusMsg}
            </div>
          )}

          <form onSubmit={handleCreateOrg} className="space-y-4">
            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Legal Entity Name / Organization
              </label>
              <input
                type="text"
                required
                value={newOrgName}
                onChange={(e) => {
                  setNewOrgName(e.target.value);
                  setNewOrgSlug(e.target.value.toLowerCase().replace(/[^a-z0-9]/g, '-').replace(/-+/g, '-'));
                }}
                placeholder="e.g. Global Power Corporation"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                Slug Identificador
              </label>
              <input
                type="text"
                required
                value={newOrgSlug}
                onChange={(e) => setNewOrgSlug(e.target.value)}
                placeholder="ej. red-electrica"
                className="w-full bg-slate-950 border border-slate-800 rounded-lg px-3.5 py-2 text-sm text-slate-100 font-mono placeholder:text-slate-600 focus:outline-none focus:ring-2 focus:ring-blue-500/40"
              />
            </div>

            <button
              type="submit"
              disabled={isCreating}
              className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white font-medium text-xs transition-colors shadow-lg shadow-blue-600/20 disabled:opacity-50"
            >
              <Plus className="h-4 w-4" />
              {isCreating ? 'Guardando en Supabase...' : 'Register Enterprise'}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}
