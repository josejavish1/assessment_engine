'use client';

import React from 'react';
import { 
  Clock, 
  Download, 
  Save, 
  Globe, 
  ArrowRight, 
  Check
} from 'lucide-react';
import { TowerMetadata, QuestionnaireAnswers } from '@/app/actions/questionnaire';

interface TowerHubViewProps {
  towers: TowerMetadata[];
  answers: QuestionnaireAnswers;
  totalQuestions: number;
  locale: 'es' | 'en';
  onSelectTower: (towerId: string) => void;
  onToggleLocale: () => void;
  onSaveToServer: () => void;
  onExportTxt: () => void;
  isSaving: boolean;
  lastSavedText: string;
}

export function TowerHubView({
  towers,
  answers,
  totalQuestions,
  locale,
  onSelectTower,
  onToggleLocale,
  onSaveToServer,
  onExportTxt,
  isSaving,
  lastSavedText,
}: TowerHubViewProps) {
  // Global answered counter
  let totalAnswered = 0;
  for (const tower of towers) {
    for (const pillar of tower.pillars) {
      for (const q of pillar.questions) {
        if (answers[q.questionId] && typeof answers[q.questionId].score === 'number') {
          totalAnswered++;
        }
      }
    }
  }

  const globalPct = totalQuestions > 0 ? Math.round((totalAnswered / totalQuestions) * 100) : 0;

  return (
    <div className="space-y-8 font-sans">
      {/* Executive Hero Banner - Clean Apple/PoCGPU Light Theme */}
      <div className="bg-white border border-[#d2d2d7]/70 p-8 rounded-3xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] relative overflow-hidden">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
          <div className="space-y-2">
            <div className="flex items-center gap-2.5">
              <span className="text-xs font-black text-[#0071e3] bg-[#0071e3]/10 px-3 py-1 rounded-full uppercase tracking-wider">
                10 Dominios Tecnológicos
              </span>
              <span className="text-xs font-bold text-[#86868b]">
                CMMI v2.0 & Open FAIR™ Methodology
              </span>
            </div>
            <h1 className="text-3xl lg:text-4xl font-extrabold tracking-tight text-[#1d1d1f]">
              Cuestionario de Evaluación Técnica
            </h1>
            <p className="text-sm text-[#6e6e73] font-medium max-w-2xl leading-relaxed">
              Seleccione cada torre de infraestructura para responder o calibrar las preguntas técnicas. Cada respuesta se refleja automáticamente en la postura diagnóstica.
            </p>
          </div>

          {/* Action Tools */}
          <div className="flex items-center gap-3 flex-wrap">
            <button
              type="button"
              onClick={onToggleLocale}
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-2xl text-xs font-bold text-[#1d1d1f] bg-[#f5f5f7] hover:bg-[#e8e8ed] border border-[#d2d2d7]/60 transition-colors cursor-pointer"
            >
              <Globe className="h-4 w-4 text-[#0071e3]" />
              <span>Idioma: <strong className="text-[#1d1d1f] uppercase">{locale}</strong></span>
            </button>

            <button
              type="button"
              onClick={onSaveToServer}
              disabled={isSaving}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-2xl text-xs font-bold text-white bg-[#0071e3] hover:bg-[#0077ed] shadow-sm transition-all disabled:opacity-50 cursor-pointer"
            >
              <Save className="h-4 w-4" />
              <span>{isSaving ? 'Guardando...' : 'Guardar Borrador'}</span>
            </button>

            <button
              type="button"
              onClick={onExportTxt}
              className="flex items-center gap-1.5 px-4 py-2.5 rounded-2xl text-xs font-bold text-emerald-800 bg-emerald-50 hover:bg-emerald-100 border border-emerald-200 transition-all cursor-pointer"
            >
              <Download className="h-4 w-4" />
              <span>Exportar responses.txt</span>
            </button>
          </div>
        </div>

        {/* Global Progress Gauge */}
        <div className="mt-8 pt-6 border-t border-[#d2d2d7]/50 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs font-bold text-[#6e6e73]">Progreso Consolidado:</span>
              <strong className="text-sm font-extrabold text-[#1d1d1f]">
                {totalAnswered} / {totalQuestions} preguntas ({globalPct}%)
              </strong>
            </div>
            {lastSavedText && (
              <span className="text-[11px] text-[#86868b] block font-mono">
                {lastSavedText}
              </span>
            )}
          </div>

          <div className="flex-1 max-w-md h-3 bg-[#f5f5f7] rounded-full overflow-hidden border border-[#d2d2d7]/60 p-0.5">
            <div
              className={`h-full rounded-full transition-all duration-500 ${
                globalPct === 100
                  ? 'bg-[#34c759]'
                  : 'bg-[#0071e3]'
              }`}
              style={{ width: `${globalPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Tower Grid (10 Cards) - Styled after PoCGPU renderCard */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-2 gap-6">
        {towers.map((tower) => {
          let towerAnswered = 0;
          for (const pillar of tower.pillars) {
            for (const q of pillar.questions) {
              if (answers[q.questionId] && typeof answers[q.questionId].score === 'number') {
                towerAnswered++;
              }
            }
          }

          const pct = tower.totalQuestions > 0 ? Math.round((towerAnswered / tower.totalQuestions) * 100) : 0;
          const isComplete = pct === 100;
          const isInProgress = pct > 0 && pct < 100;

          return (
            <div
              key={tower.towerId}
              onClick={() => onSelectTower(tower.towerId)}
              className="group bg-white border border-[#d2d2d7]/70 rounded-3xl p-7 shadow-[0_2px_12px_rgba(0,0,0,0.03)] hover:border-[#86868b] hover:shadow-[0_8px_24px_rgba(0,0,0,0.06)] hover:-translate-y-1 transition-all duration-300 cursor-pointer flex flex-col justify-between"
            >
              <div className="space-y-4">
                {/* Card Top: Icon + Badge + Check */}
                <div className="flex items-center justify-between">
                  <div className="w-12 h-12 rounded-2xl bg-[#0071e3]/10 text-[#0071e3] font-black text-base flex items-center justify-center shrink-0">
                    {tower.towerId}
                  </div>

                  <div className="flex items-center gap-2.5 shrink-0">
                    <span className="text-xs font-black text-[#0071e3] bg-[#0071e3]/10 px-3 py-1 rounded-full uppercase tracking-wider">
                      {tower.canonicalCode}
                    </span>

                    {isComplete ? (
                      <div className="w-7 h-7 rounded-xl border-2 border-[#34c759] bg-[#34c759] text-white flex items-center justify-center shadow-xs">
                        <Check className="w-4 h-4 stroke-[3.5]" />
                      </div>
                    ) : isInProgress ? (
                      <span className="text-[11px] font-bold text-amber-800 bg-amber-50 border border-amber-200 px-2.5 py-0.5 rounded-full flex items-center gap-1">
                        <Clock className="w-3 h-3" />
                        {pct}%
                      </span>
                    ) : (
                      <div className="w-7 h-7 rounded-xl border-2 border-[#d2d2d7] bg-[#fbfbfd]" />
                    )}
                  </div>
                </div>

                {/* Card Titles */}
                <div>
                  <h2 className="text-xl font-black text-[#1d1d1f] tracking-tight group-hover:text-[#0071e3] transition-colors leading-snug">
                    {tower.towerName}
                  </h2>
                  <div className="text-xs font-bold text-[#0071e3] mt-1">
                    {tower.primaryStandard}
                  </div>
                  <p className="text-sm text-[#3a3a3c] mt-2.5 leading-relaxed font-normal line-clamp-2">
                    {tower.purpose}
                  </p>
                </div>
              </div>

              {/* Progress & Bottom Action Bar */}
              <div className="pt-5 mt-6 border-t border-[#d2d2d7]/50 space-y-2.5">
                <div className="flex items-center justify-between text-xs font-semibold">
                  <span className="text-[#6e6e73]">
                    {towerAnswered} de {tower.totalQuestions} contestadas
                  </span>
                  <span className="font-extrabold text-[#1d1d1f]">
                    {pct}%
                  </span>
                </div>

                <div className="w-full h-2 bg-[#f5f5f7] rounded-full overflow-hidden border border-[#d2d2d7]/60">
                  <div
                    className={`h-full transition-all duration-300 ${
                      isComplete ? 'bg-[#34c759]' : 'bg-[#0071e3]'
                    }`}
                    style={{ width: `${pct}%` }}
                  />
                </div>

                <div className="flex items-center justify-end pt-1">
                  <span className="inline-flex items-center gap-1.5 text-xs font-bold text-[#0071e3] group-hover:translate-x-1 transition-transform">
                    <span>Evaluar Torre</span>
                    <ArrowRight className="h-4 w-4" />
                  </span>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
