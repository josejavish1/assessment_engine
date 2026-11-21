'use client';

import React, { useState } from 'react';
import { MessageSquare, ChevronUp, CheckCircle2, Check } from 'lucide-react';
import { QuestionItem, SavedQuestionResponse } from '@/app/actions/questionnaire';

interface QuestionCardProps {
  question: QuestionItem;
  response?: SavedQuestionResponse;
  locale: 'es' | 'en';
  onUpdate: (data: { score: number; comment?: string }) => void;
}

export function QuestionCard({ question, response, locale, onUpdate }: QuestionCardProps) {
  const [isObservationOpen, setIsObservationOpen] = useState(Boolean(response?.comment));
  const currentScore = response?.score;
  const currentComment = response?.comment || '';

  const statement = locale === 'es' ? question.textEs : question.textEn;
  const isAnswered = typeof currentScore === 'number';

  const handleScoreChange = (score: number) => {
    onUpdate({ score, comment: currentComment });
  };

  const handleCommentChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    if (typeof currentScore === 'number') {
      onUpdate({ score: currentScore, comment: e.target.value });
    }
  };

  return (
    <div
      className={`p-7 rounded-3xl border transition-all duration-300 font-sans ${
        isAnswered
          ? 'bg-white border-[#0071e3]/40 shadow-[0_8px_24px_rgba(0,113,227,0.06)] ring-1 ring-[#0071e3]/20'
          : 'bg-white border-[#d2d2d7]/70 shadow-[0_2px_12px_rgba(0,0,0,0.03)]'
      }`}
    >
      {/* Top Header: KPI & Question ID */}
      <div className="flex items-start justify-between gap-4 mb-3">
        <div className="flex items-center gap-2.5 flex-wrap">
          <span className="text-xs font-black text-[#0071e3] bg-[#0071e3]/10 px-3 py-1 rounded-full uppercase tracking-wider font-mono">
            {question.questionId}
          </span>
          <span className="text-xs font-bold text-[#6e6e73]">
            {question.kpiName}
          </span>
        </div>

        {isAnswered && (
          <span className="inline-flex items-center gap-1.5 text-xs font-bold text-emerald-800 bg-emerald-50 px-3 py-1 rounded-full border border-emerald-200">
            <CheckCircle2 className="h-3.5 w-3.5 text-[#34c759]" />
            Nivel {currentScore}/5 Seleccionado
          </span>
        )}
      </div>

      {/* Main Question Statement */}
      <h3 className="text-base font-extrabold text-[#1d1d1f] leading-snug mb-5">
        {statement}
      </h3>

      {/* Specific Answer Options (Levels 1 to 5) */}
      <div className="space-y-2.5 mb-5">
        <span className="text-xs uppercase tracking-wider font-extrabold text-[#86868b] block mb-2">
          Seleccione el escenario operativo que describe su estado actual:
        </span>

        <div className="space-y-2.5">
          {question.options.map((opt) => {
            const isSelected = currentScore === opt.level;
            return (
              <div
                key={opt.level}
                onClick={() => handleScoreChange(opt.level)}
                className={`p-4 rounded-2xl border text-left transition-all duration-200 cursor-pointer flex items-start gap-3.5 ${
                  isSelected
                    ? 'border-[#0071e3] bg-[#0071e3]/5 shadow-[0_4px_16px_rgba(0,113,227,0.10)] ring-1 ring-[#0071e3]'
                    : 'border-[#d2d2d7]/70 bg-[#fbfbfd] hover:border-[#86868b] hover:bg-[#f5f5f7]'
                }`}
              >
                {/* Radio selection indicator matching PoCGPU */}
                <div className="pt-0.5 shrink-0">
                  <div
                    className={`w-6 h-6 rounded-xl border-2 flex items-center justify-center transition-all ${
                      isSelected
                        ? 'border-[#0071e3] bg-[#0071e3] text-white shadow-xs'
                        : 'border-[#d2d2d7] bg-white'
                    }`}
                  >
                    {isSelected && <Check className="w-3.5 h-3.5 stroke-[3.5]" />}
                  </div>
                </div>

                {/* Option Content */}
                <div className="space-y-1 flex-1">
                  <div className="flex items-center gap-2">
                    <span
                      className={`text-xs font-black ${
                        isSelected ? 'text-[#0071e3]' : 'text-[#1d1d1f]'
                      }`}
                    >
                      {opt.label}
                    </span>
                  </div>
                  <p className="text-sm text-[#3a3a3c] leading-relaxed font-normal">
                    {opt.description}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Decimal / Intermediate Calibrations */}
      <div className="flex items-center gap-2 py-3 border-t border-[#d2d2d7]/50 flex-wrap">
        <span className="text-xs text-[#6e6e73] font-bold">¿Su situación se ubica entre dos niveles?</span>
        {[1.5, 2.5, 3.5, 4.5].map((val) => {
          const isSelected = currentScore === val;
          return (
            <button
              key={val}
              type="button"
              onClick={() => handleScoreChange(val)}
              className={`px-3 py-1 rounded-xl text-xs font-bold font-mono transition-colors border cursor-pointer ${
                isSelected
                  ? 'bg-[#0071e3] text-white border-[#0071e3]'
                  : 'bg-[#f5f5f7] text-[#6e6e73] border-[#d2d2d7]/60 hover:text-[#1d1d1f] hover:bg-[#e8e8ed]'
              }`}
            >
              {val.toFixed(1)}
            </button>
          );
        })}
      </div>

      {/* Observation / Clarification Field */}
      <div className="pt-3 border-t border-[#d2d2d7]/50">
        {!isObservationOpen ? (
          <button
            type="button"
            onClick={() => setIsObservationOpen(true)}
            className="flex items-center gap-1.5 text-xs font-bold text-[#0071e3] hover:underline transition-colors py-1 cursor-pointer"
          >
            <MessageSquare className="h-4 w-4" />
            <span>+ Añadir aclaración u observación técnica</span>
          </button>
        ) : (
          <div className="space-y-2 mt-2">
            <div className="flex items-center justify-between">
              <label className="text-xs font-bold text-[#1d1d1f] flex items-center gap-1.5">
                <MessageSquare className="h-4 w-4 text-[#0071e3]" />
                Aclaración / Justificación Técnica de la Respuesta
              </label>
              <button
                type="button"
                onClick={() => setIsObservationOpen(false)}
                className="text-xs text-[#6e6e73] hover:text-[#1d1d1f] flex items-center gap-1 cursor-pointer font-semibold"
              >
                Plegar <ChevronUp className="h-3.5 w-3.5" />
              </button>
            </div>
            <textarea
              rows={2}
              value={currentComment}
              onChange={handleCommentChange}
              placeholder="Indique detalles de su infraestructura, acuerdos de mantenimiento o matices técnicos de esta nota..."
              className="w-full text-xs bg-[#fbfbfd] border border-[#d2d2d7] rounded-2xl p-3.5 text-[#1d1d1f] placeholder-[#86868b] focus:outline-none focus:ring-2 focus:ring-[#0071e3] focus:border-transparent transition-all resize-none font-normal"
            />
          </div>
        )}
      </div>
    </div>
  );
}
