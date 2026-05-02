'use client';

import React, { useEffect, useState } from 'react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';
import { Play, FileText, Settings, Bot } from 'lucide-react';

export default function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'j' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Escribe un comando o busca... (Lanzar Assessment, Configuración...)" />
      <CommandList>
        <CommandEmpty>No se encontraron resultados.</CommandEmpty>
        <CommandGroup heading="Acciones Principales">
          <CommandItem className="cursor-pointer">
            <Play className="mr-2 h-4 w-4" />
            <span>Lanzar Nuevo Assessment</span>
          </CommandItem>
          <CommandItem className="cursor-pointer">
            <Bot className="mr-2 h-4 w-4" />
            <span>Consultar Agente Arquitecto</span>
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Vistas">
          <CommandItem className="cursor-pointer">
            <FileText className="mr-2 h-4 w-4" />
            <span>Ver Directorio de Blueprints</span>
          </CommandItem>
          <CommandItem className="cursor-pointer">
            <Settings className="mr-2 h-4 w-4" />
            <span>Configuración de Integraciones</span>
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
