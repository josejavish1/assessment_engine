'use client';

import React, { useState, useEffect } from 'react';
import { Play, XCircle, Terminal, Activity, Loader2, GitPullRequest, ArrowLeft } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { startPlanExecution, checkExecutionStatus, abortAndRevert, checkActionGate, authorizeActionGate } from '../actions/mcp';

interface ExecutiveExecutionDashboardProps {
  plan: any;
  requestDir: string;
  altIndex: number;
  onBack: () => void;
}

export function ExecutiveExecutionDashboard({ plan, requestDir, altIndex, onBack }: ExecutiveExecutionDashboardProps) {
  const [executionState, setExecutionState] = useState<'idle' | 'running' | 'completed' | 'error' | 'action_gate'>('idle');
  const [logs, setLogs] = useState<string>('');
  const [eta, setEta] = useState<number>(plan?.tasks?.length * 2 || 5); // Rough estimate in minutes
  const [actionGate, setActionGate] = useState<any>(null);

  const startExecution = async () => {
    setExecutionState('running');
    setLogs("Iniciando Pipeline de Ejecución Autónoma...\nCalculando Blast Radius...\nAsignando Agentes...\n\n");
    
    const res = await startPlanExecution(requestDir, altIndex);
    if (res.success && res.jobId) {
      const poll = setInterval(async () => {
        const statusRes = await checkExecutionStatus(res.jobId);
        if (statusRes.status === 'completed') {
          clearInterval(poll);
          setExecutionState('completed');
          setLogs(prev => prev + "\n✅ " + statusRes.result);
        } else if (statusRes.status === 'error') {
          clearInterval(poll);
          const agRes = await checkActionGate(requestDir);
          if (agRes.success && agRes.data?.action_gate_active) {
            setActionGate(agRes.data.data);
            setExecutionState('action_gate');
          } else {
            setExecutionState('error');
            setLogs(prev => prev + "\n❌ " + statusRes.result);
          }
        } else {
          // Decrement ETA slightly for effect
          setEta(e => Math.max(1, e - 0.1));
        }
      }, 3000);
    } else {
      setExecutionState('error');
      setLogs(prev => prev + `\n❌ Error al iniciar: ${res.error}`);
    }
  };

  const handleKillSwitch = async () => {
    if (!confirm("⚠️ ATENCIÓN: ¿Estás seguro de querer abortar la ejecución? El sistema ejecutará un 'git reset --hard' para revertir todos los cambios y asegurar el repositorio.")) return;
    
    setLogs(prev => prev + "\n\n🚨 ABORTANDO EJECUCIÓN...\nEjecutando git reset --hard...");
    const res = await abortAndRevert();
    setExecutionState('error');
    if (res.success) {
      setLogs(prev => prev + "\n✅ Repositorio revertido a su estado seguro.");
      alert("Ejecución abortada. El repositorio ha sido revertido a su estado seguro.");
    } else {
      setLogs(prev => prev + `\n❌ Error en el rollback: ${res.error}`);
    }
  };

  const handleAuthorizeActionGate = async () => {
    setLogs(prev => prev + "\n\n⚠️ AUTORIZANDO RUPTURA DE INVARIANTE (Action Gate Bypass)...\n");
    setActionGate(null);
    setExecutionState('running');
    const res = await authorizeActionGate(requestDir);
    if (res.success) {
      setLogs(prev => prev + "✅ Action Gate autorizado. Reintentando ejecución...\n");
      // Resuming execution
      const runRes = await startPlanExecution(requestDir, altIndex);
      if (runRes.success && runRes.jobId) {
        const poll = setInterval(async () => {
          const statusRes = await checkExecutionStatus(runRes.jobId);
          if (statusRes.result) setLogs(statusRes.result);
          if (statusRes.status === 'completed') {
            clearInterval(poll);
            setExecutionState('completed');
          } else if (statusRes.status === 'error') {
            clearInterval(poll);
            const agRes = await checkActionGate(requestDir);
            if (agRes.success && agRes.data?.action_gate_active) {
              setActionGate(agRes.data.data);
              setExecutionState('action_gate');
            } else {
              setExecutionState('error');
            }
          }
        }, 3000);
      }
    } else {
      setLogs(prev => prev + `\n❌ Error autorizando: ${res.error}`);
      setExecutionState('error');
    }
  };

  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-hidden animate-in fade-in duration-300">
      {/* Header Bar */}
      <div className="border-b border-border/50 bg-muted/10 p-6 flex items-center justify-between shrink-0">
        <div>
          <button 
            onClick={onBack}
            disabled={executionState === 'running'}
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground mb-4 transition-colors disabled:opacity-50"
          >
            <ArrowLeft className="h-4 w-4" /> Volver a Planificación
          </button>
          <div className="flex items-center gap-4">
            <h2 className="text-2xl font-bold tracking-tight text-foreground flex items-center gap-3">
              <Activity className="h-6 w-6 text-primary" />
              Centro de Mando de Ejecución
            </h2>
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
              {executionState === 'running' ? 'Live Execution' : executionState === 'completed' ? 'Success' : executionState === 'error' ? 'Halted' : 'Ready'}
            </Badge>
          </div>
        </div>
        <div className="flex gap-4 items-center">
          {executionState === 'running' && (
             <div className="text-right mr-4">
               <p className="text-xs text-muted-foreground uppercase font-bold tracking-wider mb-1">Predictive ETA</p>
               <p className="text-xl font-mono text-foreground">{Math.ceil(eta)} min</p>
             </div>
          )}
          
          <button 
            onClick={handleKillSwitch}
            disabled={executionState !== 'running'}
            className="px-4 py-2 rounded-lg font-bold border-2 border-destructive text-destructive hover:bg-destructive hover:text-destructive-foreground transition-all disabled:opacity-30 flex items-center gap-2"
          >
            <XCircle className="h-5 w-5" /> The Kill Switch
          </button>
          
          <button 
            onClick={startExecution}
            disabled={executionState === 'running' || executionState === 'completed'}
            className="px-6 py-2.5 rounded-lg font-bold bg-primary text-primary-foreground hover:bg-primary/90 transition-all shadow-lg disabled:opacity-50 flex items-center gap-2"
          >
            {executionState === 'running' ? <Loader2 className="h-5 w-5 animate-spin" /> : <Play className="h-5 w-5" />}
            {executionState === 'running' ? 'Ejecutando...' : executionState === 'idle' ? 'Iniciar Ejecución Autónoma' : 'Reintentar'}
          </button>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden p-6 gap-6 bg-muted/5">
        
        {/* Left Column: Causal Pipeline */}
        <div className="w-1/3 flex flex-col gap-4 overflow-y-auto">
          <h3 className="text-lg font-semibold text-foreground flex items-center gap-2">
            <GitPullRequest className="h-5 w-5" /> Causal Pipeline
          </h3>
          <div className="space-y-3">
            {plan?.tasks?.map((t: any, i: number) => (
              <div key={i} className={`p-4 rounded-xl border-2 transition-all ${executionState === 'running' && i === 0 ? 'border-primary bg-primary/5 shadow-md scale-[1.02]' : 'border-border/50 bg-card'}`}>
                <div className="flex justify-between items-center mb-2">
                  <Badge variant="secondary" className="text-xs">Task {i+1}</Badge>
                  {executionState === 'running' && i === 0 && <Loader2 className="h-4 w-4 animate-spin text-primary" />}
                </div>
                <h4 className="font-semibold text-sm mb-1">{t.title}</h4>
                <p className="text-xs text-muted-foreground">{t.objective}</p>
              </div>
            ))}
          </div>
        </div>

        {/* Right Column: Liability Logs */}
        <div className="flex-1 bg-slate-950 rounded-xl border border-border overflow-hidden flex flex-col shadow-inner">
          <div className="bg-slate-900 border-b border-slate-800 p-3 flex justify-between items-center">
             <h3 className="text-sm font-mono font-semibold text-slate-300 flex items-center gap-2">
               <Terminal className="h-4 w-4" /> Liability Logs (Immutable)
             </h3>
             {executionState === 'completed' && (
               <button className="text-xs text-primary hover:underline">Exportar PDF de Auditoría</button>
             )}
          </div>
          <div className="flex-1 p-4 overflow-y-auto font-mono text-xs text-slate-300 whitespace-pre-wrap leading-relaxed">
            {logs || (
              <div className="h-full flex items-center justify-center text-slate-600 italic">
                Esperando inicio de ejecución...
              </div>
            )}
          </div>
        </div>

      </div>

      {/* Action Gate Modal */}
      {executionState === 'action_gate' && actionGate && (
        <div className="absolute inset-0 bg-background/80 backdrop-blur-sm z-50 flex items-center justify-center p-6">
          <div className="bg-slate-950 border border-destructive rounded-xl shadow-2xl max-w-3xl w-full flex flex-col overflow-hidden animate-in zoom-in-95 duration-200">
            <div className="bg-destructive/20 border-b border-destructive p-4 flex items-center gap-3">
              <XCircle className="h-6 w-6 text-destructive" />
              <h2 className="text-xl font-bold text-destructive">ACTION GATE TRIGGERED</h2>
            </div>
            
            <div className="p-6 space-y-6 text-slate-300">
              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Diagnóstico del Doctor Agent</h3>
                <p className="bg-slate-900 p-3 rounded border border-slate-800 text-sm">{actionGate.diagnosis.diagnosis}</p>
              </div>

              {actionGate.diagnosis.required_invariant_breach && (
                <div>
                  <h3 className="text-sm font-semibold uppercase tracking-wider text-destructive mb-2">Invariante Comprometido</h3>
                  <p className="bg-destructive/10 p-3 rounded border border-destructive/30 text-sm text-red-200">{actionGate.diagnosis.required_invariant_breach}</p>
                </div>
              )}

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Cura Propuesta</h3>
                <p className="bg-slate-900 p-3 rounded border border-slate-800 text-sm">{actionGate.diagnosis.proposed_cure}</p>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-muted-foreground mb-2">Blast Radius (Archivos Afectados)</h3>
                <div className="flex gap-2 flex-wrap">
                  {actionGate.diagnosis.blast_radius?.map((file: string, idx: number) => (
                    <Badge key={idx} variant="outline" className="bg-slate-800 border-slate-700">{file}</Badge>
                  ))}
                </div>
              </div>

              <div>
                <h3 className="text-sm font-semibold uppercase tracking-wider text-orange-400 mb-2">Impacto Secundario (Riesgo)</h3>
                <p className="bg-orange-500/10 p-3 rounded border border-orange-500/30 text-sm text-orange-200">{actionGate.diagnosis.second_order_impact}</p>
              </div>
            </div>

            <div className="bg-slate-900 p-4 border-t border-slate-800 flex justify-end gap-4">
              <button 
                onClick={handleKillSwitch}
                className="px-4 py-2 rounded font-medium border border-slate-700 hover:bg-slate-800 transition-colors"
              >
                Denegar y Abortar
              </button>
              <button 
                onClick={handleAuthorizeActionGate}
                className="px-6 py-2 rounded font-bold bg-destructive text-destructive-foreground hover:bg-destructive/90 transition-colors shadow-lg"
              >
                Autorizar Excepción
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}