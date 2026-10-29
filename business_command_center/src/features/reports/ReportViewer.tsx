'use client';

import React, { useState, useEffect } from 'react';
import {
  FileText,
  Download,
  CheckCircle2,
  AlertCircle,
  Loader2,
  Sparkles,
  ArrowRight,
  Send,
  MessageSquare,
  BookOpen,
  Award,
  Layers,
  ChevronRight,
  Printer,
  FileQuestion
} from 'lucide-react';
import { getReportPayload, type ReportData, type ReportChapter } from './actions';
import { sendWarRoomTacticalMessage } from '@/app/actions/war_room';

interface ReportViewerProps {
  clientSlug: string;
  clientName: string;
}

export function ReportViewer({ clientSlug, clientName }: ReportViewerProps) {
  const [report, setReport] = useState<ReportData | null>(null);
  const [selectedChapterId, setSelectedChapterId] = useState<string>('executive');
  const [isLoading, setIsLoading] = useState(true);
  const [suggestionInput, setSuggestionInput] = useState('');
  const [isSubmittingSuggestion, setIsSubmittingSuggestion] = useState(false);
  const [feedbackMsg, setFeedbackMsg] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  useEffect(() => {
    const fetchReport = async () => {
      setIsLoading(true);
      const res = await getReportPayload(clientSlug);
      if (res.success && res.data) {
        setReport(res.data);
      }
      setIsLoading(false);
    };
    fetchReport();
  }, [clientSlug]);

  const handleSendSuggestion = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!suggestionInput.trim() || isSubmittingSuggestion) return;
    setIsSubmittingSuggestion(true);
    setFeedbackMsg(null);

    try {
      const prompt = `Adjustment for section [${selectedChapterId}]: ${suggestionInput.trim()}`;
      const res = await sendWarRoomTacticalMessage(clientSlug, prompt);
      if (res.success) {
        setFeedbackMsg({
          type: 'success',
          text: `Tactical adjustment registered and incorporated by War Room Architect.`,
        });
        setSuggestionInput('');
      } else {
        setFeedbackMsg({
          type: 'error',
          text: res.error || 'Error al registrar el ajuste.',
        });
      }
    } catch (err: any) {
      setFeedbackMsg({ type: 'error', text: err.message || 'Connection error' });
    } finally {
      setIsSubmittingSuggestion(false);
    }
  };

  const handlePrint = () => {
    window.print();
  };

  if (isLoading) {
    return (
      <div className="p-16 text-center space-y-3 bg-white border border-stone-200/80 rounded-2xl shadow-sm">
        <Loader2 className="h-8 w-8 animate-spin text-[#0072BC] mx-auto" />
        <div className="text-xs font-mono text-stone-500">Loading structured technical annex for {clientName}...</div>
      </div>
    );
  }

  if (!report) {
    return (
      <div className="p-12 text-center text-stone-500 text-xs font-mono bg-white border border-stone-200 rounded-2xl shadow-sm">
        No generated report found yet for {clientName}. Run the actuarial simulation to compile the Technical Annex.
      </div>
    );
  }

  const activeChapter = report.chapters.find((c) => c.id === selectedChapterId) || report.chapters[0];

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Top Header Card (Clean White Canvas) */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 p-6 bg-white border border-stone-200/80 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] print:hidden">
        <div className="space-y-1.5">
          <div className="flex items-center gap-2">
            <span className="text-[10px] font-mono uppercase px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0072BC] border border-blue-200 font-semibold">
              Online Technical Annex
            </span>
            <span className="text-[10px] font-mono text-emerald-700 flex items-center gap-1 font-semibold">
              <CheckCircle2 className="h-3 w-3" /> Certificado Soberano
            </span>
          </div>
          <h2 className="text-base font-bold text-[#1d1d1f] tracking-wide">
            {report.client_name} · Technical Assessment Report
          </h2>
          <div className="flex items-center gap-2 text-[11px] font-mono text-stone-500">
            <span>Marco: {report.regulatory_framework}</span>
            <span>•</span>
            <span>Jurisdiction: {report.jurisdiction}</span>
            <span>•</span>
            <span>Maturity Score: {report.global_score} ({report.global_band})</span>
          </div>
        </div>

        {/* Action Buttons: Download Word & Print PDF */}
        <div className="flex items-center gap-2.5 shrink-0">
          <button
            onClick={handlePrint}
            className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-stone-50 hover:bg-stone-100 text-stone-700 border border-stone-200 transition-all shadow-2xs"
            title="Imprimir o Guardar como PDF"
          >
            <Printer className="h-4 w-4 text-stone-600" />
            <span>Imprimir / PDF</span>
          </button>

          {report.has_docx ? (
            <a
              href={`/api/download?path=/home/jsanchhi/assessment_engine/working/out/simulations/${clientSlug}/Anexo_Tecnico_${clientSlug}.docx`}
              className="flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] active:bg-[#00609e] text-white transition-all shadow-sm shadow-[#0072BC]/20"
            >
              <Download className="h-4 w-4" /> Descargar Word Oficial (.docx)
            </a>
          ) : (
            <div
              className="flex items-center gap-1.5 px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-amber-50 text-amber-800 border border-amber-200 cursor-not-allowed"
              title="Word document not yet compiled. Click 'Run Simulation' to generate."
            >
              <FileQuestion className="h-4 w-4 text-amber-600" />
              <span>Word Report Pending Simulation</span>
            </div>
          )}
        </div>
      </div>

      {/* Main Document Body with Chapters Navigation */}
      <div className="grid grid-cols-1 lg:grid-cols-4 gap-6">
        {/* Left: Chapters Index (Print: hidden) */}
        <div className="space-y-1.5 bg-white border border-stone-200/80 p-3 rounded-2xl h-fit shadow-[0_2px_12px_rgba(0,0,0,0.03)] print:hidden">
          <div className="px-3 py-2 text-[10px] font-mono uppercase text-stone-400 font-bold tracking-wider">
            Chapter Index
          </div>

          <button
            onClick={() => { setSelectedChapterId('executive'); setFeedbackMsg(null); }}
            className={`w-full text-left p-3 rounded-xl text-xs font-semibold flex items-center justify-between transition-all ${
              selectedChapterId === 'executive'
                ? 'bg-blue-50/70 border border-blue-200 text-[#0072BC] shadow-2xs font-bold'
                : 'text-stone-700 hover:bg-stone-50 hover:text-[#1d1d1f]'
            }`}
          >
            <span className="flex items-center gap-2 truncate">
              <Sparkles className="h-3.5 w-3.5 shrink-0 text-[#0072BC]" /> Resumen Ejecutivo
            </span>
            <ChevronRight className="h-3.5 w-3.5 shrink-0 opacity-40" />
          </button>

          {report.chapters.map((ch) => {
            const isSelected = ch.id === selectedChapterId;
            return (
              <button
                key={ch.id}
                onClick={() => { setSelectedChapterId(ch.id); setFeedbackMsg(null); }}
                className={`w-full text-left p-3 rounded-xl text-xs font-semibold flex items-center justify-between transition-all ${
                  isSelected
                    ? 'bg-blue-50/70 border border-blue-200 text-[#0072BC] shadow-2xs font-bold'
                    : 'text-stone-700 hover:bg-stone-50 hover:text-[#1d1d1f]'
                }`}
              >
                <span className="truncate">{ch.title}</span>
                <ChevronRight className="h-3.5 w-3.5 shrink-0 opacity-40" />
              </button>
            );
          })}
        </div>

        {/* Right: Chapter Content Viewer & Interactive Feedback Card */}
        <div className="lg:col-span-3 space-y-6">
          {selectedChapterId === 'executive' ? (
            <div className="bg-white border border-stone-200/80 rounded-2xl p-8 space-y-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] print:border-none print:shadow-none print:p-0">
              <div className="space-y-2 border-b border-stone-100 pb-4">
                <span className="text-[10px] font-mono uppercase text-[#0072BC] font-bold tracking-wider">
                  Resumen Ejecutivo & Dictamen
                </span>
                <h3 className="text-base font-bold text-[#1d1d1f] leading-snug">{report.headline}</h3>
              </div>

              <div className="text-xs text-stone-700 leading-relaxed font-sans whitespace-pre-wrap space-y-4">
                <p>{report.summary_body}</p>
              </div>

              <div className="p-4 rounded-xl bg-[#fbfbfa] border border-stone-200/80 grid grid-cols-2 sm:grid-cols-3 gap-3 text-xs font-mono">
                <div>
                  <div className="text-[9px] text-stone-400 uppercase">Score Global</div>
                  <div className="text-sm font-bold text-emerald-700">{report.global_score}</div>
                </div>
                <div>
                  <div className="text-[9px] text-stone-400 uppercase">Nivel de Madurez</div>
                  <div className="text-sm font-bold text-[#1d1d1f]">{report.global_band}</div>
                </div>
                <div>
                  <div className="text-[9px] text-stone-400 uppercase">Regulation</div>
                  <div className="text-sm font-bold text-[#0072BC]">{report.regulatory_framework}</div>
                </div>
              </div>
            </div>
          ) : (
            <div className="bg-white border border-stone-200/80 rounded-2xl p-8 space-y-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] print:border-none print:shadow-none print:p-0">
              <div className="space-y-1.5 border-b border-stone-100 pb-4">
                <span className="text-[10px] font-mono uppercase text-[#0072BC] font-bold tracking-wider">
                  Technical Chapter
                </span>
                <h3 className="text-base font-bold text-[#1d1d1f] leading-snug">{activeChapter.title}</h3>
              </div>

              <div className="text-xs text-stone-700 leading-relaxed font-sans whitespace-pre-wrap space-y-4">
                <p>{activeChapter.content}</p>
              </div>

              {activeChapter.bullet_points && activeChapter.bullet_points.length > 0 && (
                <div className="space-y-2 pt-2">
                  <span className="text-[11px] font-semibold text-stone-800 uppercase tracking-wider block font-mono">
                    Hallazgos Principales:
                  </span>
                  <ul className="space-y-2 text-xs text-stone-700">
                    {activeChapter.bullet_points.map((pt, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className="text-[#0072BC] font-bold font-mono">✓</span>
                        <span>{pt}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}

          {/* Interactive Suggestion & HITL Review Box (Print: hidden) */}
          <div className="bg-white border border-stone-200/80 rounded-2xl p-6 space-y-4 shadow-[0_2px_12px_rgba(0,0,0,0.03)] print:hidden">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2.5">
                <div className="h-7 w-7 rounded-lg bg-amber-50 border border-amber-200 flex items-center justify-center text-amber-700">
                  <MessageSquare className="h-4 w-4" />
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[#1d1d1f] uppercase tracking-wider">
                    Suggest Live Adjustment for this Chapter
                  </h4>
                  <p className="text-[11px] text-stone-500">
                    Provide specific feedback or directives for the War Room Architect to recompute this section.
                  </p>
                </div>
              </div>
            </div>

            {feedbackMsg && (
              <div
                className={`p-3 rounded-xl text-xs flex items-center gap-2 font-mono ${
                  feedbackMsg.type === 'success'
                    ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                    : 'bg-rose-50 text-rose-800 border border-rose-200'
                }`}
              >
                {feedbackMsg.type === 'success' ? (
                  <CheckCircle2 className="h-4 w-4 text-emerald-600 shrink-0" />
                ) : (
                  <AlertCircle className="h-4 w-4 text-rose-600 shrink-0" />
                )}
                <span>{feedbackMsg.text}</span>
              </div>
            )}

            <form onSubmit={handleSendSuggestion} className="flex gap-2">
              <input
                type="text"
                value={suggestionInput}
                onChange={(e) => setSuggestionInput(e.target.value)}
                placeholder="e.g. Prioritize VMware migration to OpenShift in H1 roadmap..."
                disabled={isSubmittingSuggestion}
                className="flex-1 bg-[#fbfbfa] border border-stone-200 rounded-xl px-4 py-2.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] transition-all font-mono"
              />
              <button
                type="submit"
                disabled={isSubmittingSuggestion || !suggestionInput.trim()}
                className="px-5 py-2.5 rounded-xl text-xs font-semibold bg-amber-500 hover:bg-amber-400 active:bg-amber-600 text-slate-950 transition-all shadow-sm shadow-amber-500/20 disabled:opacity-50 flex items-center gap-2 shrink-0"
              >
                {isSubmittingSuggestion ? (
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                ) : (
                  <Send className="h-3.5 w-3.5" />
                )}
                Adjust Section
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
