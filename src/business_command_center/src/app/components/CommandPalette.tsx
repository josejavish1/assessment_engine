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
import { Play, FileText, Settings, Bot, Search } from 'lucide-react';

export default function CommandPalette() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      // Usar Ctrl+Shift+P (Estándar de VS Code / Paletas de Comandos modernas)
      // para evitar conflictos con navegadores.
      if (e.key === 'P' && e.shiftKey && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };
    document.addEventListener('keydown', down);
    
    // Escuchar un evento personalizado para abrir desde un botón
    const handleOpenCommandPalette = () => setOpen(true);
    document.addEventListener('openCommandPalette', handleOpenCommandPalette);

    return () => {
      document.removeEventListener('keydown', down);
      document.removeEventListener('openCommandPalette', handleOpenCommandPalette);
    };
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
