'use client';

import React from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { 
  ClipboardList, 
  UploadCloud, 
  FileCheck, 
  Sparkles, 
  LogOut,
  HelpCircle
} from 'lucide-react';
import { createClient } from '@/lib/supabase/client';

export default function UserPortalLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const pathname = usePathname();
  const supabase = createClient();

  const handleSignOut = async () => {
    await supabase.auth.signOut();
    window.location.href = '/login';
  };

  const navItems = [
    { label: 'Mis Evaluaciones', href: '/portal', icon: ClipboardList },
    { label: 'Subir Evidencias', href: '/portal/upload', icon: UploadCloud },
    { label: 'Mis Entregables', href: '/portal/deliverables', icon: FileCheck },
    { label: 'Support & Docs', href: '/portal/help', icon: HelpCircle },
  ];

  return (
    <div className="flex h-screen bg-slate-950 text-slate-100 overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 border-r border-slate-800 flex flex-col justify-between">
        <div>
          <div className="h-16 flex items-center px-6 border-b border-slate-800 gap-3">
            <div className="h-9 w-9 rounded-lg bg-indigo-600/20 border border-indigo-500/30 flex items-center justify-center text-indigo-400">
              <Sparkles className="h-5 w-5" />
            </div>
            <div>
              <span className="font-bold text-sm tracking-wide text-white block">Assessment Engine</span>
              <span className="text-[10px] uppercase font-semibold tracking-wider text-indigo-400 block">Portal del Usuario</span>
            </div>
          </div>

          <nav className="p-4 space-y-1.5">
            {navItems.map((item) => {
              const Icon = item.icon;
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium transition-all ${
                    isActive
                      ? 'bg-indigo-600/15 text-indigo-400 border border-indigo-500/25'
                      : 'text-slate-400 hover:text-slate-200 hover:bg-slate-800/60'
                  }`}
                >
                  <Icon className="h-4 w-4" />
                  {item.label}
                </Link>
              );
            })}
          </nav>
        </div>

        <div className="p-4 border-t border-slate-800">
          <button
            onClick={handleSignOut}
            className="w-full flex items-center gap-3 px-3.5 py-2.5 rounded-lg text-xs font-medium text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <LogOut className="h-4 w-4" />
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <main className="flex-1 flex flex-col overflow-y-auto">
        <header className="h-16 bg-slate-900/60 backdrop-blur-md border-b border-slate-800 flex items-center justify-between px-8 sticky top-0 z-10">
          <div className="flex items-center gap-2">
            <span className="text-xs font-medium text-slate-300">Espacio de Trabajo Asignado</span>
          </div>
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className="font-mono bg-indigo-950/60 text-indigo-400 px-2 py-1 rounded border border-indigo-700/40">
              Evaluador Certificado
            </span>
          </div>
        </header>

        <div className="p-8">
          {children}
        </div>
      </main>
    </div>
  );
}
