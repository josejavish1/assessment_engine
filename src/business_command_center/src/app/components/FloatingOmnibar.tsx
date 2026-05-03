'use client';

import React, { useState, KeyboardEvent as ReactKeyboardEvent, useEffect } from 'react';
import { Bot, Loader2, Send } from 'lucide-react';
import { submitProductOwnerRequest, checkPlanStatus } from '../actions/mcp';
import { readLiveTrace } from '../actions/trace';

interface FloatingOmnibarProps {
  onPlanGenerated: (plan: any, request: string, requestDir: string) => void;
  isSubmitting: boolean;
  setIsSubmitting: (val: boolean) => void;
}

export function FloatingOmnibar({ onPlanGenerated, isSubmitting, setIsSubmitting }: FloatingOmnibarProps) {
  const [inputValue, setInputValue] = useState('');
  const [traceMsg, setTraceMsg] = useState('Analizando contexto y diseñando el plan...');

  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (isSubmitting) {
      interval = setInterval(async () => {
        const msg = await readLiveTrace();
        setTraceMsg(msg);
      }, 800);
    }
    return () => clearInterval(interval);
  }, [isSubmitting]);

  const pollJobStatus = async (jobId: string, requestText: string) => {
    const pollInterval = setInterval(async () => {
      const statusRes = await checkPlanStatus(jobId);
      if (!statusRes.success || statusRes.status === "error") {
        clearInterval(pollInterval);
        setIsSubmitting(false);
        console.error("Job error:", statusRes.error || statusRes.result);
        alert("El orquestador devolvió un error. Revisa la consola.");
        return;
      }
      if (statusRes.status === "completed") {
        clearInterval(pollInterval);
        setIsSubmitting(false);
        
        let planData = null;
        let requestDir = "";
        try {
            const textContent = statusRes.result;
            if (textContent && textContent.startsWith("✅")) {
              const lines = textContent.split('\n');
              const requestDirLine = lines.find((l: string) => l.startsWith('REQUEST_DIR='));
              if (requestDirLine) {
                requestDir = requestDirLine.replace('REQUEST_DIR=', '').trim();
              }
              const jsonPart = lines.slice(requestDirLine ? 2 : 1).join('\n');
              planData = JSON.parse(jsonPart);
              onPlanGenerated(planData, requestText, requestDir);
              setInputValue('');
            } else {
              console.error("Orchestrator returned an error:", textContent);
              alert("El orquestador devolvió un error. Revisa la consola.");
            }
        } catch (e) {
            console.error("Could not parse plan json:", e);
            alert("Error al parsear el plan generado.");
        }
      }
    }, 2000);
  };

  const handleSubmit = async () => {
    if (inputValue.trim() === '') return;
    
    const requestText = inputValue;
    setIsSubmitting(true);
    setTraceMsg('Iniciando orquestador asíncrono...');
    const response = await submitProductOwnerRequest(requestText);
    
    if (response.success && response.jobId) {
      pollJobStatus(response.jobId, requestText);
    } else {
      setIsSubmitting(false);
      console.error("Error:", response.error);
      alert("Error al contactar con el orquestador MCP. Revisa la consola.");
    }
  };

  const handleKeyDown = (e: ReactKeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="fixed bottom-8 left-1/2 -translate-x-1/2 w-full max-w-2xl px-4 z-50">
      {isSubmitting && (
        <div className="absolute -top-10 left-1/2 -translate-x-1/2 bg-background/90 backdrop-blur border border-border shadow-sm px-4 py-1.5 rounded-full text-xs font-mono text-muted-foreground flex items-center gap-2 animate-in slide-in-from-bottom-2 whitespace-nowrap max-w-full overflow-hidden text-ellipsis">
          <Loader2 className="h-3 w-3 animate-spin text-primary shrink-0" />
          <span className="truncate">{traceMsg}</span>
        </div>
      )}
      <div className="bg-popover border border-border shadow-2xl rounded-2xl flex items-center p-2 focus-within:ring-2 focus-within:ring-primary/50 transition-all relative">
        <div className="pl-3 pr-2 text-muted-foreground">
          {isSubmitting ? <Loader2 className="h-5 w-5 animate-spin text-primary" /> : <Bot className="h-5 w-5" />}
        </div>
        <input
          type="text"
          className="flex-1 bg-transparent border-none outline-none text-foreground placeholder:text-muted-foreground px-2 py-3"
          placeholder="¿Qué quieres construir o mejorar hoy? (ej. Endurecer reconciliación de PRs)"
          value={inputValue}
          onChange={(e) => setInputValue(e.target.value)}
          onKeyDown={handleKeyDown}
          disabled={isSubmitting}
          autoFocus
        />
        <button 
          onClick={handleSubmit}
          disabled={isSubmitting || inputValue.trim() === ''}
          className="bg-primary text-primary-foreground p-3 rounded-xl hover:bg-primary/90 disabled:opacity-50 transition-colors ml-2"
        >
          <Send className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}