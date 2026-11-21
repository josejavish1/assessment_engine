'use client';

import React from 'react';

interface ScorePillsProps {
  currentScore?: number;
  onSelectScore: (score: number) => void;
}

const CMMI_LEVELS = [
  { level: 1, label: '1 - Inicial', desc: 'Prácticas ad-hoc no estandarizadas' },
  { level: 2, label: '2 - Gestionado', desc: 'Controles operativos y repetibles' },
  { level: 3, label: '3 - Definido', desc: 'Estándar formal en toda la organización' },
  { level: 4, label: '4 - Cuantitativo', desc: 'Medición con métricas y telemetría continua' },
  { level: 5, label: '5 - Optimizado', desc: 'Automatización y mejora predictiva' },
];

export function ScorePills({ currentScore, onSelectScore }: ScorePillsProps) {
  return (
    <div className="space-y-2">
      <div className="grid grid-cols-2 sm:grid-cols-5 gap-2">
        {CMMI_LEVELS.map((cmmi) => {
          const isSelected = currentScore === cmmi.level;
          return (
            <button
              key={cmmi.level}
              type="button"
              onClick={() => onSelectScore(cmmi.level)}
              className={`p-2.5 rounded-xl border text-left transition-all flex flex-col justify-between ${
                isSelected
                  ? 'bg-blue-600/20 border-blue-500 text-white shadow-lg shadow-blue-500/20 ring-1 ring-blue-500'
                  : 'bg-slate-900/60 border-slate-800 text-slate-300 hover:bg-slate-800 hover:border-slate-700'
              }`}
            >
              <div className="flex items-center justify-between w-full">
                <span className="font-semibold text-xs text-white">{cmmi.label}</span>
                {isSelected && (
                  <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
                )}
              </div>
              <span className="text-[10px] text-slate-400 mt-1 line-clamp-1">
                {cmmi.desc}
              </span>
            </button>
          );
        })}
      </div>

      {/* Decimal / Granular Shortcuts */}
      <div className="flex items-center gap-2 pt-1">
        <span className="text-[11px] text-slate-400 font-medium">Calificación Intermedia:</span>
        {[1.5, 2.5, 3.5, 4.5].map((val) => {
          const isSelected = currentScore === val;
          return (
            <button
              key={val}
              type="button"
              onClick={() => onSelectScore(val)}
              className={`px-2.5 py-1 rounded-md text-[11px] font-mono font-medium transition-colors border ${
                isSelected
                  ? 'bg-blue-600 text-white border-blue-400'
                  : 'bg-slate-900/80 text-slate-400 border-slate-800 hover:bg-slate-800 hover:text-slate-200'
              }`}
            >
              {val.toFixed(1)}
            </button>
          );
        })}
      </div>
    </div>
  );
}
