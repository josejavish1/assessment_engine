'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  Table as TableIcon,
  LayoutGrid,
  ArrowRight,
} from 'lucide-react';
import type { AccountAssessment } from './intelligence';

interface DossierAssessmentsTabProps {
  clientAssessments: AccountAssessment[];
  onOpenWorkspace: (clientSlug: string) => void;
}

export function DossierAssessmentsTab({
  clientAssessments,
  onOpenWorkspace,
}: DossierAssessmentsTabProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState<'all' | 'in_progress' | 'completed'>('all');
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');

  const filteredAssessments = useMemo(() => {
    return clientAssessments.filter((a) => {
      const matchesStatus =
        statusFilter === 'all' ||
        (statusFilter === 'in_progress' && a.status === 'En Curso') ||
        (statusFilter === 'completed' && a.status === 'Finalizado');
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        a.title.toLowerCase().includes(term) ||
        a.code.toLowerCase().includes(term) ||
        a.scopeTorres.toLowerCase().includes(term);
      return matchesStatus && matchesSearch;
    });
  }, [clientAssessments, statusFilter, searchTerm]);

  return (
    <div className="space-y-4">
      <div className="bg-white border border-stone-200/80 p-3 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col md:flex-row items-center justify-between gap-3">
        <div className="relative flex-1 w-full">
          <Search className="h-4 w-4 text-stone-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar assessment o expediente de esta cuenta..."
            className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
          />
        </div>

        <div className="flex items-center gap-2 w-full md:w-auto">
          <div className="flex items-center p-1 bg-stone-100 rounded-xl text-xs border border-stone-200">
            <button
              onClick={() => setStatusFilter('all')}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                statusFilter === 'all'
                  ? 'bg-white text-[#0072BC] font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              Todas ({clientAssessments.length})
            </button>
            <button
              onClick={() => setStatusFilter('in_progress')}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                statusFilter === 'in_progress'
                  ? 'bg-white text-[#0072BC] font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              En Curso ({clientAssessments.filter((a) => a.status === 'En Curso').length})
            </button>
            <button
              onClick={() => setStatusFilter('completed')}
              className={`px-3 py-1.5 rounded-lg text-xs transition-all ${
                statusFilter === 'completed'
                  ? 'bg-white text-[#0072BC] font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              Finalizadas ({clientAssessments.filter((a) => a.status === 'Finalizado').length})
            </button>
          </div>

          <div className="flex items-center p-1 bg-stone-100 rounded-xl text-xs border border-stone-200">
            <button
              onClick={() => setViewMode('table')}
              className={`px-2.5 py-1.5 rounded-lg flex items-center gap-1 ${
                viewMode === 'table' ? 'bg-white text-[#0072BC] font-bold shadow-2xs' : 'text-stone-500'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-2.5 py-1.5 rounded-lg flex items-center gap-1 ${
                viewMode === 'cards' ? 'bg-white text-[#0072BC] font-bold shadow-2xs' : 'text-stone-500'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
            </button>
          </div>
        </div>
      </div>

      {viewMode === 'table' && (
        <div className="bg-white border border-stone-200/80 rounded-2xl overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#fbfbfa] border-b border-stone-200 text-[11px] font-mono uppercase tracking-wider text-stone-500 font-bold">
                <th className="py-3.5 px-6">Assessment / Informe</th>
                <th className="py-3.5 px-6">Ámbito / Torre</th>
                <th className="py-3.5 px-6">Presupuesto / FAIR ALE</th>
                <th className="py-3.5 px-6">Marco Regulatorio</th>
                <th className="py-3.5 px-6">Estado Pipeline</th>
                <th className="py-3.5 px-6 text-right">Acción</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 text-xs">
              {filteredAssessments.map((item) => (
                <tr key={item.id} className="hover:bg-blue-50/30 transition-colors group">
                  <td className="py-4 px-6 max-w-sm">
                    <div className="font-bold text-sm text-[#1d1d1f] group-hover:text-[#0072BC] transition-colors">
                      {item.title}
                    </div>
                    <div className="text-stone-400 font-mono text-[11px] mt-0.5">
                      ID: {item.code} · Actualizado: {item.updatedAt}
                    </div>
                  </td>

                  <td className="py-4 px-6">
                    <span className="px-2.5 py-1 rounded-lg text-xs bg-stone-100 text-stone-700 font-mono">
                      {item.scopeTorres}
                    </span>
                  </td>

                  <td className="py-4 px-6 font-mono font-bold text-xs text-[#0072BC]">
                    {item.presupuestoFairAle}
                  </td>

                  <td className="py-4 px-6">
                    <span className="text-xs font-semibold text-stone-700">
                      {item.standard}
                    </span>
                  </td>

                  <td className="py-4 px-6">
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-semibold font-mono ${
                        item.status === 'Finalizado'
                          ? 'bg-emerald-50 text-emerald-800 border border-emerald-200'
                          : 'bg-blue-50 text-[#0072BC] border border-blue-200'
                      }`}
                    >
                      {item.status}
                    </span>
                  </td>

                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => onOpenWorkspace(item.clientSlug)}
                      className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 ml-auto shadow-sm transition-all"
                    >
                      <span>Abrir</span>
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {filteredAssessments.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-stone-200/80 rounded-2xl p-5 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-3"
            >
              <div className="flex items-start justify-between gap-3">
                <div>
                  <h4 className="font-bold text-sm text-[#1d1d1f]">{item.title}</h4>
                  <p className="text-stone-400 font-mono text-[11px]">ID: {item.code}</p>
                </div>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-blue-50 text-[#0072BC] border border-blue-200 font-bold shrink-0">
                  {item.status}
                </span>
              </div>

              <div className="grid grid-cols-2 gap-2 text-xs pt-2 border-t border-stone-100 font-mono">
                <div>
                  <div className="text-stone-400 text-[10px]">ÁMBITO</div>
                  <div className="text-stone-800 font-semibold truncate">{item.scopeTorres}</div>
                </div>
                <div>
                  <div className="text-stone-400 text-[10px]">FAIR ALE</div>
                  <div className="text-[#0072BC] font-bold">{item.presupuestoFairAle}</div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 flex justify-end">
                <button
                  onClick={() => onOpenWorkspace(item.clientSlug)}
                  className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all"
                >
                  <span>Abrir Expediente</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
