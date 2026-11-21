'use client';

import React, { useState } from 'react';
import { Send } from 'lucide-react';

interface DossierNotesTabProps {
  initialNotes?: string[];
}

export function DossierNotesTab({ initialNotes = [] }: DossierNotesTabProps) {
  const [notes, setNotes] = useState<string[]>(initialNotes);
  const [newNoteInput, setNewNoteInput] = useState('');

  const handleAddNote = (e: React.FormEvent) => {
    e.preventDefault();
    if (!newNoteInput.trim()) return;
    setNotes((prev) => [
      `[${new Date().toLocaleDateString()} - Consultoría NTT DATA]: ${newNoteInput.trim()}`,
      ...prev,
    ]);
    setNewNoteInput('');
  };

  return (
    <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-6 max-w-4xl">
      <div className="border-b border-stone-100 pb-3">
        <h3 className="text-sm font-bold text-[#1d1d1f] uppercase tracking-wider font-mono">
          Bitácora de Consultoría NTT DATA
        </h3>
        <p className="text-xs text-stone-500">
          Notas y apreciaciones técnicas internas reservadas al equipo de evaluación.
        </p>
      </div>

      <form onSubmit={handleAddNote} className="space-y-3">
        <textarea
          rows={3}
          value={newNoteInput}
          onChange={(e) => setNewNoteInput(e.target.value)}
          placeholder="Escribe una nueva nota o apreciación técnica para este cliente..."
          className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl p-3 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
        />
        <div className="flex justify-end">
          <button
            type="submit"
            disabled={!newNoteInput.trim()}
            className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all disabled:opacity-50"
          >
            <Send className="w-3.5 h-3.5" />
            <span>Añadir Nota</span>
          </button>
        </div>
      </form>

      <div className="space-y-3 pt-2">
        {notes.map((note, idx) => (
          <div
            key={idx}
            className="p-3.5 rounded-xl bg-[#fbfbfa] border border-stone-200/80 text-xs text-stone-700 leading-relaxed font-mono"
          >
            {note}
          </div>
        ))}
      </div>
    </div>
  );
}
