'use client';

import React, { useState, useEffect } from 'react';
import {
  Activity,
  Layers,
  Cpu,
  Award,
  Terminal,
  FileText,
  Play,
  Loader2,
  Building2,
  AlertCircle,
  ChevronRight,
  ShieldAlert,
  Database,
  RefreshCw,
  ExternalLink,
  Sliders,
  ArrowRight,
  UploadCloud,
  MessageSquare,
  Send,
  Zap,
  User,
  Plus,
  BookOpen,
  CheckCircle2,
  Download,
  Filter,
  Search,
  Lock,
  Menu,
  X,
  LogOut,
  ShieldCheck,
  Crown,
  UserX,
  UserCheck
} from 'lucide-react';
import { getSimulationSummary, type SimulationArchetype, type PillarData } from '@/app/actions/assessment';
import { sendWarRoomTacticalMessage, getWarRoomHistory, type WarRoomMessage } from '@/app/actions/war_room';
import { getUserProfiles, toggleUserBlock, updateUserRole, type UserProfile } from '@/app/actions/governance';
import { KnowledgeHubModal } from '@/components/KnowledgeHubModal';
import { ClientHubView } from '@/components/ClientHubView';
import { ClientPortalView } from '@/components/ClientPortalView';
import { NewClientModal } from '@/features/clients/NewClientModal';
import { ReportViewer } from '@/features/reports/ReportViewer';
import { NttDataAuthGate, type AuthUser } from '@/components/NttDataAuthGate';

