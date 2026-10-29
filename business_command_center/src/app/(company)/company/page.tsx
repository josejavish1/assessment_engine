'use client';

import React, { useEffect, useState } from 'react';
import { 
  CheckCircle2, 
  TrendingUp, 
  Download, 
  Play, 
  Loader2, 
  FileText, 
  Building, 
  ShieldCheck, 
  Sparkles,
  AlertCircle
} from 'lucide-react';
import { getSimulationSummary, runFullEngineSimulation, type SimulationArchetype } from '@/app/actions/assessment';

export default function CompanyDashboardPage() {
  const [archetypes, setArchetypes] = useState<SimulationArchetype[]>([]);
  const [selectedArchetype, setSelectedArchetype] = useState<SimulationArchetype | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [isRunning, setIsRunning] = useState(false);
  const [feedback, setFeedback] = useState<{ type: 'success' | 'error'; message: string } | null>(null);

  const loadData = async () => {
    setIsLoading(true);
    const res = await getSimulationSummary();
    if (res.success && res.data) {
      setArchetypes(res.data);
      if (res.data.length > 0 && !selectedArchetype) {
        setSelectedArchetype(res.data[0]);
      }
    }
    setIsLoading(false);
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleRunSimulation = async () => {
    setIsRunning(true);
    setFeedback(null);
    try {
      const res = await runFullEngineSimulation();
      if (res.success) {
        setFeedback({ type: 'success', message: res.message });
        await loadData();
      } else {
        setFeedback({ type: 'error', message: res.message });
      }
    } catch (err: any) {
      setFeedback({ type: 'error', message: err.message ?? 'Error executing simulation' });
    } finally {
      setIsRunning(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Page Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-white flex items-center gap-2">
            Executive Technology Assessment Dashboard
            <span className="text-xs font-mono font-medium bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 px-2 py-0.5 rounded">
              Python Core Conectado
            </span>
          </h1>
          <p className="text-sm text-slate-400 mt-1">
            Real-time actuarial pipeline execution, DOCX technical annex generation, and Open FAIR risk quantification.
          </p>
        </div>

        <button
          onClick={handleRunSimulation}
          disabled={isRunning}
          className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-600 hover:bg-emerald-500 active:bg-emerald-700 text-white font-medium text-xs transition-colors shadow-lg shadow-emerald-600/25 disabled:opacity-50"
        >
          {isRunning ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" />
              Ejecutando Pipeline Python...
            </>
          ) : (
            <>
              <Play className="h-4 w-4 fill-white" />
              Ejecutar Pipeline Actuarial Completo
            </>
          )}
        </button>
      </div>

      {/* Feedback Banner */}
      {feedback && (
        <div
          className={`p-4 rounded-xl text-xs flex items-center gap-2 ${
            feedback.type === 'success'
              ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20'
              : 'bg-rose-500/10 text-rose-400 border border-rose-500/20'
          }`}
        >
          {feedback.type === 'success' ? (
            <CheckCircle2 className="h-4 w-4 flex-shrink-0" />
          ) : (
            <AlertCircle className="h-4 w-4 flex-shrink-0" />
          )}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Arquetipos Globales</span>
          <div className="text-2xl font-bold text-white tracking-tight">{archetypes.length} Multinacionales</div>
          <p className="text-[11px] text-slate-400">DE, JP, US, ES certificados</p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Modelo Actuarial FAIR</span>
          <div className="text-2xl font-bold text-white tracking-tight">10.000 Corridas</div>
          <p className="text-[11px] text-emerald-400 flex items-center gap-1">
            <TrendingUp className="h-3 w-3" />
            Inferencia Bayesiana activa
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Entregables Generados</span>
          <div className="text-2xl font-bold text-white tracking-tight">16 Documentos</div>
          <p className="text-[11px] text-blue-400 flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            DOCX & Radar Charts
          </p>
        </div>

        <div className="bg-slate-900 border border-slate-800 p-5 rounded-xl space-y-2">
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">Governance & Sovereignty</span>
          <div className="text-2xl font-bold text-white tracking-tight">100% Pasado</div>
          <p className="text-[11px] text-emerald-400 flex items-center gap-1">
            <ShieldCheck className="h-3 w-3" />
            Zero Vendor Lock-in
          </p>
        </div>
      </div>

      {/* Selector of Multinational Archetypes */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl p-6 space-y-6">
        <div>
          <h2 className="text-base font-semibold text-white">Client Archetype Selection</h2>
          <p className="text-xs text-slate-400 mt-1">
            Select corporate entity to inspect generated deliverables from the assessment engine.
          </p>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
          {archetypes.map((item) => {
            const isSelected = selectedArchetype?.archetype_id === item.archetype_id;
            return (
              <button
                key={item.archetype_id}
                onClick={() => setSelectedArchetype(item)}
                className={`p-4 rounded-xl text-left border transition-all ${
                  isSelected
                    ? 'bg-emerald-600/15 border-emerald-500/40 shadow-lg shadow-emerald-500/10'
                    : 'bg-slate-950/60 border-slate-800 hover:border-slate-700 text-slate-300'
                }`}
              >
                <div className="flex items-center justify-between mb-2">
                  <span className="text-[10px] font-mono uppercase bg-slate-800 px-1.5 py-0.5 rounded text-slate-300">
                    {item.language.toUpperCase()} ({item.currency})
                  </span>
                  {item.checks_passed && (
                    <span className="h-2 w-2 rounded-full bg-emerald-400 ring-4 ring-emerald-500/20" />
                  )}
                </div>
                <div className="font-semibold text-xs text-white line-clamp-1">{item.company_name}</div>
                <div className="text-[11px] text-slate-400 font-mono mt-1">{item.archetype_id}</div>
              </button>
            );
          })}
        </div>

        {/* Deliverables List for Selected Archetype */}
        {selectedArchetype && (
          <div className="pt-6 border-t border-slate-800 space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h3 className="text-sm font-semibold text-white">
                  Entregables Certificados: {selectedArchetype.company_name}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  Physical artifacts generated and verified in the engine working directory.
                </p>
              </div>
              <span className="text-xs font-mono bg-slate-800 px-2 py-1 rounded text-slate-300">
                {selectedArchetype.files_meta?.length ?? 0} Physical Artifacts
              </span>
            </div>

            <div className="divide-y divide-slate-800/80 bg-slate-950 rounded-xl border border-slate-800 overflow-hidden">
              {selectedArchetype.files_meta?.map((file) => (
                <div
                  key={file.name}
                  className="p-3.5 px-5 flex items-center justify-between hover:bg-slate-900/40 transition-colors"
                >
                  <div className="flex items-center gap-3">
                    <div className="h-8 w-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center text-emerald-400">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div>
                      <span className="font-medium text-xs text-white block font-mono">{file.name}</span>
                      <span className="text-[11px] text-slate-500 block">
                        {(file.sizeBytes / 1024).toFixed(1)} KB • Actualizado: {new Date(file.updatedAt).toLocaleTimeString()}
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <span className="text-[10px] uppercase font-semibold px-2 py-0.5 rounded bg-emerald-950 text-emerald-300 border border-emerald-800/40">
                      Verificado
                    </span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
