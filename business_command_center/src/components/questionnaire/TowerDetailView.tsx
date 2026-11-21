'use client';

import React, { useState } from 'react';
import { 
  ArrowLeft, 
  ShieldCheck, 
  ChevronRight, 
  ChevronLeft, 
  CheckCircle2, 
  Award
} from 'lucide-react';
import { QuestionCard } from './QuestionCard';
import { TowerMetadata, QuestionnaireAnswers } from '@/app/actions/questionnaire';

interface TowerDetailViewProps {
  tower: TowerMetadata;
  answers: QuestionnaireAnswers;
  locale: 'es' | 'en';
  onBackToHub: () => void;
  onUpdateAnswer: (questionId: string, data: { score: number; comment?: string }) => void;
}

export function TowerDetailView({
  tower,
  answers,
  locale,
  onBackToHub,
  onUpdateAnswer,
}: TowerDetailViewProps) {
  const [selectedPillarId, setSelectedPillarId] = useState<string>(
    tower.pillars[0]?.pillarId || ''
  );

  const activePillarIndex = tower.pillars.findIndex(
    (p) => p.pillarId === selectedPillarId
  );
  const activePillar = tower.pillars[activePillarIndex] || tower.pillars[0];

  // Calculate Tower-level completion
  let towerAnsweredCount = 0;
  for (const pillar of tower.pillars) {
    for (const q of pillar.questions) {
      if (answers[q.questionId] && typeof answers[q.questionId].score === 'number') {
        towerAnsweredCount++;
      }
    }
  }

  const towerPct = tower.totalQuestions > 0 
    ? Math.round((towerAnsweredCount / tower.totalQuestions) * 100)
    : 0;

  return (
    <div className="space-y-6 font-sans">
      {/* Top Breadcrumb & Return to Hub */}
      <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 pb-4 border-b border-[#d2d2d7]/60">
        <button
          type="button"
          onClick={onBackToHub}
          className="inline-flex items-center gap-2 text-xs font-bold text-[#1d1d1f] hover:text-[#0071e3] px-4 py-2 rounded-2xl bg-white border border-[#d2d2d7]/70 hover:border-[#86868b] shadow-xs transition-all cursor-pointer"
        >
          <ArrowLeft className="h-4 w-4" />
          <span>Volver al Catálogo de Torres</span>
        </button>

        <div className="flex items-center gap-3">
          <div className="text-right">
            <span className="text-xs font-extrabold text-[#1d1d1f] block">
              Progreso: {towerAnsweredCount} / {tower.totalQuestions} ({towerPct}%)
            </span>
          </div>
          <div className="w-32 h-2.5 bg-[#f5f5f7] rounded-full overflow-hidden border border-[#d2d2d7]/60">
            <div
              className={`h-full transition-all duration-300 ${
                towerPct === 100 ? 'bg-[#34c759]' : 'bg-[#0071e3]'
              }`}
              style={{ width: `${towerPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Tower Identity Header - Clean PoCGPU Card */}
      <div className="bg-white border border-[#d2d2d7]/70 p-7 rounded-3xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] relative overflow-hidden">
        <div className="flex items-start gap-4">
          <div className="w-14 h-14 rounded-2xl bg-[#0071e3]/10 text-[#0071e3] font-black text-lg flex items-center justify-center shrink-0">
            {tower.towerId}
          </div>
          <div className="space-y-1.5 flex-1">
            <div className="flex items-center gap-2.5 flex-wrap">
              <h2 className="text-2xl font-black text-[#1d1d1f] tracking-tight">
                {tower.towerName}
              </h2>
              <span className="text-xs font-black text-[#0071e3] bg-[#0071e3]/10 px-3 py-0.5 rounded-full uppercase tracking-wider">
                {tower.canonicalCode}
              </span>
            </div>
            <p className="text-sm text-[#3a3a3c] leading-relaxed max-w-4xl">
              {tower.purpose}
            </p>
            <div className="flex items-center gap-4 pt-2 text-xs text-[#6e6e73] font-medium flex-wrap">
              <span className="flex items-center gap-1.5">
                <ShieldCheck className="h-4 w-4 text-[#0071e3]" />
                Estándar: <strong className="text-[#1d1d1f]">{tower.primaryStandard}</strong>
              </span>
              <span className="flex items-center gap-1.5">
                <Award className="h-4 w-4 text-[#0071e3]" />
                Gobernanza: <strong className="text-[#1d1d1f]">{tower.complianceFramework}</strong>
              </span>
            </div>
          </div>
        </div>
      </div>

      {/* Pillar Tabs Bar - Clean Stepper Style */}
      <div className="bg-[#f5f5f7] border border-[#d2d2d7]/60 p-1.5 rounded-2xl flex items-center gap-1.5 overflow-x-auto">
        {tower.pillars.map((pillar, idx) => {
          const isSelected = pillar.pillarId === selectedPillarId;

          // Count answers in this pillar
          let pAnswered = 0;
          for (const q of pillar.questions) {
            if (answers[q.questionId] && typeof answers[q.questionId].score === 'number') {
              pAnswered++;
            }
          }
          const isComplete = pAnswered === pillar.questions.length && pillar.questions.length > 0;

          return (
            <button
              key={pillar.pillarId}
              type="button"
              onClick={() => setSelectedPillarId(pillar.pillarId)}
              className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all shrink-0 flex items-center gap-2 cursor-pointer ${
                isSelected
                  ? 'bg-white text-[#1d1d1f] shadow-sm border border-[#d2d2d7]'
                  : 'text-[#6e6e73] hover:text-[#1d1d1f] hover:bg-white/60'
              }`}
            >
              <span className="text-[#0071e3] font-mono">P{idx + 1}</span>
              <span className="truncate max-w-[160px]">{pillar.pillarName}</span>
              <span
                className={`h-2 w-2 rounded-full ${
                  isComplete
                    ? 'bg-[#34c759]'
                    : pAnswered > 0
                    ? 'bg-amber-400'
                    : 'bg-[#d2d2d7]'
                }`}
              />
            </button>
          );
        })}
      </div>

      {/* Active Pillar Questions */}
      <div className="space-y-4">
        <div className="flex items-center justify-between px-1">
          <div className="flex items-center gap-2.5">
            <h3 className="text-base font-extrabold text-[#1d1d1f]">
              {activePillar.pillarName}
            </h3>
            <span className="text-xs font-bold text-[#0071e3] bg-[#0071e3]/10 px-2.5 py-0.5 rounded-full">
              Ponderación: {activePillar.weightPct}%
            </span>
          </div>
          <span className="text-xs font-bold text-[#6e6e73]">
            {activePillar.questions.length} preguntas en este pilar
          </span>
        </div>

        <div className="space-y-4">
          {activePillar.questions.map((q) => (
            <QuestionCard
              key={q.questionId}
              question={q}
              response={answers[q.questionId]}
              locale={locale}
              onUpdate={(data) => onUpdateAnswer(q.questionId, data)}
            />
          ))}
        </div>
      </div>

      {/* Pillar Navigation Footers */}
      <div className="flex items-center justify-between pt-6 border-t border-[#d2d2d7]/60">
        <button
          type="button"
          disabled={activePillarIndex <= 0}
          onClick={() => {
            if (activePillarIndex > 0) {
              setSelectedPillarId(tower.pillars[activePillarIndex - 1].pillarId);
            }
          }}
          className="inline-flex items-center gap-2 text-xs font-bold text-[#1d1d1f] px-5 py-2.5 rounded-2xl bg-white border border-[#d2d2d7]/70 hover:bg-[#f5f5f7] disabled:opacity-40 disabled:cursor-not-allowed transition-all cursor-pointer shadow-xs"
        >
          <ChevronLeft className="h-4 w-4" />
          Pilar Anterior
        </button>

        {activePillarIndex < tower.pillars.length - 1 ? (
          <button
            type="button"
            onClick={() => {
              setSelectedPillarId(tower.pillars[activePillarIndex + 1].pillarId);
            }}
            className="inline-flex items-center gap-2 text-xs font-bold text-white px-6 py-2.5 rounded-2xl bg-[#0071e3] hover:bg-[#0077ed] shadow-sm transition-all cursor-pointer"
          >
            Siguiente Pilar
            <ChevronRight className="h-4 w-4" />
          </button>
        ) : (
          <button
            type="button"
            onClick={onBackToHub}
            className="inline-flex items-center gap-2 text-xs font-bold text-emerald-800 bg-emerald-50 border border-emerald-200 px-6 py-2.5 rounded-2xl hover:bg-emerald-100 transition-all cursor-pointer"
          >
            <CheckCircle2 className="h-4 w-4" />
            Torre Finalizada · Volver al Catálogo
          </button>
        )}
      </div>
    </div>
  );
}
