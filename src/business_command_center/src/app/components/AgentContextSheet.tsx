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
import { Terminal, GitPullRequest, CheckCircle2 } from 'lucide-react';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
  agentic_state?: 'thinking' | 'coding' | 'testing' | 'done';
};

type AgentContextSheetProps = {
  task: Task | null;
  isOpen: boolean;
  onClose: () => void;
};

export default function AgentContextSheet({ task, isOpen, onClose }: AgentContextSheetProps) {
  if (!task) return null;

  return (
    <Sheet open={isOpen} onOpenChange={onClose}>
      <SheetContent className="w-[400px] sm:w-[540px] bg-slate-900 border-slate-800 text-slate-100 p-0 flex flex-col">
        <SheetHeader className="p-6 border-b border-slate-800">
          <div className="flex items-center justify-between">
            <SheetTitle className="text-slate-100">{task.title}</SheetTitle>
            {task.agentic_state === 'thinking' && (
              <Badge variant="outline" className="bg-blue-500/10 text-blue-400 border-blue-500/20">
                Agent Thinking
              </Badge>
            )}
          </div>
          <SheetDescription className="text-slate-400">
            Inspector de contexto y auditoría de la IA.
          </SheetDescription>
        </SheetHeader>

        <ScrollArea className="flex-1 p-6">
          <div className="space-y-6">
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                <Terminal className="h-4 w-4" /> Reasoning Trace
              </h4>
              <div className="bg-slate-950 rounded-md p-3 text-xs font-mono text-slate-400 border border-slate-800">
                <p>&gt; Analizando petición...</p>
                <p className="text-emerald-400">&gt; Golden Path detectado: fastapi_endpoint</p>
                <p>&gt; Generando código basado en plantilla...</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                <GitPullRequest className="h-4 w-4" /> Live Diff
              </h4>
              <div className="bg-slate-950 rounded-md p-3 text-xs font-mono border border-slate-800">
                <p className="text-red-400">- print("Procesando")</p>
                <p className="text-emerald-400">+ logger.info("Procesando")</p>
              </div>
            </div>

            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2 flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4" /> Quality Gates
              </h4>
              <ul className="space-y-2 text-sm">
                <li className="flex items-center gap-2 text-emerald-400">
                  <CheckCircle2 className="h-4 w-4" /> Mypy Typecheck
                </li>
                <li className="flex items-center gap-2 text-amber-400">
                  <span className="relative flex h-2 w-2 mr-1">
                    <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
                    <span className="relative inline-flex rounded-full h-2 w-2 bg-amber-500"></span>
                  </span>
                  Ruff Linter
                </li>
              </ul>
            </div>
          </div>
        </ScrollArea>
        
        <div className="p-6 border-t border-slate-800 bg-slate-900/50">
           <button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition-colors">
              Aprobar y Continuar
           </button>
        </div>
      </SheetContent>
    </Sheet>
  );
}