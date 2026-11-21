'use client';

import React, { useEffect } from 'react';
import { AlertCircle, RotateCcw, Home } from 'lucide-react';

interface ErrorProps {
  error: Error & { digest?: string };
  reset: () => void;
}

/**
 * Root Error Boundary (Next.js 16 App Router).
 * Catches uncaught runtime exceptions and provides graceful degradation with state recovery.
 */
export default function ErrorBoundary({ error, reset }: ErrorProps) {
  useEffect(() => {
    console.error('[NEXTJS_APP_ERROR_BOUNDARY]', error);
  }, [error]);

  return (
    <div className="min-h-screen bg-[#f5f5f7] flex items-center justify-center p-4">
      <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-xl space-y-6 text-center">
        <div className="h-14 w-14 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto text-rose-600">
          <AlertCircle className="w-7 h-7" />
        </div>

        <div className="space-y-2">
          <h2 className="text-lg sm:text-xl font-bold text-[#1d1d1f] tracking-tight">
            Error en la Plataforma de Evaluación
          </h2>
          <p className="text-xs text-stone-600 leading-relaxed">
            Se ha producido una excepción imprevista durante la renderización o ejecución del motor actuarial.
          </p>
        </div>

        {error.message && (
          <div className="p-3.5 rounded-xl bg-[#0f172a] text-emerald-400 font-mono text-left text-xs whitespace-pre-wrap overflow-x-auto max-h-36 border border-slate-800">
            {error.message}
            {error.digest && (
              <div className="text-[10px] text-slate-500 mt-1">Digest: {error.digest}</div>
            )}
          </div>
        )}

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3 pt-2">
          <button
            onClick={() => reset()}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center justify-center gap-2 shadow-sm transition-all"
          >
            <RotateCcw className="w-3.5 h-3.5" />
            <span>Reintentar Operación</span>
          </button>

          <button
            onClick={() => {
              window.location.href = '/';
            }}
            className="w-full sm:w-auto px-5 py-2.5 rounded-xl text-xs font-semibold bg-stone-100 hover:bg-stone-200 text-stone-700 flex items-center justify-center gap-2 transition-colors"
          >
            <Home className="w-3.5 h-3.5" />
            <span>Volver al Inicio</span>
          </button>
        </div>
      </div>
    </div>
  );
}
