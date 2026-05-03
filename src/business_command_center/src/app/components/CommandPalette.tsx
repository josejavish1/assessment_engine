'use client';

import React, { useEffect, useState, KeyboardEvent as ReactKeyboardEvent } from 'react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { Play, FileText, Settings, Bot, Loader2 } from 'lucide-react';
import { submitProductOwnerRequest, checkPlanStatus } from '../actions/mcp';

interface CommandPaletteProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  onPlanGenerated?: (plan: any, request: string) => void;
}

export default function CommandPalette({ open, setOpen, onPlanGenerated }: CommandPaletteProps) {
  const [inputValue, setInputValue] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      // Capturamos la combinación Ctrl+Shift+P o Cmd+Shift+P
      if (e.key.toLowerCase() === 'p' && e.shiftKey && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
      // También prevenimos Ctrl+P por si el usuario se equivoca de atajo
      else if (e.key.toLowerCase() === 'p' && (e.metaKey || e.ctrlKey) && !e.shiftKey) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, [setOpen]);

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
        try {
            const textContent = statusRes.result;
            if (textContent && textContent.startsWith("✅")) {
              const jsonPart = textContent.split('\n').slice(1).join('\n');
              planData = JSON.parse(jsonPart);
              if (onPlanGenerated) {
                onPlanGenerated(planData, requestText);
              }
              setInputValue('');
              setOpen(false);
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

  const handleKeyDown = async (e: ReactKeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter' && inputValue.trim() !== '') {
      e.preventDefault();
      setIsSubmitting(true);
      
      const requestText = inputValue;
      const response = await submitProductOwnerRequest(requestText);
      
      if (response.success && response.jobId) {
        pollJobStatus(response.jobId, requestText);
      } else {
        setIsSubmitting(false);
        console.error("Error:", response.error);
        alert("Error al contactar con el orquestador MCP. Revisa la consola.");
      }
    }
  };

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput 
        placeholder="Ej: Quiero endurecer la reconciliación automática de PRs..." 
        value={inputValue}
        onValueChange={setInputValue}
        onKeyDown={handleKeyDown}
        disabled={isSubmitting}
      />
      <CommandList>
        {isSubmitting ? (
          <div className="py-8 text-center text-sm flex flex-col items-center justify-center text-muted-foreground gap-3">
            <Loader2 className="h-6 w-6 animate-spin text-primary" />
            <p className="font-medium text-foreground">Conectando con Product Owner Orchestrator...</p>
            <p className="text-xs opacity-70 max-w-[250px]">La IA está analizando la petición y generando un plan estructural. Esto puede tardar unos segundos.</p>
          </div>
        ) : (
          <>
            <CommandEmpty>Presiona Enter para enviar a la IA: "{inputValue}"</CommandEmpty>
            <CommandGroup heading="Acciones Sugeridas">
              <CommandItem className="cursor-pointer" onSelect={() => setInputValue("Quiero que el informe global priorice los riesgos críticos")}>
                <Bot className="mr-2 h-4 w-4" />
                <span>Ejemplo: "Priorizar riesgos críticos en reporte global"</span>
              </CommandItem>
              <CommandItem className="cursor-pointer" onSelect={() => setInputValue("Quiero endurecer la reconciliación automática de PRs")}>
                <Bot className="mr-2 h-4 w-4" />
                <span>Ejemplo: "Endurecer reconciliación de PRs"</span>
              </CommandItem>
            </CommandGroup>
            <CommandSeparator />
            <CommandGroup heading="Navegación">
              <CommandItem className="cursor-pointer">
                <FileText className="mr-2 h-4 w-4" />
                <span>Ver Directorio de Blueprints</span>
              </CommandItem>
              <CommandItem className="cursor-pointer">
                <Settings className="mr-2 h-4 w-4" />
                <span>Configuración de Integraciones</span>
              </CommandItem>
            </CommandGroup>
          </>
        )}
      </CommandList>
    </CommandDialog>
  );
}
