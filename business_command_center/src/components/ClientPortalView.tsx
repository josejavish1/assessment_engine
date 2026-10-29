'use client';

import React, { useState, useEffect } from 'react';
import {
  Building2,
  Globe,
  ShieldCheck,
  Activity,
  FileText,
  Download,
  UploadCloud,
  CheckCircle2,
  Calendar,
  ChevronDown,
  Printer,
  Plus,
  ArrowRight,
  Clock,
  Sparkles,
  Layers,
  FileCheck
} from 'lucide-react';
import { type SimulationArchetype } from '@/app/actions/assessment';

interface SubsidiaryAssessment {
  id: string;
  name: string;
  country: string;
  flag: string;
  framework: string;
  period: string;
  score: string;
  band: string;
  ale: string;
  status: 'Certified' | 'En Progreso' | 'Planificado';
}

interface ClientPortalViewProps {
  currentClient?: SimulationArchetype | null;
  onOpenUploadModal: () => void;
}

export function ClientPortalView({ currentClient, onOpenUploadModal }: ClientPortalViewProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'deliverables' | 'evidence'>('overview');
  const [selectedSubId, setSelectedSubId] = useState<string>('sub_1');
  const [requestModalOpen, setRequestModalOpen] = useState(false);
  const [newSocietyName, setNewSocietyName] = useState('');
  const [newCountry, setNewCountry] = useState('Spain (ES)');
  const [newFramework, setNewFramework] = useState('ENS High Category');
  const [successToast, setSuccessToast] = useState<string | null>(null);

  const clientName = currentClient?.company_name || 'Cliente Corporativo';

  // Subsidiaries & Periodic Assessments for the Corporate Client
  const [subsidiaries, setSubsidiaries] = useState<SubsidiaryAssessment[]>([
    {
      id: 'sub_1',
      name: `${clientName} · Sede Central`,
      country: currentClient?.country || 'Germany (DE)',
      flag: '🇩🇪',
      framework: currentClient?.standard || 'NIS2 / Critical Infrastructure',
      period: 'Q3 2026 (Oficial Certificado)',
      score: currentClient?.global_score || '2.9 / 5.0',
      band: currentClient?.global_band || 'Defined',
      ale: currentClient?.ale_formatted || '€131,574/yr',
      status: 'Certified',
    },
    {
      id: 'sub_2',
      name: `${clientName.split(' ')[0]} Austria Energy AG`,
      country: 'Austria (AT)',
      flag: '🇦🇹',
      framework: 'DORA / Operational Resilience',
      period: 'Q4 2026 (En Proceso)',
      score: '3.4 / 5.0',
      band: 'Managed',
      ale: '€89,200/yr',
      status: 'En Progreso',
    },
    {
      id: 'sub_3',
      name: `${clientName.split(' ')[0]} Offshore Wind B.V.`,
      country: 'Netherlands (NL)',
      flag: '🇳🇱',
      framework: 'Directiva de Ciberseguridad Critical',
      period: 'Q1 2027 (Planificado)',
      score: 'Pending',
      band: 'Initial Assessment',
      ale: 'Por calcular',
      status: 'Planificado',
    },
  ]);

  useEffect(() => {
    if (currentClient) {
      setSubsidiaries((prev) => [
        {
          id: 'sub_1',
          name: `${currentClient.company_name} · Sede Central`,
          country: currentClient.country || 'Germany (DE)',
          flag: currentClient.country?.includes('ES') ? '🇪🇸' : currentClient.country?.includes('DE') ? '🇩🇪' : '🌐',
          framework: currentClient.standard || 'NIS2 / Critical Infrastructure',
          period: 'Q3 2026 (Oficial Certificado)',
          score: currentClient.global_score || '2.9 / 5.0',
          band: currentClient.global_band || 'Defined',
          ale: currentClient.ale_formatted || '€131,574/yr',
          status: 'Certified',
        },
        ...prev.slice(1),
      ]);
    }
  }, [currentClient?.company_name, currentClient?.global_score, currentClient?.ale_formatted]);

  const activeSub = subsidiaries.find((s) => s.id === selectedSubId) || subsidiaries[0];

  const handleRequestAssessment = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newSocietyName.trim()) return;

    const newSub: SubsidiaryAssessment = {
      id: `sub_${Date.now()}`,
      name: newSocietyName.trim(),
      country: newCountry,
      flag: newCountry.includes('ES') ? '🇪🇸' : newCountry.includes('DE') ? '🇩🇪' : newCountry.includes('US') ? '🇺🇸' : '🌐',
      framework: newFramework,
      period: 'Q1 2027 (Solicitud Registrada)',
      score: 'Pending',
      band: 'Por calibrar',
      ale: 'Under Estimation',
      status: 'Planificado',
    };

    setSubsidiaries((prev) => [...prev, newSub]);
    setSelectedSubId(newSub.id);
    setRequestModalOpen(false);
    setNewSocietyName('');
    setSuccessToast(`Assessment requested successfully for ${newSub.name}. Your NTT DATA account partner will activate it.`);
    setTimeout(() => setSuccessToast(null), 5000);
  };

  if (!currentClient) {
    return null;
  }

  return (
    <div className="max-w-6xl mx-auto space-y-8 pb-16 font-sans">
      {/* Toast Notification */}
      {successToast && (
        <div className="p-4 rounded-xl bg-emerald-50 border border-emerald-200 text-emerald-800 text-xs flex items-center justify-between shadow-sm animate-in fade-in">
          <div className="flex items-center gap-2">
            <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
            <span className="font-medium">{successToast}</span>
          </div>
          <button onClick={() => setSuccessToast(null)} className="text-emerald-600 hover:text-emerald-900 font-bold">&times;</button>
        </div>
      )}

      {/* Hero Welcome & Corporate Subsidiary Switcher */}
      <div className="p-8 rounded-3xl bg-white border border-stone-200/80 shadow-[0_4px_20px_rgba(0,0,0,0.03)] space-y-6">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 border-b border-stone-100 pb-6">
          <div className="space-y-1.5">
            <div className="flex items-center gap-2">
              <span className="text-[11px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0072BC] border border-blue-200 font-bold">
                Portal Ejecutivo del CIO / CISO
              </span>
              <span className="text-[11px] font-mono text-emerald-700 bg-emerald-50 border border-emerald-200 px-2.5 py-0.5 rounded-full font-semibold flex items-center gap-1">
                <CheckCircle2 className="h-3 w-3" /> Entorno Soberano Certificado
              </span>
            </div>
            <h1 className="text-2xl font-bold text-[#1d1d1f] tracking-tight">
              {currentClient.company_name}
            </h1>
            <p className="text-xs text-stone-500 max-w-2xl leading-relaxed">
              Technology maturity oversight, quantitative actuarial risk quantification, and continuous statutory compliance managed by NTT DATA.
            </p>
          </div>

          {/* Subsidiary / Assessment Switcher */}
          <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <div className="relative">
              <label className="text-[10px] font-mono uppercase text-stone-400 font-bold block mb-1">
                Subsidiary / Active Assessment
              </label>
              <select
                value={selectedSubId}
                onChange={(e) => setSelectedSubId(e.target.value)}
                className="bg-[#fbfbfa] border border-stone-200 rounded-xl px-4 py-2.5 text-xs font-semibold text-[#1d1d1f] focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all shadow-2xs pr-8 cursor-pointer"
              >
                {subsidiaries.map((sub) => (
                  <option key={sub.id} value={sub.id}>
                    {sub.flag} {sub.name} ({sub.period})
                  </option>
                ))}
              </select>
            </div>

            <button
              onClick={() => setRequestModalOpen(true)}
              className="mt-auto flex items-center justify-center gap-1.5 px-4 py-2.5 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 text-stone-700 border border-stone-200 transition-all shadow-2xs"
            >
              <Plus className="h-3.5 w-3.5 text-[#0072BC]" />
              <span>New Subsidiary / Country</span>
            </button>
          </div>
        </div>

        {/* 3 Executive High-Impact KPI Tiles */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-5">
          {/* Tile 1: Global Maturity Score */}
          <div className="p-6 rounded-2xl bg-[#fbfbfa] border border-stone-200/80 space-y-3">
            <div className="flex items-center justify-between text-xs text-stone-500">
              <span className="font-semibold uppercase tracking-wider text-[10px]">Madurez Global</span>
              <span className="px-2 py-0.5 rounded-full bg-blue-100 text-[#0072BC] font-mono font-bold text-[10px]">
                Escala CMMI 1-5
              </span>
            </div>
            <div className="flex items-baseline gap-3">
              <span className="text-3xl font-extrabold text-[#1d1d1f] tracking-tight">{activeSub.score}</span>
              <span className="text-xs font-semibold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                {activeSub.band}
              </span>
            </div>
            <div className="space-y-1">
              <div className="h-2 w-full rounded-full bg-stone-200 overflow-hidden">
                <div className="h-full bg-[#0072BC] rounded-full transition-all duration-500" style={{ width: '58%' }} />
              </div>
              <div className="flex justify-between text-[10px] text-stone-400 font-mono">
                <span>Estado Actual: 2.9</span>
                <span>Strategic Target: 4.0</span>
              </div>
            </div>
          </div>

          {/* Tile 2: FAIR Residual Financial Risk */}
          <div className="p-6 rounded-2xl bg-[#fbfbfa] border border-stone-200/80 space-y-3">
            <div className="flex items-center justify-between text-xs text-stone-500">
              <span className="font-semibold uppercase tracking-wider text-[10px]">Risk Exposure (Open FAIR)</span>
              <span className="px-2 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-mono font-bold text-[10px]">
                Monte Carlo 10k
              </span>
            </div>
            <div className="text-3xl font-extrabold text-emerald-700 tracking-tight">
              {activeSub.ale}
            </div>
            <div className="text-xs text-stone-500 leading-relaxed">
              Annualized Loss Expectancy (ALE) bounded. 95th percentile maximum loss estimated at <strong className="text-[#1d1d1f]">€353,196</strong>.
            </div>
          </div>

          {/* Tile 3: Regulatory Compliance Status */}
          <div className="p-6 rounded-2xl bg-[#fbfbfa] border border-stone-200/80 space-y-3">
            <div className="flex items-center justify-between text-xs text-stone-500">
              <span className="font-semibold uppercase tracking-wider text-[10px]">Marco Regulatorio Oficial</span>
              <span className="px-2 py-0.5 rounded-full bg-purple-100 text-purple-800 font-mono font-bold text-[10px]">
                {activeSub.country}
              </span>
            </div>
            <div className="text-lg font-bold text-[#1d1d1f] tracking-tight">
              {activeSub.framework}
            </div>
            <div className="text-xs text-stone-500 flex items-center gap-1.5">
              <ShieldCheck className="h-4 w-4 text-emerald-600 shrink-0" />
              <span>Convergencia normativa verificada al 87%</span>
            </div>
          </div>
        </div>
      </div>

      {/* 3 Executive Tabs */}
      <div className="border-b border-stone-200 bg-white rounded-2xl px-6 flex gap-2 shadow-2xs">
        {[
          { id: 'overview', label: '1. Capability Diagnostic & Radar', icon: Activity },
          { id: 'deliverables', label: '2. Entregables Oficiales & Descargas', icon: FileCheck },
          { id: 'evidence', label: '3. Technical Evidence Submission', icon: UploadCloud },
        ].map((tab) => {
          const Icon = tab.icon;
          const isActive = activeTab === tab.id;
          return (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 py-4 px-4 text-xs font-semibold border-b-2 transition-all ${
                isActive
                  ? 'border-[#0072BC] text-[#0072BC] font-bold bg-blue-50/40'
                  : 'border-transparent text-stone-500 hover:text-stone-800'
              }`}
            >
              <Icon className={`h-4 w-4 ${isActive ? 'text-[#0072BC]' : 'text-stone-400'}`} />
              <span>{tab.label}</span>
            </button>
          );
        })}
      </div>

      {/* Tab 1: Overview & Vector Radar */}
      {activeTab === 'overview' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Vector Radar Card */}
          <div className="p-7 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <h3 className="text-sm font-bold text-[#1d1d1f] flex items-center gap-2">
                <Activity className="h-4 w-4 text-[#0072BC]" />
                Radar Multidimensional de Torres (Vector 10-Ejes)
              </h3>
              <span className="text-[10px] font-mono text-stone-500">{activeSub.name}</span>
            </div>

            <div className="flex items-center justify-center p-4 bg-[#fbfbfa] rounded-xl border border-stone-200/80 min-h-[380px]">
              {currentClient.radar_path ? (
                <img
                  src={`/api/download?path=${encodeURIComponent(currentClient.radar_path)}`}
                  alt="Radar de Madurez Multidimensional"
                  className="max-h-[360px] w-auto object-contain"
                />
              ) : (
                <div className="text-center text-stone-400 font-mono text-xs">
                  Generating actuarial radar visualization...
                </div>
              )}
            </div>

            <div className="flex justify-end pt-2">
              <a
                href={`/api/download?path=${encodeURIComponent(currentClient.radar_path || '')}`}
                download
                className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 text-stone-700 border border-stone-200 transition-all shadow-2xs"
              >
                <Download className="h-3.5 w-3.5 text-[#0072BC]" /> Download High-Resolution PNG
              </a>
            </div>
          </div>

          {/* Executive Synthesis Card */}
          <div className="p-7 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <h3 className="text-sm font-bold text-[#1d1d1f] flex items-center gap-2">
                <Sparkles className="h-4 w-4 text-emerald-600" />
                Executive Synthesis of Technical Assessment
              </h3>
            </div>

            <p className="text-xs text-stone-600 leading-relaxed font-sans">
              Assessment for <strong className="text-[#1d1d1f]">{activeSub.name}</strong> concludes that infrastructure displays a functional operational posture with consolidation required to achieve compliance alignment with <strong className="text-[#0072BC]">{activeSub.framework}</strong>.
            </p>

            <div className="space-y-3 pt-2">
              <span className="text-[10px] font-mono uppercase text-stone-400 font-bold block">
                Pilares Evaluados & Estado de Convergencia
              </span>

              {currentClient.pillars?.map((p, idx) => (
                <div key={idx} className="p-3 rounded-xl bg-[#fbfbfa] border border-stone-200/80 flex items-center justify-between text-xs">
                  <div className="flex items-center gap-2.5">
                    <span className="h-6 w-6 rounded-lg bg-stone-100 text-[#0072BC] font-mono font-bold text-[10px] flex items-center justify-center">
                      P{idx + 1}
                    </span>
                    <span className="font-semibold text-[#1d1d1f]">{p.pillar_label}</span>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="font-mono font-bold text-stone-700">{p.score_display} / 4.0</span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-semibold ${
                      p.maturity_band === 'Managed' || p.maturity_band === 'Optimized'
                        ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                        : 'bg-amber-50 text-amber-800 border border-amber-200'
                    }`}>
                      {p.maturity_band}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Tab 2: Official Deliverables */}
      {activeTab === 'deliverables' && (
        <div className="space-y-6">
          <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div>
              <h3 className="text-sm font-bold text-[#1d1d1f]">
                Entregables Oficiales Certificados por NTT DATA
              </h3>
              <p className="text-xs text-stone-500 mt-0.5">
                Formally compiled artifacts valid for executive committees, external auditors, and regulatory bodies.
              </p>
            </div>
            <button
              onClick={() => window.print()}
              className="flex items-center gap-2 px-4 py-2 rounded-xl text-xs font-semibold bg-stone-50 hover:bg-stone-100 text-stone-700 border border-stone-200 transition-colors shadow-2xs self-start sm:self-auto"
            >
              <Printer className="h-4 w-4 text-[#0072BC]" />
              <span>Imprimir / Exportar a PDF</span>
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Deliverable 1: Word Technical Annex */}
            <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="p-2.5 rounded-xl bg-blue-50 text-[#0072BC] border border-blue-200">
                    <FileText className="h-5 w-5" />
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-emerald-50 text-emerald-800 font-bold border border-emerald-200">
                    v1.0 Certificada
                  </span>
                </div>
                <h4 className="text-sm font-bold text-[#1d1d1f]">
                  Technical Annex and Executive Report (.docx)
                </h4>
                <p className="text-xs text-stone-500 leading-relaxed">
                  Comprehensive formal deliverable containing As-Is baseline diagnostic, To-Be target architecture, statutory gap analysis, and modernization roadmap.
                </p>
              </div>

              <a
                href={`/api/download?path=/home/jsanchhi/assessment_engine/working/out/simulations/${currentClient.client_slug || currentClient.archetype_id}/Anexo_Tecnico_${currentClient.client_slug || currentClient.archetype_id}.docx`}
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-sm shadow-[#0072BC]/20"
              >
                <Download className="h-4 w-4" /> Descargar Memoria Oficial (.docx)
              </a>
            </div>

            {/* Deliverable 2: Radar Chart Vectorial */}
            <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4 flex flex-col justify-between">
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="p-2.5 rounded-xl bg-purple-50 text-purple-700 border border-purple-200">
                    <Activity className="h-5 w-5" />
                  </span>
                  <span className="text-[10px] font-mono px-2 py-0.5 rounded-full bg-purple-50 text-purple-800 font-bold border border-purple-200">
                    Vector 300 DPI
                  </span>
                </div>
                <h4 className="text-sm font-bold text-[#1d1d1f]">
                  High-Resolution Vector Radar Visualization (.png)
                </h4>
                <p className="text-xs text-stone-500 leading-relaxed">
                  10-pillar quantitative visualization tailored for board presentations and public tenders.
                </p>
              </div>

              <a
                href={`/api/download?path=${encodeURIComponent(currentClient.radar_path || '')}`}
                download
                className="w-full flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 text-stone-700 border border-stone-200 transition-all shadow-2xs"
              >
                <Download className="h-4 w-4 text-[#0072BC]" /> Download Radar PNG
              </a>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: Evidence Submission Dropzone */}
      {activeTab === 'evidence' && (
        <div className="space-y-6">
          <div className="p-10 rounded-2xl bg-white border-2 border-dashed border-stone-300 hover:border-[#0072BC] transition-colors text-center space-y-4 shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
            <div className="h-16 w-16 rounded-2xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0072BC] mx-auto shadow-2xs">
              <UploadCloud className="h-8 w-8" />
            </div>
            <div className="space-y-1">
              <h3 className="text-base font-bold text-[#1d1d1f]">
                Submit Technical Documentation & Evidence for {activeSub.name}
              </h3>
              <p className="text-xs text-stone-500 max-w-md mx-auto">
                Drag and drop security policies, architecture diagrams, technical RFPs, or ZIP archives here.
              </p>
            </div>

            <button
              onClick={onOpenUploadModal}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white transition-all shadow-sm shadow-[#0072BC]/20"
            >
              <UploadCloud className="h-4 w-4" /> Seleccionar Archivos o ZIP
            </button>
          </div>

          {/* Evidence Ledger Status */}
          <div className="p-6 rounded-2xl bg-white border border-stone-200/80 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-3">
            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
              <h4 className="text-xs font-bold text-[#1d1d1f] font-mono uppercase tracking-wider">
                Sovereign Chain of Custody & Physical Air-Gapping Guarantee
              </h4>
              <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-full font-bold border border-emerald-200">
                Inmutable
              </span>
            </div>
            <p className="text-xs text-stone-600 leading-relaxed">
              All submitted documentation is stored exclusively in your local isolated dossier (`source_docs/{currentClient.client_slug || currentClient.archetype_id}/`) with SHA-256 cryptographic hashes guaranteeing forensic audibility.
            </p>
          </div>
        </div>
      )}

      {/* Modal: Request Assessment for New Society */}
      {requestModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 backdrop-blur-sm p-4 animate-in fade-in">
          <div className="bg-white border border-stone-200 rounded-3xl max-w-lg w-full p-7 shadow-2xl space-y-5">
            <div className="flex items-center justify-between border-b border-stone-100 pb-4">
              <div className="flex items-center gap-3">
                <div className="h-10 w-10 rounded-xl bg-blue-50 border border-blue-200 flex items-center justify-center text-[#0072BC]">
                  <Building2 className="h-5 w-5" />
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1d1d1f]">
                    Request Assessment for New Subsidiary or Jurisdiction
                  </h3>
                  <p className="text-[11px] text-stone-500 font-mono">
                    {currentClient.company_name} · Multi-Entidad Corporativa
                  </p>
                </div>
              </div>
              <button onClick={() => setRequestModalOpen(false)} className="text-stone-400 hover:text-stone-700 p-1 font-bold text-lg">&times;</button>
            </div>

            <form onSubmit={handleRequestAssessment} className="space-y-4">
              <div className="space-y-1">
                <label className="text-[10px] font-mono uppercase text-stone-500 font-bold block">
                  Nombre de la Sociedad / Filial *
                </label>
                <input
                  type="text"
                  required
                  placeholder="Ej. Nordic Grid Renovables Iberia S.L."
                  value={newSocietyName}
                  onChange={(e) => setNewSocietyName(e.target.value)}
                  className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl px-3.5 py-2.5 text-xs text-[#1d1d1f] focus:outline-none focus:bg-white focus:border-[#0072BC] transition-all font-sans"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-1">
                  <label className="text-[10px] font-mono uppercase text-stone-500 font-bold block">
                    Country / Jurisdiction
                  </label>
                  <select
                    value={newCountry}
                    onChange={(e) => setNewCountry(e.target.value)}
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl px-3 py-2 text-xs text-[#1d1d1f] focus:outline-none focus:border-[#0072BC]"
                  >
                    <option value="Spain (ES)">Spain (ES)</option>
                    <option value="Germany (DE)">Germany (DE)</option>
                    <option value="United Kingdom (UK)">United Kingdom (UK)</option>
                    <option value="United States (US)">United States (US)</option>
                    <option value="Austria (AT)">Austria (AT)</option>
                    <option value="Netherlands (NL)">Netherlands (NL)</option>
                  </select>
                </div>

                <div className="space-y-1">
                  <label className="text-[10px] font-mono uppercase text-stone-500 font-bold block">
                    Marco Regulatorio
                  </label>
                  <select
                    value={newFramework}
                    onChange={(e) => setNewFramework(e.target.value)}
                    className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl px-3 py-2 text-xs text-[#1d1d1f] focus:outline-none focus:border-[#0072BC]"
                  >
                    <option value="NIS2 / Critical Infrastructure">NIS2 / Critical Infrastructure</option>
                    <option value="DORA / Operational Resilience">DORA / Operational Resilience</option>
                    <option value="ENS High Category">ENS High Category</option>
                    <option value="ISO 27001">ISO 27001</option>
                    <option value="HIPAA">HIPAA</option>
                  </select>
                </div>
              </div>

              <div className="pt-4 border-t border-stone-100 flex justify-end gap-2">
                <button
                  type="button"
                  onClick={() => setRequestModalOpen(false)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold text-stone-500 hover:text-stone-800 transition-colors"
                >
                  Cancelar
                </button>
                <button
                  type="submit"
                  className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white transition-all shadow-sm shadow-[#0072BC]/20 flex items-center gap-1.5"
                >
                  <Plus className="h-3.5 w-3.5" /> Registrar Sociedad
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
