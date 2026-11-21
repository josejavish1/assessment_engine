'use client';

import React, { useState } from 'react';
import { TowerHubView } from './TowerHubView';
import { TowerDetailView } from './TowerDetailView';
import { 
  QuestionnaireBundle, 
  QuestionnaireAnswers,
  saveAssessmentResponses 
} from '@/app/actions/questionnaire';

interface AssessmentContainerProps {
  initialBundle: QuestionnaireBundle;
  initialAnswers: QuestionnaireAnswers;
  clientSlug?: string;
}

export function AssessmentContainer({
  initialBundle,
  initialAnswers,
  clientSlug = 'cliente_assessment',
}: AssessmentContainerProps) {
  const [activeTowerId, setActiveTowerId] = useState<string | null>(null);
  const [answers, setAnswers] = useState<QuestionnaireAnswers>(() => {
    if (typeof window !== 'undefined') {
      try {
        const cached = localStorage.getItem(`assessment_answers_${clientSlug}`);
        if (cached) {
          const parsed = JSON.parse(cached);
          if (Object.keys(parsed).length > 0) {
            return { ...initialAnswers, ...parsed };
          }
        }
      } catch {}
    }
    return initialAnswers;
  });
  const [locale, setLocale] = useState<'es' | 'en'>('es');
  const [isSaving, setIsSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  const [notification, setNotification] = useState<string | null>(null);

  const LOCAL_STORAGE_KEY = `assessment_answers_${clientSlug}`;

  // Auto-save to localStorage on updates
  const handleUpdateAnswer = (
    questionId: string,
    data: { score: number; comment?: string }
  ) => {
    setAnswers((prev) => {
      const next = {
        ...prev,
        [questionId]: {
          score: data.score,
          comment: data.comment,
          updatedAt: new Date().toISOString(),
        },
      };

      try {
        localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(next));
      } catch {
        // LocalStorage quota or error
      }
      return next;
    });
  };

  // 3. Save to server action
  const handleSaveToServer = async () => {
    setIsSaving(true);
    try {
      const res = await saveAssessmentResponses(clientSlug, answers);
      if (res.success) {
        setLastSaved(new Date());
        setNotification('✓ Borrador sincronizado exitosamente en el servidor.');
      } else {
        setNotification('⚠️ No se pudo guardar en el servidor. Guardado localmente.');
      }
    } catch {
      setNotification('⚠️ Error al comunicar con el servidor.');
    } finally {
      setIsSaving(false);
      setTimeout(() => setNotification(null), 4000);
    }
  };

  // 4. Download / Export canonical responses.txt directly
  const handleExportTxt = async () => {
    const res = await saveAssessmentResponses(clientSlug, answers);
    const content = res.formattedTxt || '';

    // Trigger direct browser download
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${clientSlug}_responses.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);

    setNotification(`✓ Archivo '${clientSlug}_responses.txt' generado y descargado.`);
    setTimeout(() => setNotification(null), 4000);
  };

  const selectedTower = initialBundle.towers.find((t) => t.towerId === activeTowerId);

  const lastSavedFormatted = lastSaved
    ? `Guardado a las ${lastSaved.toLocaleTimeString()}`
    : 'Borrador activo en almacenamiento local';

  return (
    <div className="relative">
      {/* Toast Notification */}
      {notification && (
        <div className="fixed bottom-6 right-6 z-50 bg-slate-900 border border-blue-500/50 text-white text-xs px-4 py-3 rounded-xl shadow-2xl flex items-center gap-2 animate-in fade-in slide-in-from-bottom-2">
          <span className="h-2 w-2 rounded-full bg-blue-400 animate-pulse" />
          <span>{notification}</span>
        </div>
      )}

      {selectedTower ? (
        <TowerDetailView
          tower={selectedTower}
          answers={answers}
          locale={locale}
          onBackToHub={() => setActiveTowerId(null)}
          onUpdateAnswer={handleUpdateAnswer}
        />
      ) : (
        <TowerHubView
          towers={initialBundle.towers}
          answers={answers}
          totalQuestions={initialBundle.totalQuestions}
          locale={locale}
          onSelectTower={(tid) => setActiveTowerId(tid)}
          onToggleLocale={() => setLocale((prev) => (prev === 'es' ? 'en' : 'es'))}
          onSaveToServer={handleSaveToServer}
          onExportTxt={handleExportTxt}
          isSaving={isSaving}
          lastSavedText={lastSavedFormatted}
        />
      )}
    </div>
  );
}