export default function UnifiedCommandCenterPage() {
  const [currentUser, setCurrentUser] = useState<AuthUser | null>(null);
  const [isAuthChecking, setIsAuthChecking] = useState(true);
  const [archetypes, setArchetypes] = useState<SimulationArchetype[]>([]);
  const [selectedId, setSelectedId] = useState<string>('nordic_grid_power_gmbh');
  const [mainView, setMainView] = useState<'workspace' | 'hub'>('workspace');
  const [activeTab, setActiveTab] = useState<'radar' | 'report' | 'evidence' | 'war_room' | 'governance'>('radar');
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [showNewClientModal, setShowNewClientModal] = useState(false);
  const [selectedPillar, setSelectedPillar] = useState<PillarData | null>(null);
  const [telemetryLogs, setTelemetryLogs] = useState<string>('Sistema inicializado. Listo para despachar pipelines actuariales.\n');
  const [warRoomHistory, setWarRoomHistory] = useState<WarRoomMessage[]>([]);
  const [chatInput, setChatInput] = useState('');
  const [chatLoading, setChatLoading] = useState(false);
  const [notification, setNotification] = useState<{ type: 'success' | 'error'; message: string } | null>(null);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [searchFilter, setSearchFilter] = useState('');
  const [userProfiles, setUserProfiles] = useState<UserProfile[]>([]);
  const [governanceLoading, setGovernanceLoading] = useState(false);
  const [tefSlider, setTefSlider] = useState<number>(0.04);
  const [vulnSlider, setVulnSlider] = useState<number>(14.2);

  const loadData = async (selectSlug?: string) => {
    setIsLoading(true);
    const res = await getSimulationSummary();
    if (res.success && res.data && res.data.length > 0) {
      setArchetypes(res.data);
      const targetSlug = selectSlug || selectedId;
      const found = res.data.find(a => a.archetype_id === targetSlug || a.client_slug === targetSlug);
      if (found) {
        setSelectedId(found.client_slug || found.archetype_id);
      } else {
        setSelectedId(res.data[0].client_slug || res.data[0].archetype_id);
      }
    }
    setIsLoading(false);
  };

  useEffect(() => {
    try {
      const saved = localStorage.getItem('assessment_auth_user');
      if (saved) {
        const parsed: AuthUser = JSON.parse(saved);
        setCurrentUser(parsed);
        if (parsed.role === 'CLIENT' && parsed.clientSlug) {
          setSelectedId(parsed.clientSlug);
        }
      }
    } catch {}
    setIsAuthChecking(false);
  }, []);

  useEffect(() => {
    loadData();
  }, []);

  const activeOpp = archetypes.find(a => a.archetype_id === selectedId || a.client_slug === selectedId) || archetypes[0];

  useEffect(() => {
    const fetchChat = async () => {
      const slug = activeOpp?.client_slug || selectedId;
      const alt = activeOpp?.archetype_id;
      if (slug) {
        const history = await getWarRoomHistory(slug, alt);
        setWarRoomHistory(history);
      }
    };
    fetchChat();
  }, [selectedId, activeOpp?.client_slug, activeOpp?.archetype_id]);

  const handleRunPipeline = async () => {
    setIsRunning(true);
    setNotification(null);
    setTelemetryLogs(prev => prev + `\n[${new Date().toLocaleTimeString()}] [STREAM] Connecting to real-time actuarial engine...\n`);
    setActiveTab('war_room');

    try {
      const response = await fetch('/api/pipeline/stream');
      if (!response.body) throw new Error('Failed to establish telemetry stream with actuarial engine.');

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        const text = decoder.decode(value, { stream: true });
        setTelemetryLogs(prev => prev + text);
      }

      setNotification({ type: 'success', message: 'Actuarial simulation executed successfully. Deliverables regenerated.' });
      await loadData();
    } catch (err: any) {
      const msg = err.message || 'Error desconocido';
      setNotification({ type: 'error', message: msg });
      setTelemetryLogs(prev => prev + `[${new Date().toLocaleTimeString()}] [ERROR] Fallo en stream: ${msg}\n`);
    } finally {
      setIsRunning(false);
    }
  };

  const handleSendWarRoomChat = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!chatInput.trim() || chatLoading) return;
    const msg = chatInput.trim();
    setChatInput('');
    const userMsg: WarRoomMessage = {
      role: 'user',
      text: msg,
      timestamp: new Date().toLocaleTimeString(),
    };
    setWarRoomHistory(prev => [...prev, userMsg]);
    setChatLoading(true);

    try {
      const targetSlug = activeOpp?.client_slug || activeOpp?.archetype_id || selectedId;
      const res = await sendWarRoomTacticalMessage(targetSlug, msg);
      if (res.success && res.reply) {
        setWarRoomHistory(prev => [...prev, res.reply!]);
        setNotification({
          type: 'success',
          message: `Tactical adjustment incorporated into dossier (${res.reply.impacted_vectors?.join(', ') || 'Impact Actuarial'}).`,
        });
      } else {
        setNotification({ type: 'error', message: res.error || 'Error en War Room' });
      }
    } catch (err: any) {
      setNotification({ type: 'error', message: err.message || 'Network communication error' });
    } finally {
      setChatLoading(false);
    }
  };

  const loadGovernance = async () => {
    setGovernanceLoading(true);
    const res = await getUserProfiles();
    if (res.success && res.data) {
      setUserProfiles(res.data);
    }
    setGovernanceLoading(false);
  };

  useEffect(() => {
    if (activeTab === 'governance') {
      loadGovernance();
    }
  }, [activeTab]);

  const handleToggleBlock = async (userId: string, isBlocked: boolean) => {
    const res = await toggleUserBlock(userId, isBlocked);
    if (res.success) {
      setNotification({ type: 'success', message: res.message });
      await loadGovernance();
    } else {
      setNotification({ type: 'error', message: res.message });
    }
  };

  const handleUpdateRole = async (userId: string, newRole: 'ADMIN' | 'CONSULTANT' | 'CLIENT') => {
    const res = await updateUserRole(userId, newRole);
    if (res.success) {
      setNotification({ type: 'success', message: res.message });
      await loadGovernance();
    } else {
      setNotification({ type: 'error', message: res.message });
    }
  };

  const filteredArchetypes = archetypes
    .filter((a) => {
      if (currentUser?.role === 'CLIENT' && currentUser.clientSlug) {
        return a.client_slug === currentUser.clientSlug || a.archetype_id === currentUser.clientSlug;
      }
      return true;
    })
    .filter((a) =>
      a.company_name.toLowerCase().includes(searchFilter.toLowerCase()) ||
      (a.client_slug && a.client_slug.toLowerCase().includes(searchFilter.toLowerCase())) ||
      (a.sector && a.sector.toLowerCase().includes(searchFilter.toLowerCase()))
    );

  if (isAuthChecking) {
    return (
      <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-[#0072BC]" />
      </div>
    );
  }

  if (!currentUser) {
    return (
      <NttDataAuthGate
        onSuccess={(user) => {
          setCurrentUser(user);
          if (user.role === 'CLIENT' && user.clientSlug) {
            setSelectedId(user.clientSlug);
          }
        }}
      />
    );
  }

  return (
    <div className="flex h-screen bg-[#f5f5f7] text-[#1d1d1f] font-sans antialiased overflow-hidden flex-col">
      {/* Top Global Corporate Bar (NTT DATA Midnight Navy & White Canvas Contrast) */}
      <header className="h-16 border-b border-[#14233e] bg-[#0a1120] px-6 lg:px-8 flex items-center justify-between shrink-0 select-none z-30 shadow-md print:hidden">
        <div className="flex items-center gap-5">
          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
            className="lg:hidden p-1.5 rounded-lg text-slate-400 hover:text-white hover:bg-[#14233e] transition-colors"
          >
            {mobileMenuOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
          </button>

          {/* NTT DATA Brand Logo & App Title */}
          <div className="flex items-center gap-3.5 pr-5 border-r border-[#1e3052]">
            <img src="/ntt_data_brand.svg" alt="NTT DATA" className="h-6 w-auto object-contain" />
            <div className="flex items-center gap-2 font-mono text-xs tracking-wider text-white font-bold">
              <span>ASSESSMENT ENGINE</span>
              <span className="text-[10px] text-blue-300 font-semibold px-2 py-0.5 rounded-full bg-[#0072BC]/20 border border-[#0072BC]/40">
                SOVEREIGN EMEAL
              </span>
            </div>
          </div>

          {/* Top High-Level View Switcher (Consultor NTT DATA y Administrador) */}
          {currentUser.role !== 'CLIENT' && (
            <div className="hidden sm:flex items-center p-1 bg-[#131d33] rounded-xl text-xs font-medium border border-[#1e2d4d]">
              <button
                onClick={() => setMainView('workspace')}
                className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                  mainView === 'workspace'
                    ? 'bg-[#0072BC] text-white shadow-sm font-semibold'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <Layers className="w-3.5 h-3.5" />
                <span>Assessment Dossier</span>
              </button>
              <button
                onClick={() => setMainView('hub')}
                className={`px-3.5 py-1.5 rounded-lg transition-all flex items-center gap-2 ${
                  mainView === 'hub'
                    ? 'bg-[#0072BC] text-white shadow-sm font-semibold'
                    : 'text-slate-300 hover:text-white'
                }`}
              >
                <Building2 className="w-3.5 h-3.5" />
                <span>Portafolio de Cuentas ({archetypes.length})</span>
              </button>
            </div>
          )}
        </div>

        {/* Global Action Buttons & User Profile */}
        <div className="flex items-center gap-3">
          {currentUser.role !== 'CLIENT' && (
            <>
              <button
                onClick={() => setShowUploadModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-medium bg-[#131d33] hover:bg-[#1a2745] text-slate-200 border border-[#1e2d4d] transition-colors shadow-sm"
              >
                <UploadCloud className="w-3.5 h-3.5 text-blue-400" />
                <span className="hidden md:inline">Ingestar Evidencias</span> (ZIP/PDF)
              </button>

              <button
                onClick={() => setShowNewClientModal(true)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-semibold bg-[#131d33] hover:bg-[#1a2745] text-blue-400 border border-[#1e2d4d] transition-colors shadow-sm"
              >
                <Plus className="w-3.5 h-3.5" />
                <span className="hidden md:inline">New</span> Expediente
              </button>

              <button
                onClick={handleRunPipeline}
                disabled={isRunning}
                className="flex items-center gap-2 px-4 py-1.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-md shadow-[#0072BC]/30 disabled:opacity-50"
              >
                {isRunning ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Simulando...</span>
                  </>
                ) : (
                  <>
                    <Play className="w-3 h-3 fill-white" />
                    <span>Run Simulation</span>
                  </>
                )}
              </button>
            </>
          )}

          {/* User Profile Info & Logout */}
          <div className="flex items-center gap-3 pl-3 border-l border-[#1e3052]">
            <div className="text-right hidden sm:block">
              <div className="text-xs font-semibold text-white truncate max-w-[150px]">
                {currentUser.fullName}
              </div>
              <div className="text-[10px] text-slate-400 font-mono flex items-center justify-end gap-1">
                {currentUser.role === 'ADMIN' ? (
                  <span className="text-blue-400 font-bold">NTT DATA · ADMIN</span>
                ) : (
                  <span className="text-emerald-400 font-bold">INQUILINO CLIENTE</span>
                )}
              </div>
            </div>

            <button
              onClick={() => {
                localStorage.removeItem('assessment_auth_user');
                setCurrentUser(null);
              }}
              className="p-1.5 rounded-lg hover:bg-[#14233e] text-slate-400 hover:text-rose-400 transition-colors"
              title="Sign Out Corporativa"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>
      </header>

      {/* Global Toast Notification */}
      {notification && (
        <div
          className={`px-8 py-2.5 text-xs flex items-center justify-between border-b transition-all ${
            notification.type === 'success'
              ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
              : 'bg-rose-50 border-rose-200 text-rose-800'
          }`}
        >
          <span className="flex items-center gap-2 font-mono">
            {notification.type === 'success' ? (
              <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            ) : (
              <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
            )}
            {notification.message}
          </span>
          <button
            onClick={() => setNotification(null)}
            className="text-stone-400 hover:text-stone-700 font-mono text-sm px-2"
          >
            &times;
          </button>
        </div>
      )}

      {/* Main Content Area */}
      <div className="flex-1 flex overflow-hidden">
        {currentUser.role === 'CLIENT' ? (
          <div className="flex-1 overflow-y-auto p-6 lg:p-10 bg-[#f5f5f7]">
            {isLoading || !activeOpp ? (
              <div className="max-w-6xl mx-auto p-16 text-center space-y-3">
                <Loader2 className="w-8 h-8 animate-spin text-[#0072BC] mx-auto" />
                <div className="text-xs font-mono text-stone-500">Cargando expediente ejecutivo...</div>
              </div>
            ) : (
              <ClientPortalView
                currentClient={activeOpp}
                onOpenUploadModal={() => setShowUploadModal(true)}
              />
            )}
          </div>
        ) : mainView === 'hub' ? (
          <div className="flex-1 overflow-y-auto p-8">
            <ClientHubView
              onSelectClient={(id) => {
                setSelectedId(id);
                setMainView('workspace');
                setActiveTab('radar');
              }}
              activeClientId={selectedId}
            />
          </div>
        ) : (
          <>
            {/* Sidebar: Client Dossiers List (Clean White Canvas Card Style) */}
            <aside
              className={`${
                mobileMenuOpen ? 'block absolute inset-y-16 left-0 z-20 w-80 shadow-2xl' : 'hidden'
              } lg:block w-80 border-r border-stone-200/80 bg-white flex flex-col shrink-0 select-none shadow-[2px_0_12px_rgba(0,0,0,0.02)] print:hidden`}
            >
              <div className="p-3.5 border-b border-stone-100 space-y-2.5">
                <div className="flex items-center justify-between px-1">
                  <span className="text-[10px] font-mono uppercase text-stone-500 font-bold tracking-wider">
                    Expedientes de Clientes
                  </span>
                  <span className="text-[10px] font-mono text-[#0072BC] font-semibold">
                    {filteredArchetypes.length} activo{filteredArchetypes.length === 1 ? '' : 's'}
                  </span>
                </div>

                <div className="relative">
                  <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-stone-400" />
                  <input
                    type="text"
                    aria-label="Search client, country, or sector"
                    value={searchFilter}
                    onChange={(e) => setSearchFilter(e.target.value)}
                    placeholder="Search client, country, or sector..."
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-8 pr-3 py-1.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:bg-white focus:border-[#0072BC] transition-all font-sans"
                  />
                </div>
              </div>

              <div className="flex-1 overflow-y-auto p-2.5 space-y-1.5">
                {filteredArchetypes.length === 0 ? (
                  <div className="p-8 text-center space-y-2">
                    <Search className="h-6 w-6 text-stone-300 mx-auto" />
                    <div className="text-xs font-semibold text-stone-700">Sin coincidencias</div>
                    <div className="text-[11px] text-stone-400 font-mono">
                      No se encontraron expedientes con &quot;{searchFilter}&quot;
                    </div>
                  </div>
                ) : (
                  filteredArchetypes.map((arch) => {
                  const isSelected =
                    arch.client_slug === activeOpp?.client_slug ||
                    arch.archetype_id === activeOpp?.archetype_id;
                  return (
                    <button
                      key={arch.client_slug || arch.archetype_id}
                      onClick={() => {
                        setSelectedId(arch.client_slug || arch.archetype_id);
                        setMobileMenuOpen(false);
                      }}
                      className={`w-full text-left p-3 rounded-xl border transition-all ${
                        isSelected
                          ? 'bg-blue-50/70 border-blue-200 text-[#1d1d1f] shadow-2xs'
                          : 'bg-white border-stone-200/60 hover:border-stone-300 hover:bg-stone-50/50 text-[#1d1d1f]'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="text-[10px] font-mono text-stone-500 font-medium">
                          {arch.country?.split(' ')[0] || 'ES'} • {arch.currency || 'EUR'}
                        </span>
                        <span className="h-2 w-2 rounded-full bg-emerald-500 ring-2 ring-emerald-500/20" />
                      </div>
                      <div className="font-semibold text-xs line-clamp-1 text-[#1d1d1f]">
                        {arch.company_name}
                      </div>
                      <div className="text-[10px] text-stone-500 font-mono mt-1 flex items-center justify-between">
                        <span className="truncate max-w-[140px]">{arch.standard || 'Official Standard'}</span>
                        <span className="text-emerald-700 font-semibold">{arch.global_score || '3.0'}</span>
                      </div>
                    </button>
                  );
                })
              )}
              </div>

              {/* Sidebar Footer Info */}
              <div className="p-3 border-t border-stone-100 bg-[#fbfbfa] text-[10px] font-mono text-stone-500 space-y-1">
                <div className="flex justify-between items-center">
                  <span>PostgreSQL 17.6 + RLS</span>
                  <span className="text-emerald-700 font-semibold">Puerto 8002</span>
                </div>
                <div className="flex justify-between items-center">
                  <span>Python Actuarial Core</span>
                  <span className="text-[#0072BC] font-semibold">Conectado</span>
                </div>
              </div>
            </aside>

            {/* Main Center Console (Light Executive Canvas) */}
            <main className="flex-1 flex flex-col overflow-hidden bg-[#f5f5f7] print:bg-white print:overflow-visible">
              {/* Active Client Executive Header */}
              <div className="border-b border-stone-200/80 bg-white px-8 py-4 flex flex-col sm:flex-row sm:items-center justify-between gap-4 shadow-[0_2px_8px_rgba(0,0,0,0.02)] print:hidden">
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0072BC] border border-blue-200 font-semibold">
                      {activeOpp?.country || 'Spain (ES)'} • {activeOpp?.currency || 'EUR (€)'}
                    </span>
                    <span className="text-[10px] font-mono px-2.5 py-0.5 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-semibold">
                      {activeOpp?.standard || 'ENS High'}
                    </span>
                  </div>
                  <h1 className="text-lg font-bold text-[#1d1d1f] tracking-wide">
                    {activeOpp?.company_name || 'Selecciona un expediente'}
                  </h1>
                </div>

                <div className="flex items-center gap-6">
                  <div className="text-right">
                    <div className="text-[10px] font-mono text-stone-500 uppercase tracking-wider">
                      Madurez Actuarial Consolidada
                    </div>
                    <div className="text-sm font-bold text-emerald-700 font-mono">
                      {activeOpp?.global_score || '3.0 / 5.0'} ({activeOpp?.global_band || 'Defined'})
                    </div>
                  </div>
                </div>
              </div>

              {/* Progressive HRBAC Navigation (ANSI/INCITS 359-2004) */}
              <div className="border-b border-stone-200/80 bg-white px-8 flex overflow-x-auto gap-2 scrollbar-none print:hidden">
                {[
                  { id: 'radar', label: '1. Multidimensional Diagnostic Radar', icon: Activity },
                  { id: 'report', label: '2. Online Technical Annex & Word Report', icon: BookOpen },
                  { id: 'evidence', label: '3. Ingesta de Evidencias (ZIP/PDF)', icon: FileText },
                  { id: 'war_room', label: '4. Tactical War Room & Open FAIR Model', icon: ShieldAlert },
                  ...(currentUser.role === 'ADMIN'
                    ? [{ id: 'governance', label: '5. User Management & Governance', icon: Crown }]
                    : []),
                ].map((tab) => {
                  const Icon = tab.icon;
                  const isActive = activeTab === tab.id;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id as any)}
                      className={`flex items-center gap-2 py-3.5 px-4 text-xs font-semibold border-b-2 transition-all whitespace-nowrap ${
                        isActive
                          ? 'border-[#0072BC] text-[#0072BC] font-semibold bg-blue-50/50'
                          : 'border-transparent text-stone-500 hover:text-stone-800 hover:border-stone-300'
                      }`}
                    >
                      <Icon className={`h-4 w-4 ${isActive ? 'text-[#0072BC]' : 'text-stone-400'}`} />
                      <span>{tab.label}</span>
                    </button>
                  );
                })}
              </div>

              {/* Workspace Body by Phase */}
              <div className="flex-1 overflow-y-auto p-6 lg:p-8">
                {/* PHASE 1: MULTIDIMENSIONAL DIAGNOSTIC & RADAR */}
                {activeTab === 'radar' && (
                  <div className="space-y-6 max-w-6xl">
                    {/* 4 Executive KPI Cards (White with Soft Shadows) */}
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                      <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-1">
                        <div className="text-[10px] font-mono text-stone-500 uppercase tracking-wider">
                          Madurez Actuarial
                        </div>
                        <div className="text-xl font-bold text-[#1d1d1f] font-mono">
                          {activeOpp?.global_score || '3.0 / 5.0'}
                        </div>
                        <div className="text-[11px] text-emerald-700 font-mono font-medium">
                          Nivel {activeOpp?.global_band || 'Defined'}
                        </div>
                      </div>

                      <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-1">
                        <div className="text-[10px] font-mono text-stone-500 uppercase tracking-wider">
                          Risk Residual FAIR
                        </div>
                        <div className="text-xl font-bold text-emerald-700 font-mono">
                          {activeOpp?.ale_formatted || 'Calculando...'}
                        </div>
                        <div className="text-[11px] text-stone-500 font-mono">
                          Annual Loss Expectancy ({activeOpp?.iterations || 5000} iterations)
                        </div>
                      </div>

                      <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-1">
                        <div className="text-[10px] font-mono text-stone-500 uppercase tracking-wider">
                          Entregables Listos
                        </div>
                        <div className="text-xl font-bold text-[#1d1d1f] font-mono">
                          {activeOpp?.generated_files?.length || 4} Binarios
                        </div>
                        <div className="text-[11px] text-[#0072BC] font-mono font-medium">
                          DOCX + PNG verificados
                        </div>
                      </div>

                      <div className="p-5 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-1">
                        <div className="text-[10px] font-mono text-stone-500 uppercase tracking-wider">
                          Governance & Sovereignty
                        </div>
                        <div className="text-xl font-bold text-[#1d1d1f] font-mono">
                          {activeOpp?.standard?.split('/')[0] || 'ENS High'}
                        </div>
                        <div className="text-[11px] text-purple-700 font-mono font-medium">
                          {activeOpp?.country || 'Soberano'}
                        </div>
                      </div>
                    </div>

                    {/* Radar Chart & Actuarial Findings Split */}
                    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                      {/* Radar Chart Container */}
                      <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4">
                        <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                          <h3 className="text-sm font-bold text-[#1d1d1f] flex items-center gap-2">
                            <Activity className="h-4 w-4 text-[#0072BC]" />
                            Radar de Madurez Multidimensional (Pillars)
                          </h3>
                          <span className="text-[10px] font-mono text-stone-500">Vector 10-Ejes</span>
                        </div>

                        <div className="flex items-center justify-center p-4 bg-[#fbfbfa] rounded-xl border border-stone-200/80 min-h-[360px]">
                          {activeOpp?.radar_path ? (
                            <img
                              src={`/api/download?path=${encodeURIComponent(activeOpp.radar_path)}`}
                              alt="Radar de Madurez Multidimensional"
                              className="max-h-[340px] w-auto object-contain"
                            />
                          ) : (
                            <div className="text-center text-stone-400 font-mono text-xs">
                              Generating actuarial radar visualization...
                            </div>
                          )}
                        </div>

                        <div className="flex justify-end pt-2">
                          <a
                            href={`/api/download?path=${encodeURIComponent(
                              activeOpp?.radar_path || ''
                            )}`}
                            download
                            className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 text-stone-700 border border-stone-200 transition-all shadow-2xs"
                          >
                            <Download className="h-3.5 w-3.5 text-[#0072BC]" /> Descargar PNG Vectorial
                          </a>
                        </div>
                      </div>

                      {/* Findings & Actuarial Summary */}
                      <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
                        <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                          <h3 className="text-sm font-bold text-[#1d1d1f] flex items-center gap-2">
                            <FileText className="h-4 w-4 text-emerald-600" />
                            Dictamen Actuarial y Hallazgos Principales
                          </h3>
                        </div>

                        <p className="text-xs text-stone-600 leading-relaxed font-sans">
                          Technical assessment for <strong className="text-[#1d1d1f]">{activeOpp?.company_name}</strong> verifies compliance alignment under <strong className="text-[#0072BC]">{activeOpp?.standard}</strong>. Monte Carlo actuarial models project an Annual Loss Expectancy of <strong className="text-emerald-700">{activeOpp?.ale_formatted}</strong>, with 95th percentile maximum loss bounded at <strong className="text-[#1d1d1f]">{activeOpp?.p95_formatted}</strong>.
                        </p>

                        <div className="space-y-2.5 font-mono text-xs">
                          <div className="flex justify-between p-2.5 rounded-lg bg-[#fbfbfa] border border-stone-200/80">
                            <span className="text-stone-500">Sector Industrial:</span>
                            <span className="text-[#1d1d1f] font-semibold">{activeOpp?.sector}</span>
                          </div>
                          <div className="flex justify-between p-2.5 rounded-lg bg-[#fbfbfa] border border-stone-200/80">
                            <span className="text-stone-500">Marco Regulatorio:</span>
                            <span className="text-[#0072BC] font-semibold">{activeOpp?.standard}</span>
                          </div>
                          <div className="flex justify-between p-2.5 rounded-lg bg-[#fbfbfa] border border-stone-200/80">
                            <span className="text-stone-500">Nivel de Madurez Global:</span>
                            <span className="text-emerald-700 font-semibold">{activeOpp?.global_score} ({activeOpp?.global_band})</span>
                          </div>
                        </div>

                        <div className="pt-4 border-t border-stone-100 flex justify-end gap-2">
                          <button
                            onClick={() => setActiveTab('report')}
                            className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white transition-all shadow-sm shadow-[#0072BC]/20"
                          >
                            View Technical Annex <ArrowRight className="h-3.5 w-3.5" />
                          </button>
                        </div>
                      </div>
                    </div>

                    {/* Interactive Pillars Matriz (T1-T10) */}
                    <div className="space-y-4 pt-4">
                      <div className="flex items-center justify-between">
                        <div>
                          <h3 className="text-sm font-bold text-[#1d1d1f] flex items-center gap-2">
                            <Layers className="h-4 w-4 text-[#0072BC]" />
                            Technology Pillars & Operational Gaps Breakdown
                          </h3>
                          <p className="text-[11px] text-stone-500 mt-0.5">
                            Selecciona cualquier pilar para inspeccionar su lectura actuarial detallada.
                          </p>
                        </div>
                        <span className="text-[10px] font-mono bg-stone-100 px-2.5 py-1 rounded-full text-stone-600 border border-stone-200">
                          {activeOpp?.pillars?.length || 5} Pilares Evaluados
                        </span>
                      </div>

                      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                        {/* Pillars List */}
                        <div className="lg:col-span-2 bg-white border border-stone-200/80 rounded-2xl overflow-hidden divide-y divide-stone-100 shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
                          {activeOpp?.pillars?.map((p, idx) => {
                            const isSelected = selectedPillar?.pillar_label === p.pillar_label;
                            const scoreNum = parseFloat(p.score_display) || 3.0;
                            const gap = (scoreNum - (p.target_maturity || 4)).toFixed(1);
                            return (
                              <div
                                key={idx}
                                onClick={() => setSelectedPillar(p)}
                                className={`p-4 px-6 flex items-center justify-between cursor-pointer transition-all ${
                                  isSelected
                                    ? 'bg-blue-50/60 border-l-4 border-l-[#0072BC]'
                                    : 'hover:bg-stone-50/60'
                                }`}
                              >
                                <div className="flex items-center gap-4">
                                  <div className="h-9 w-9 rounded-xl bg-stone-100 border border-stone-200 flex items-center justify-center font-mono text-xs font-bold text-[#0072BC] shrink-0">
                                    P{idx + 1}
                                  </div>
                                  <div>
                                    <div className="font-semibold text-xs text-[#1d1d1f]">{p.pillar_label}</div>
                                    <div className="text-[11px] text-stone-500 font-mono mt-0.5">Banda: {p.maturity_band}</div>
                                  </div>
                                </div>

                                <div className="flex items-center gap-6">
                                  <div className="text-right">
                                    <div className="text-[10px] text-stone-400 font-mono uppercase">Madurez / Objetivo</div>
                                    <div className="text-xs font-bold text-[#1d1d1f] font-mono">{p.score_display} / 4.0</div>
                                  </div>

                                  <div className="text-right w-16">
                                    <div className="text-[10px] text-stone-400 font-mono uppercase">Brecha</div>
                                    <div className={`text-xs font-bold font-mono ${parseFloat(gap) >= 0 ? 'text-emerald-700' : 'text-amber-700'}`}>
                                      {parseFloat(gap) >= 0 ? '0' : gap}
                                    </div>
                                  </div>

                                  <span className={`px-2.5 py-1 rounded-lg text-xs font-medium font-mono ${
                                    p.maturity_band === 'Managed' || p.maturity_band === 'Optimized'
                                      ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                                      : 'bg-amber-50 text-amber-800 border border-amber-200'
                                  }`}>
                                    {p.maturity_band}
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>

                        {/* Pillar Deep Dive Inspection Card */}
                        <div className="bg-white border border-stone-200/80 rounded-2xl p-6 space-y-4 shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
                          {selectedPillar ? (
                            <div className="space-y-4">
                              <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                                <span className="text-[10px] font-mono uppercase text-[#0072BC] font-bold">
                                  Pillar Inspector
                                </span>
                                <span className="text-xs font-bold font-mono text-emerald-700">
                                  Score: {selectedPillar.score_display} / 5.0
                                </span>
                              </div>

                              <h3 className="text-sm font-bold text-[#1d1d1f]">{selectedPillar.pillar_label}</h3>

                              <div className="p-3.5 rounded-xl bg-[#fbfbfa] border border-stone-200 text-xs text-stone-700 leading-relaxed font-sans max-h-72 overflow-y-auto whitespace-pre-wrap">
                                {selectedPillar.executive_reading || 'Detailed actuarial assessment available in compiled final deliverable.'}
                              </div>

                              <button
                                onClick={() => {
                                  setActiveTab('war_room');
                                  setChatInput(`Condicionante para pilar [${selectedPillar.pillar_label}]: Mejorar madurez desde ${selectedPillar.score_display} hacia Nivel 4.`);
                                }}
                                className="w-full flex items-center justify-center gap-2 py-2.5 px-3 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 text-slate-950 transition-all shadow-sm shadow-amber-500/20"
                              >
                                <Zap className="h-3.5 w-3.5" /> Dispatch Mitigation to War Room
                              </button>
                            </div>
                          ) : (
                            <div className="text-center py-12 space-y-2 text-stone-400 text-xs font-mono">
                              <Layers className="h-8 w-8 mx-auto text-stone-300" />
                              <div>Select a pillar from the list to inspect actuarial findings and operational gaps.</div>
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* PHASE 2: ONLINE TECHNICAL ANNEX */}
                {activeTab === 'report' && (
                  <ReportViewer
                    clientSlug={activeOpp?.client_slug || activeOpp?.archetype_id || 'nordic_grid_power_gmbh'}
                    clientName={activeOpp?.company_name || 'Cliente'}
                  />
                )}

                {/* FASE 3: INGESTA DE EVIDENCIAS (DROPZONE ESTILO BIDSTRATEGY) */}
                {activeTab === 'evidence' && (
                  <div className="space-y-6 max-w-4xl">
                    <div className="p-8 rounded-2xl bg-white border-2 border-dashed border-stone-300 text-center space-y-4 hover:border-[#0072BC] transition-colors shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
                      <div className="h-14 w-14 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0072BC] mx-auto shadow-xs">
                        <UploadCloud className="h-7 w-7" />
                      </div>
                      <div className="space-y-1">
                        <h3 className="text-sm font-bold text-[#1d1d1f]">
                          Technical Evidence Ingestion & RFP Upload for {activeOpp?.company_name}
                        </h3>
                        <p className="text-xs text-stone-500">
                          Supports ZIP archives with client-side decompression, PDFs, DOCX, and XLSX files.
                        </p>
                      </div>

                      <button
                        onClick={() => setShowUploadModal(true)}
                        className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white transition-all shadow-sm shadow-[#0072BC]/20"
                      >
                        <UploadCloud className="h-4 w-4" /> Open Modal de Carga Asistida
                      </button>
                    </div>

                    {/* Evidence Folder Status */}
                    <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4">
                      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                        <h4 className="text-xs font-bold text-[#1d1d1f] font-mono uppercase tracking-wider">
                          Sovereign On-Disk Storage Path
                        </h4>
                        <span className="text-[11px] font-mono text-emerald-700 font-semibold">Physical Isolation Active</span>
                      </div>
                      <div className="font-mono text-xs text-stone-700 bg-[#fbfbfa] p-3 rounded-xl border border-stone-200">
                        source_docs/{activeOpp?.client_slug || activeOpp?.archetype_id}/
                      </div>
                      <p className="text-xs text-stone-600 leading-relaxed font-sans">
                        Evidence deposited in this dossier is automatically processed by engine extractors to calibrate Beta-Binomial vulnerability distributions and Gamma-Poisson conjugate priors for Open FAIR modeling.
                      </p>
                    </div>
                  </div>
                )}

                {/* PHASE 4: TACTICAL WAR ROOM & OPEN FAIR MODEL */}
                {activeTab === 'war_room' && (
                  <div className="space-y-6 max-w-6xl">
                    {/* War Room Dialog Box */}
                    <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
                      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-xl bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                            <MessageSquare className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-[#1d1d1f]">
                              Tactical War Room — Live ADR Mutator & Strategic Dialogue
                            </h3>
                            <p className="text-[11px] text-stone-500">
                              Introduce restricciones sobrevenidas (persistidas de forma inmutable en PostgreSQL).
                            </p>
                          </div>
                        </div>
                        <span className="text-[10px] font-mono text-amber-800 bg-amber-50 border border-amber-200 px-2 py-0.5 rounded-full font-semibold">
                          ADR MUTATOR ACTIVO
                        </span>
                      </div>

                      {/* Messages History */}
                      <div className="bg-[#fbfbfa] border border-stone-200 rounded-xl p-4 min-h-[220px] max-h-[360px] overflow-y-auto space-y-3 font-mono text-xs">
                        {warRoomHistory.length === 0 ? (
                          <div className="text-center py-12 text-stone-400 text-xs">
                            Active tactical communication channel. Enter a constraint directive to recompute actuarial bounds for {activeOpp?.company_name}.
                          </div>
                        ) : (
                          warRoomHistory.map((msg, i) => (
                            <div
                              key={i}
                              className={`p-3.5 rounded-xl max-w-2xl ${
                                msg.role === 'user'
                                  ? 'ml-auto bg-blue-50 border border-blue-200 text-blue-900 shadow-2xs'
                                  : 'mr-auto bg-white border border-stone-200 text-stone-800 shadow-2xs'
                              }`}
                            >
                              <div className="flex items-center justify-between mb-1 text-[10px] text-stone-400">
                                <span className="font-semibold text-stone-600">{msg.role === 'user' ? '👤 Lead Engineer' : '🤖 War Room Lead Architect'}</span>
                                <span>{msg.timestamp}</span>
                              </div>
                              <p className="whitespace-pre-wrap leading-relaxed">{msg.text}</p>
                              {msg.impacted_vectors && msg.impacted_vectors.length > 0 && (
                                <div className="mt-2 pt-2 border-t border-stone-200/80 flex flex-wrap gap-1">
                                  {msg.impacted_vectors.map((vec, vi) => (
                                    <span key={vi} className="text-[9px] px-1.5 py-0.5 rounded bg-blue-100 text-[#0072BC] border border-blue-200 font-semibold">
                                      {vec}
                                    </span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))
                        )}
                        {chatLoading && (
                          <div className="flex items-center gap-2 text-amber-600 py-2">
                            <Loader2 className="h-4 w-4 animate-spin" />
                            <span>War Room Architect is analyzing actuarial impact and recalibrating bounds...</span>
                          </div>
                        )}
                      </div>

                      {/* Chat Input */}
                      <form onSubmit={handleSendWarRoomChat} className="flex gap-2">
                        <input
                          type="text"
                          aria-label="Enter tactical constraint"
                          value={chatInput}
                          onChange={(e) => setChatInput(e.target.value)}
                          placeholder="Enter tactical constraint (e.g. Enforce ISO 27001 certification and client-managed KMS encryption)..."
                          className="flex-1 bg-white border border-stone-200 rounded-xl px-4 py-2.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] transition-all font-mono"
                        />
                        <button
                          type="submit"
                          disabled={chatLoading || !chatInput.trim()}
                          className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-slate-950 transition-all shadow-sm shadow-amber-500/20 disabled:opacity-50 flex items-center gap-2"
                        >
                          <Send className="h-3.5 w-3.5" /> Enviar Ajuste
                        </button>
                      </form>
                    </div>

                    {/* Simulador Actuarial What-If (Monte Carlo & Stress Testing) */}
                    <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
                      <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                        <div className="flex items-center gap-3">
                          <div className="h-9 w-9 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0072BC]">
                            <Cpu className="h-5 w-5" />
                          </div>
                          <div>
                            <h3 className="text-sm font-bold text-[#1d1d1f]">
                              What-If Actuarial Simulator · Open FAIR Frequency and Vulnerability Stress
                            </h3>
                            <p className="text-[11px] text-stone-500">
                              Dynamically tune Bayesian parameters to simulate projected Annual Loss Expectancy (ALE) in real time.
                            </p>
                          </div>
                        </div>
                        <span className="text-[10px] font-mono text-purple-700 bg-purple-50 border border-purple-200 px-2.5 py-0.5 rounded-full font-semibold">
                          MONTE CARLO 10.000 IT.
                        </span>
                      </div>

                      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 pt-2">
                        {/* TEF Slider */}
                        <div className="space-y-2 p-4 rounded-xl bg-[#fbfbfa] border border-stone-200/80">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-semibold text-stone-700">Frecuencia Amenaza (TEF)</span>
                            <span className="font-mono font-bold text-[#0072BC]">{tefSlider.toFixed(2)} ev/yr</span>
                          </div>
                          <input
                            type="range"
                            aria-label="Threat Event Frequency (TEF)"
                            min="0.01"
                            max="1.50"
                            step="0.01"
                            value={tefSlider}
                            onChange={(e) => setTefSlider(parseFloat(e.target.value))}
                            className="w-full accent-[#0072BC] cursor-pointer"
                          />
                          <p className="text-[10px] text-stone-400 font-mono">Gamma-Poisson Conjugate Prior</p>
                        </div>

                        {/* VULN Slider */}
                        <div className="space-y-2 p-4 rounded-xl bg-[#fbfbfa] border border-stone-200/80">
                          <div className="flex justify-between items-center text-xs">
                            <span className="font-semibold text-stone-700">Vulnerabilidad (VULN)</span>
                            <span className="font-mono font-bold text-amber-700">{vulnSlider.toFixed(1)}% prob.</span>
                          </div>
                          <input
                            type="range"
                            aria-label="Vulnerability (VULN)"
                            min="1.0"
                            max="50.0"
                            step="0.5"
                            value={vulnSlider}
                            onChange={(e) => setVulnSlider(parseFloat(e.target.value))}
                            className="w-full accent-amber-500 cursor-pointer"
                          />
                          <p className="text-[10px] text-stone-400 font-mono">Beta-Binomial Distribution</p>
                        </div>

                        {/* Dynamic Recalculated ALE Result Card */}
                        <div className="p-4 rounded-xl bg-blue-50/60 border border-blue-200 flex flex-col justify-center space-y-1">
                          <div className="text-[10px] font-mono text-[#0072BC] uppercase tracking-wider font-bold">
                            ALE Recalculada en Vivo (What-If)
                          </div>
                          <div className="text-xl font-bold font-mono text-[#1d1d1f]">
                            {(131574.57 * (tefSlider / 0.04) * (vulnSlider / 14.2)).toLocaleString('es-ES', { maximumFractionDigits: 2 })} {activeOpp?.currency || 'EUR'}
                          </div>
                          <div className="text-[10px] text-stone-500 font-mono">
                            Projected loss from active Bayesian calibration
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* Live Telemetry Streaming Console */}
                    <div className="bg-[#0f172a] border border-slate-800 rounded-2xl p-6 shadow-xl space-y-3">
                      <div className="flex items-center justify-between border-b border-slate-800 pb-3">
                        <div className="flex items-center gap-2 text-xs font-bold text-white font-mono uppercase tracking-wider">
                          <Terminal className="h-4 w-4 text-emerald-400" />
                          Live Python Telemetry Stream Console
                        </div>
                        <button
                          onClick={() => setTelemetryLogs('Consola reiniciada.\n')}
                          className="text-[10px] font-mono px-2.5 py-1 rounded bg-slate-800 text-slate-300 hover:text-white transition-colors border border-slate-700"
                        >
                          Limpiar Consola
                        </button>
                      </div>

                      <div className="bg-[#020617] border border-slate-900 rounded-xl p-4 font-mono text-xs text-emerald-400/90 whitespace-pre-wrap leading-relaxed max-h-60 overflow-y-auto shadow-inner">
                        {telemetryLogs}
                      </div>
                    </div>
                  </div>
                )}

                {/* PHASE 5: USER MANAGEMENT & HRBAC GOVERNANCE */}
                {activeTab === 'governance' && currentUser.role === 'ADMIN' && (
                  <div className="space-y-6 max-w-6xl">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-white border border-stone-200/80 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
                      <div className="space-y-1">
                        <div className="flex items-center gap-2">
                          <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-purple-50 text-purple-700 border border-purple-200 font-semibold flex items-center gap-1">
                            <Crown className="w-3 h-3" /> Nivel 3 · Superadministrador
                          </span>
                          <span className="text-[10px] font-mono text-stone-500">
                            Modelo HRBAC (ANSI/INCITS 359-2004)
                          </span>
                        </div>
                        <h2 className="text-base font-bold text-[#1d1d1f]">
                          Access Control, User Management & Live Suspension
                        </h2>
                        <p className="text-xs text-stone-500">
                          Instantly suspend or reactivate corporate accounts in PostgreSQL with RLS isolation.
                        </p>
                      </div>

                      <button
                        onClick={loadGovernance}
                        disabled={governanceLoading}
                        className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-stone-50 hover:bg-stone-100 text-stone-700 border border-stone-200 transition-colors shadow-2xs self-start sm:self-auto"
                      >
                        <RefreshCw className={`w-3.5 h-3.5 ${governanceLoading ? 'animate-spin' : ''}`} />
                        <span>Actualizar Directorio</span>
                      </button>
                    </div>

                    {/* Users Management Table */}
                    <div className="bg-white border border-stone-200/80 rounded-2xl overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.03)] divide-y divide-stone-100">
                      <div className="p-4 px-6 bg-[#fbfbfa] border-b border-stone-100 flex items-center justify-between font-mono text-[11px] text-stone-500 uppercase font-bold tracking-wider">
                        <span>Usuario & Credencial</span>
                        <div className="flex items-center gap-10 pr-4">
                          <span className="w-28 text-center">Rol Acumulativo</span>
                          <span className="w-36 text-center">Empresa Asignada</span>
                          <span className="w-24 text-center">Estado</span>
                          <span className="w-36 text-right">Action de Gobierno</span>
                        </div>
                      </div>

                      {userProfiles.length === 0 ? (
                        <div className="p-12 text-center text-stone-400 font-mono text-xs">
                          {governanceLoading ? 'Cargando directorio de usuarios...' : 'No se encontraron usuarios.'}
                        </div>
                      ) : (
                        userProfiles.map((u) => (
                          <div key={u.id} data-user-email={u.email} className="p-4 px-6 flex items-center justify-between hover:bg-stone-50/50 transition-colors">
                            {/* User details */}
                            <div className="flex items-center gap-3">
                              <div className={`h-9 w-9 rounded-xl flex items-center justify-center font-mono text-xs font-bold shrink-0 ${
                                u.is_blocked
                                  ? 'bg-rose-100 text-rose-700 border border-rose-200'
                                  : u.role === 'ADMIN'
                                  ? 'bg-purple-100 text-purple-700 border border-purple-200'
                                  : u.role === 'CONSULTANT'
                                  ? 'bg-blue-100 text-[#0072BC] border border-blue-200'
                                  : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                              }`}>
                                {u.full_name?.charAt(0) || 'U'}
                              </div>
                              <div>
                                <div className="text-xs font-bold text-[#1d1d1f] flex items-center gap-2">
                                  <span>{u.full_name}</span>
                                  {u.is_blocked && (
                                    <span className="text-[9px] font-mono px-1.5 py-0.2 rounded bg-rose-100 text-rose-700 font-bold border border-rose-200">
                                      BLOQUEADO
                                    </span>
                                  )}
                                </div>
                                <div className="text-[11px] font-mono text-stone-500">{u.email}</div>
                              </div>
                            </div>

                            {/* Role selector, tenant, status, and action */}
                            <div className="flex items-center gap-10 pr-4">
                              {/* Role Selector */}
                              <div className="w-28 text-center">
                                <select
                                  value={u.role}
                                  onChange={(e) => handleUpdateRole(u.id, e.target.value as any)}
                                  disabled={u.email === currentUser.email}
                                  className="text-[11px] font-mono font-semibold px-2 py-1 rounded-lg border border-stone-200 bg-white text-stone-700 focus:outline-none focus:border-[#0072BC] cursor-pointer"
                                >
                                  <option value="ADMIN">ADMIN</option>
                                  <option value="CONSULTANT">CONSULTOR</option>
                                  <option value="CLIENT">CLIENTE</option>
                                </select>
                              </div>

                              {/* Tenant Scope */}
                              <div className="w-36 text-center text-xs font-mono text-stone-600 truncate">
                                {u.client_slug ? u.client_slug : 'Global (Multi-Cuenta)'}
                              </div>

                              {/* Status Badge */}
                              <div className="w-24 text-center">
                                <span className={`text-[10px] font-mono font-semibold px-2 py-0.5 rounded-full ${
                                  u.is_blocked
                                    ? 'bg-rose-100 text-rose-800 border border-rose-200'
                                    : 'bg-emerald-100 text-emerald-800 border border-emerald-200'
                                }`}>
                                  {u.is_blocked ? 'Suspended' : 'Active'}
                                </span>
                              </div>

                              {/* Block/Unblock Button */}
                              <div className="w-36 text-right">
                                {u.email === currentUser.email ? (
                                  <span className="text-[10px] font-mono text-stone-400 italic">Current Session</span>
                                ) : u.is_blocked ? (
                                  <button
                                    onClick={() => handleToggleBlock(u.id, false)}
                                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 transition-colors flex items-center gap-1 ml-auto"
                                  >
                                    <UserCheck className="w-3.5 h-3.5" /> Reactivate
                                  </button>
                                ) : (
                                  <button
                                    onClick={() => handleToggleBlock(u.id, true)}
                                    className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-rose-50 hover:bg-rose-100 text-rose-700 border border-rose-300 transition-colors flex items-center gap-1 ml-auto"
                                  >
                                    <UserX className="w-3.5 h-3.5" /> Bloquear
                                  </button>
                                )}
                              </div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  </div>
                )}
              </div>
            </main>
          </>
        )}
      </div>

      {/* Modal de Ingesta de Evidencias */}
      <KnowledgeHubModal
        isOpen={showUploadModal}
        onClose={() => setShowUploadModal(false)}
        clientSlug={activeOpp?.archetype_id || 'generic_client'}
        clientName={activeOpp?.company_name || 'Cliente'}
        onUploadComplete={() => {
          setNotification({ type: 'success', message: 'Evidencias ingestadas exitosamente en source_docs.' });
        }}
      />

      {/* Modal de High de New Expediente */}
      <NewClientModal
        isOpen={showNewClientModal}
        onClose={() => setShowNewClientModal(false)}
        onClientCreated={(slug) => {
          loadData(slug);
          setActiveTab('radar');
          setNotification({ type: 'success', message: `New dossier '${slug}' created and activated successfully.` });
        }}
      />
    </div>
  );
}
