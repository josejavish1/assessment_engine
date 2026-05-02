'use client';

import React, { useState } from 'react';
import { Target, ShieldAlert, GitPullRequest, Code2, ExternalLink, Bot, Check, X, ArrowLeft } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface ArtifactCanvasProps {
  plan: any;
  onApprove: (altIndex: number) => void;
  onReject: () => void;
}

export function ArtifactCanvas({ plan, onApprove, onReject }: ArtifactCanvasProps) {
  const [selectedAlt, setSelectedAlt] = useState(0);
  const [showTechnical, setShowTechnical] = useState(false);

  if (!plan) return null;

  if (plan.is_ambiguous) {
    return (
      <div className="flex-1 flex flex-col h-full bg-background items-center justify-center p-8 text-center animate-in fade-in duration-300">
          <Bot className="h-16 w-16 text-primary mb-6 animate-pulse" />
          <h2 className="text-2xl font-bold tracking-tight text-foreground mb-4">Aclaración Necesaria</h2>
          <p className="text-muted-foreground max-w-lg mb-8 text-lg">{plan.clarification_question}</p>
          <p className="text-sm text-muted-foreground bg-muted/30 p-4 rounded-lg border border-border/50">
            Responde a la pregunta en el chat lateral para que el Agente pueda generar el plan arquitectónico.
          </p>
      </div>
    );
  }

  const alternatives = plan.alternatives || [];
  const currentPlan = alternatives.length > 0 ? alternatives[selectedAlt] : plan;

  // Executive Decision Matrix View
  if (!showTechnical && alternatives.length > 0) {
    return (
      <div className="flex-1 flex flex-col h-full bg-background overflow-hidden animate-in fade-in duration-300">
        <div className="border-b border-border/50 bg-muted/10 p-8 flex items-center justify-between shrink-0">
          <div>
            <h2 className="text-3xl font-bold tracking-tight text-foreground mb-2">Matriz de Decisión Estratégica</h2>
            <p className="text-muted-foreground">Selecciona el enfoque arquitectónico que mejor se adapte a tus necesidades de negocio.</p>
          </div>
          <button onClick={onReject} className="px-6 py-2.5 rounded-lg font-medium border border-border hover:bg-muted text-muted-foreground transition-colors">
            Descartar Plan
          </button>
        </div>

        <div className="flex-1 p-8 overflow-y-auto bg-muted/5">
          <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-3 gap-6">
            {alternatives.map((alt: any, idx: number) => (
              <div key={idx} className={`flex flex-col bg-card rounded-2xl border ${idx === 1 ? 'border-primary ring-1 ring-primary/20 shadow-md' : 'border-border/60 shadow-sm'} overflow-hidden relative`}>
                {idx === 1 && <div className="absolute top-0 left-0 w-full h-1 bg-primary" />}
                
                <div className="p-6 border-b border-border/50">
                  <Badge variant="outline" className={`mb-3 ${alt.risk_level === 'high' ? 'text-destructive border-destructive/30 bg-destructive/10' : alt.risk_level === 'medium' ? 'text-amber-500 border-amber-500/30 bg-amber-500/10' : 'text-emerald-500 border-emerald-500/30 bg-emerald-500/10'}`}>
                    Riesgo: {alt.risk_level}
                  </Badge>
                  <h3 className="text-xl font-bold text-foreground mb-2">{alt.approach_name}</h3>
                  <div className="p-3 bg-muted/30 rounded-lg border border-border/50 mt-4">
                    <p className="text-sm font-medium text-foreground flex items-center gap-2"><Bot className="h-4 w-4 text-primary"/> Elígelo si...</p>
                    <p className="text-sm text-muted-foreground mt-1">{alt.recommendation_use_case}</p>
                  </div>
                </div>

                <div className="p-6 flex-1 space-y-6">
                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">👍 Ventajas (Pros)</h4>
                    <ul className="space-y-2">
                      {alt.pros?.map((pro: string, i: number) => (
                        <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                          <Check className="h-4 w-4 text-emerald-500 shrink-0 mt-0.5" />
                          <span>{pro}</span>
                        </li>
                      ))}
                    </ul>
                  </div>

                  <div>
                    <h4 className="text-sm font-semibold text-foreground mb-3 flex items-center gap-2">👎 Matriz de Riesgos Ejecutiva</h4>
                    <div className="space-y-4">
                      {alt.risks?.map((risk: any, i: number) => (
                        <div key={i} className="bg-muted/30 border border-border/50 rounded-lg p-3">
                          <p className="text-sm text-destructive font-medium flex items-start gap-2 mb-2">
                            <X className="h-4 w-4 shrink-0 mt-0.5" />
                            <span>{risk.structural_risk}</span>
                          </p>
                          <div className="pl-6 space-y-2">
                            <p className="text-xs text-foreground flex items-center gap-1.5"><ShieldAlert className="h-3 w-3 text-primary"/> <span className="font-medium text-muted-foreground">Mitigación:</span> {risk.mitigation_strategy}</p>
                            <p className="text-xs text-foreground flex items-center gap-1.5"><Target className="h-3 w-3 text-amber-500"/> <span className="font-medium text-muted-foreground">Impacto:</span> {risk.second_order_impact}</p>
                            
                            <div className="flex flex-wrap gap-2 mt-2 pt-2 border-t border-border/50">
                              <Badge variant="secondary" className="text-[10px] bg-background">
                                🚪 {risk.reversibility}
                              </Badge>
                              <Badge variant="secondary" className="text-[10px] bg-background">
                                ⏱️ Effort: {risk.mitigation_effort}
                              </Badge>
                              <Badge variant="secondary" className={`text-[10px] bg-background ${risk.confidence_score === 'High' ? 'text-emerald-500' : 'text-amber-500'}`}>
                                🧠 Confianza: {risk.confidence_score}
                              </Badge>
                            </div>
                          </div>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                <div className="p-6 bg-muted/10 border-t border-border/50 mt-auto">
                  <button 
                    onClick={() => {
                      setSelectedAlt(idx);
                      setShowTechnical(true);
                    }}
                    className={`w-full py-2.5 rounded-lg font-medium transition-colors ${idx === 1 ? 'bg-primary text-primary-foreground hover:bg-primary/90' : 'bg-muted text-foreground hover:bg-muted/80'}`}
                  >
                    Inspeccionar Arquitectura
                  </button>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // Technical View
  return (
    <div className="flex-1 flex flex-col h-full bg-background overflow-hidden animate-in slide-in-from-right-8 duration-300">
      <div className="border-b border-border/50 bg-muted/10 p-8 flex items-start justify-between shrink-0">
        <div>
          <button 
            onClick={() => setShowTechnical(false)}
            className="flex items-center gap-2 text-sm font-medium text-muted-foreground hover:text-foreground mb-4 transition-colors"
          >
            <ArrowLeft className="h-4 w-4" /> Volver a la Matriz de Decisión
          </button>
          <h2 className="text-3xl font-bold tracking-tight text-foreground mb-2">{currentPlan.approach_name}: {currentPlan.pr_title || currentPlan.request_title}</h2>
          <div className="flex items-center gap-3 text-sm text-muted-foreground">
            <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
              Technical Spec
            </Badge>
            <span className="flex items-center gap-1">
              <GitPullRequest className="h-4 w-4" /> {currentPlan.branch_name}
            </span>
            <span className="flex items-center gap-1">
              <ShieldAlert className="h-4 w-4" /> Risk: <span className="capitalize font-medium">{currentPlan.risk_level}</span>
            </span>
          </div>
        </div>
        <div className="flex gap-3 mt-8">
           <button onClick={onReject} className="px-6 py-2.5 rounded-lg font-medium border border-border hover:bg-muted text-muted-foreground transition-colors">
             Descartar Todo
           </button>
           <button onClick={() => onApprove(selectedAlt)} className="px-6 py-2.5 rounded-lg font-medium bg-primary text-primary-foreground hover:bg-primary/90 transition-colors shadow-sm">
             Aprobar y Ejecutar (Gate 1)
           </button>
        </div>
      </div>

      <div className="flex-1 p-8 overflow-y-auto pb-32">
        <div className="max-w-5xl mx-auto grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Columna Izquierda: Specs y Scope */}
          <div className="lg:col-span-1 space-y-8">
            <section>
              <h3 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-border/50 pb-2">
                <Target className="h-5 w-5 text-primary" /> Spec Mínima
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Problema</h4>
                  <p className="text-sm text-foreground leading-relaxed">{currentPlan.problem}</p>
                </div>
                <div>
                  <h4 className="text-sm font-medium text-muted-foreground mb-1">Valor Esperado</h4>
                  <p className="text-sm text-foreground leading-relaxed">{currentPlan.value_expected}</p>
                </div>
              </div>
            </section>

            <section>
              <h3 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-border/50 pb-2">
                <ShieldAlert className="h-5 w-5 text-destructive" /> Blast Radius & Scope
              </h3>
              <div className="space-y-4">
                <div>
                  <h4 className="text-xs font-bold text-emerald-500 mb-2 uppercase tracking-wider">In Scope</h4>
                  <ul className="space-y-2">
                    {currentPlan.in_scope?.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-foreground flex items-start gap-2">
                        <span className="text-emerald-500 mt-1">•</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-destructive mb-2 uppercase tracking-wider">Out of Scope</h4>
                  <ul className="space-y-2">
                    {currentPlan.out_of_scope?.map((item: string, i: number) => (
                      <li key={i} className="text-sm text-muted-foreground flex items-start gap-2">
                        <span className="text-destructive mt-1">×</span> {item}
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </section>
            
            <section>
              <h3 className="text-lg font-semibold flex items-center gap-2 mb-4 border-b border-border/50 pb-2">
                <ExternalLink className="h-5 w-5 text-amber-500" /> Source of Truth
              </h3>
              <ul className="space-y-2">
                {currentPlan.source_of_truth?.map((item: string, i: number) => (
                  <li key={i} className="text-xs font-mono text-muted-foreground bg-muted/30 p-2 rounded border border-border/50">
                    {item}
                  </li>
                ))}
              </ul>
            </section>
          </div>

          {/* Columna Derecha: Tareas / Reasoning Graph */}
          <div className="lg:col-span-2 space-y-6">
            <h3 className="text-xl font-semibold flex items-center gap-2 mb-6">
              <Code2 className="h-6 w-6 text-blue-500" /> Tareas Propuestas ({currentPlan.tasks?.length || 0})
            </h3>
            
            <div className="space-y-4">
              {currentPlan.tasks?.map((t: any, i: number) => (
                <div key={i} className="bg-card border border-border/50 rounded-xl p-5 shadow-sm">
                  <div className="flex items-center gap-3 mb-3">
                    <Badge className="bg-blue-500/10 text-blue-500 hover:bg-blue-500/20">{t.id}</Badge>
                    <h4 className="text-base font-semibold text-foreground">{t.title}</h4>
                  </div>
                  <p className="text-sm text-muted-foreground mb-4">{t.objective || t.description}</p>
                  
                  <div className="grid grid-cols-2 gap-4">
                    <div className="bg-muted/20 p-3 rounded-lg border border-border/50">
                      <span className="text-xs font-semibold text-muted-foreground uppercase mb-2 block">Validation</span>
                      <ul className="space-y-1.5">
                        {t.validation?.map((val: string, idx: number) => (
                          <li key={idx} className="text-xs text-foreground flex gap-2">
                            <span className="text-primary">-</span> {val}
                          </li>
                        ))}
                      </ul>
                    </div>
                    <div className="bg-muted/20 p-3 rounded-lg border border-border/50">
                      <span className="text-xs font-semibold text-muted-foreground uppercase mb-2 block">Invariants</span>
                      <ul className="space-y-1.5">
                        {t.invariants?.map((inv: string, idx: number) => (
                          <li key={idx} className="text-xs text-foreground flex gap-2">
                            <span className="text-destructive">-</span> {inv}
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}