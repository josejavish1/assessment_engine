import React from 'react';
import { Loader2 } from 'lucide-react';

/**
 * Root Loading Boundary (Next.js 16 App Router / React 19 Suspense).
 * Emitted instantly via streaming while the server pre-hydrates data.
 */
export default function Loading() {
  return (
    <div className="flex h-screen bg-[#f5f5f7] text-[#1d1d1f] font-sans antialiased overflow-hidden flex-col">
      {/* Header Skeleton */}
      <header className="h-16 border-b border-[#14233e] bg-[#0a1120] px-4 sm:px-6 lg:px-8 flex items-center justify-between shrink-0 select-none z-30 shadow-md">
        <div className="flex items-center gap-4">
          <div className="h-6 w-28 bg-slate-800 rounded animate-pulse" />
          <div className="h-5 w-36 bg-slate-800/60 rounded animate-pulse" />
        </div>
        <div className="flex items-center gap-3">
          <div className="h-8 w-24 bg-slate-800 rounded-xl animate-pulse" />
          <div className="h-8 w-8 bg-slate-800 rounded-full animate-pulse" />
        </div>
      </header>

      {/* Main Content Skeleton */}
      <main className="flex-1 overflow-auto p-4 sm:p-6 lg:p-8 max-w-7xl mx-auto w-full space-y-6">
        <div className="flex items-center justify-between">
          <div className="space-y-2">
            <div className="h-7 w-64 bg-stone-200 rounded-xl animate-pulse" />
            <div className="h-4 w-96 bg-stone-200/60 rounded-lg animate-pulse" />
          </div>
          <div className="h-10 w-36 bg-stone-200 rounded-xl animate-pulse" />
        </div>

        {/* Metric Cards Skeleton */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[...Array(4)].map((_, i) => (
            <div
              key={i}
              className="bg-white border border-stone-200/80 rounded-2xl p-4 shadow-xs space-y-3"
            >
              <div className="h-3 w-24 bg-stone-100 rounded animate-pulse" />
              <div className="h-6 w-32 bg-stone-200 rounded animate-pulse" />
              <div className="h-2.5 w-20 bg-stone-100 rounded animate-pulse" />
            </div>
          ))}
        </div>

        {/* Central Content Skeleton */}
        <div className="bg-white border border-stone-200/80 rounded-2xl p-8 shadow-xs min-h-[420px] flex flex-col items-center justify-center text-center space-y-3">
          <Loader2 className="w-8 h-8 animate-spin text-[#0072BC]" />
          <div className="text-xs font-mono text-stone-500">
            Sincronizando sesión y precargando expedientes actuariales...
          </div>
        </div>
      </main>
    </div>
  );
}
