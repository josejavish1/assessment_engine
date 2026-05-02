'use client';

import React from 'react';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Terminal, GitPullRequest, CheckCircle2, ShieldAlert, Target } from 'lucide-react';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
  agentic_state?: 'thinking' | 'coding' | 'testing' | 'done';
};

type AgentContextSheetProps = {
  task: Task | null;
  plan?: any;
  isOpen: boolean;
  onClose: () => void;
};

export default function AgentContextSheet({ task, plan, isOpen, onClose }: AgentContextSheetProps) {
  if (!task && !plan) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[540px] bg-card border-border text-foreground p-0 flex flex-col shadow-2xl">
        <SheetHeader className="p-6 border-b border-border/50 bg-muted/20">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-foreground text-lg tracking-tight">
              {plan ? "Plan del Orquestador" : task?.title}
            </SheetTitle>
            {task?.agentic_state === 'thinking' && (
              <Badge variant="outline" className="bg-primary/10 text-primary border-primary/20">
                Agent Thinking
              </Badge>
            )}
            {plan && (
              <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/20">
                Pending Approval
              </Badge>
            )}
          </div>
          <SheetDescription className="text-muted-foreground/80">
            {plan ? "Revisión de Spec Mínima y Tareas (Fase 2)" : "Inspector de contexto y auditoría de la IA."}
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="flex-1 p-6">
          {plan ? (
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <Target className="h-4 w-4 text-primary" /> Spec Mínima
                </h4>
                <div className="bg-muted/30 rounded-md p-4 text-sm text-muted-foreground border border-border/50 space-y-2">
                  <p><strong className="text-foreground">Problem:</strong> {plan.problem}</p>
                  <p><strong className="text-foreground">Value:</strong> {plan.value_expected}</p>
                  <p><strong className="text-foreground">Branch:</strong> <code className="bg-background px-1.5 py-0.5 rounded border border-border text-xs">{plan.branch_name}</code></p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <ShieldAlert className="h-4 w-4 text-destructive" /> Invariantes y Scope
                </h4>
                <div className="bg-muted/30 rounded-md p-4 text-xs font-mono text-muted-foreground border border-border/50">
                  <p className="text-emerald-500 mb-1"># IN SCOPE</p>
                  <ul className="list-disc pl-4 mb-3 space-y-1">
                    {plan.in_scope?.map((item: string, i: number) => <li key={i}>{item}</li>)}
                  </ul>
                  <p className="text-destructive mb-1"># OUT OF SCOPE</p>
                  <ul className="list-disc pl-4 space-y-1">
                    {plan.out_of_scope?.map((item: string, i: number) => <li key={i}>{item}</li>)}
                  </ul>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <GitPullRequest className="h-4 w-4 text-blue-500" /> Tareas Propuestas ({plan.tasks?.length})
                </h4>
                <div className="space-y-3">
                  {plan.tasks?.map((t: any, i: number) => (
                    <div key={i} className="bg-background rounded-md p-3 text-sm border border-border/50 shadow-sm">
                      <p className="font-medium text-foreground mb-1">{t.title}</p>
                      <p className="text-xs text-muted-foreground mb-2">{t.description}</p>
                      <div className="flex gap-2">
                        <Badge variant="secondary" className="text-[10px]">Source: {t.source_of_truth?.length} docs</Badge>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          ) : (
            <div className="space-y-6">
              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <Terminal className="h-4 w-4" /> Reasoning Trace
                </h4>
                <div className="bg-background rounded-md p-3 text-xs font-mono text-muted-foreground border border-border/50">
                  <p>&gt; Analizando petición...</p>
                  <p className="text-primary">&gt; Golden Path detectado: fastapi_endpoint</p>
                  <p>&gt; Generando código basado en plantilla...</p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <GitPullRequest className="h-4 w-4" /> Live Diff
                </h4>
                <div className="bg-background rounded-md p-3 text-xs font-mono border border-border/50">
                  <p className="text-destructive">- print("Procesando")</p>
                  <p className="text-emerald-500">+ logger.info("Procesando")</p>
                </div>
              </div>

              <div>
                <h4 className="text-sm font-semibold text-foreground mb-2 flex items-center gap-2">
                  <CheckCircle2 className="h-4 w-4" /> Quality Gates
                </h4>
                <ul className="space-y-2 text-sm text-muted-foreground">
                  <li className="flex items-center gap-2 text-emerald-500">
                    <CheckCircle2 className="h-4 w-4" /> Mypy Typecheck
                  </li>
                  <li className="flex items-center gap-2 text-amber-500">
                    <span className="relative flex h-2 w-2 mr-1">
                      <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                      <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                    </span>
                    Ruff Linter
                  </li>
                </ul>
              </div>
            </div>
          )}
        </ScrollArea>
        
        <div className="p-6 border-t border-border/50 bg-muted/20">
           <button className="w-full bg-primary hover:bg-primary/90 text-primary-foreground font-medium py-2.5 px-4 rounded-md transition-colors shadow-sm">
              {plan ? "Aprobar y Ejecutar (Gate 1)" : "Aprobar y Continuar"}
           </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}