'use client';

import React, { useState, useMemo } from 'react';
import {
  Search,
  Building2,
  ArrowRight,
  LayoutGrid,
  Table as TableIcon,
  Filter,
  Plus,
  Layers,
  ChevronDown
} from 'lucide-react';
import { CANONICAL_ACCOUNTS } from './AccountsCatalogView';
import { CANONICAL_ASSESSMENTS } from './AccountDossierView';

interface AssessmentsCatalogViewProps {
  onOpenWorkspace: (clientSlug: string) => void;
  onNewAssessment: () => void;
}

export function AssessmentsCatalogView({
  onOpenWorkspace,
  onNewAssessment,
}: AssessmentsCatalogViewProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedAccount, setSelectedAccount] = useState<string>('all');
  const [selectedPhase, setSelectedPhase] = useState<string>('all');
  const [onlyActive, setOnlyActive] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [accountMenuOpen, setAccountMenuOpen] = useState(false);
  const [phaseMenuOpen, setPhaseMenuOpen] = useState(false);

  const enrichedAssessments = useMemo(() => {
    return CANONICAL_ASSESSMENTS.map((item) => {
      const acc = CANONICAL_ACCOUNTS.find((a) => a.slug === item.clientSlug);
      return {
        ...item,
        clientName: acc?.name || 'Cliente Corporativo',
        sector: acc?.sector || 'Tecnología',
        country: acc?.country || 'Internacional',
      };
    });
  }, []);

  const filteredAssessments = useMemo(() => {
    return enrichedAssessments.filter((item) => {
      const matchesAccount = selectedAccount === 'all' || item.clientSlug === selectedAccount;
      const matchesPhase = selectedPhase === 'all' || item.status === selectedPhase;
      const matchesActive = !onlyActive || item.status === 'En Curso';
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        item.title.toLowerCase().includes(term) ||
        item.code.toLowerCase().includes(term) ||
        item.clientName.toLowerCase().includes(term) ||
        item.sector.toLowerCase().includes(term);
      return matchesAccount && matchesPhase && matchesActive && matchesSearch;
    });
  }, [enrichedAssessments, selectedAccount, selectedPhase, onlyActive, searchTerm]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Filters Bar (Exact BidStrategy KAIROS Expedientes View) */}
      <div className="bg-white border border-stone-200/80 p-3 sm:p-4 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 w-full">
          <Search className="h-4 w-4 text-stone-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar por expediente, título o cliente..."
            className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
          />
        </div>

        {/* Dropdowns and Toggles */}
        <div className="flex items-center gap-2 w-full md:w-auto flex-wrap sm:flex-nowrap">
          {/* Account Filter */}
          <div className="relative">
            <button
              onClick={() => setAccountMenuOpen(!accountMenuOpen)}
              className="px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#fbfbfa] hover:bg-stone-100 border border-stone-200 text-stone-700 flex items-center gap-2 transition-colors whitespace-nowrap"
            >
              <Building2 className="w-3.5 h-3.5 text-stone-500" />
              <span>
                {selectedAccount === 'all'
                  ? `Todas las cuentas (${CANONICAL_ACCOUNTS.length})`
                  : CANONICAL_ACCOUNTS.find((a) => a.slug === selectedAccount)?.name.split(' ')[0]}
              </span>
              <ChevronDown className="w-3 h-3 text-stone-400" />
            </button>

            {accountMenuOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setAccountMenuOpen(false)} />
                <div className="absolute left-0 mt-2 w-64 rounded-xl bg-white border border-stone-200 shadow-xl p-1 z-40 text-xs space-y-0.5">
                  <button
                    onClick={() => {
                      setSelectedAccount('all');
                      setAccountMenuOpen(false);
                    }}
                    className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                      selectedAccount === 'all'
                        ? 'bg-blue-50 text-[#0072BC] font-semibold'
                        : 'hover:bg-stone-50 text-stone-700'
                    }`}
                  >
                    Todas las cuentas ({CANONICAL_ACCOUNTS.length})
                  </button>
                  {CANONICAL_ACCOUNTS.map((acc) => (
                    <button
                      key={acc.id}
                      onClick={() => {
                        setSelectedAccount(acc.slug);
                        setAccountMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors truncate ${
                        selectedAccount === acc.slug
                          ? 'bg-blue-50 text-[#0072BC] font-semibold'
                          : 'hover:bg-stone-50 text-stone-700'
                      }`}
                    >
                      {acc.name}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Phase Filter */}
          <div className="relative">
            <button
              onClick={() => setPhaseMenuOpen(!phaseMenuOpen)}
              className="px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#fbfbfa] hover:bg-stone-100 border border-stone-200 text-stone-700 flex items-center gap-2 transition-colors whitespace-nowrap"
            >
              <Filter className="w-3.5 h-3.5 text-stone-500" />
              <span>{selectedPhase === 'all' ? 'Todas las fases' : selectedPhase}</span>
              <ChevronDown className="w-3 h-3 text-stone-400" />
            </button>

            {phaseMenuOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setPhaseMenuOpen(false)} />
                <div className="absolute left-0 mt-2 w-48 rounded-xl bg-white border border-stone-200 shadow-xl p-1 z-40 text-xs space-y-0.5">
                  {['all', 'En Curso', 'Finalizado', 'Borrador / Intake'].map((ph) => (
                    <button
                      key={ph}
                      onClick={() => {
                        setSelectedPhase(ph);
                        setPhaseMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        selectedPhase === ph
                          ? 'bg-blue-50 text-[#0072BC] font-semibold'
                          : 'hover:bg-stone-50 text-stone-700'
                      }`}
                    >
                      {ph === 'all' ? 'Todas las fases' : ph}
                    </button>
                  ))}
                </div>
              </>
            )}
          </div>

          {/* Toggle Solo Activas */}
          <button
            onClick={() => setOnlyActive(!onlyActive)}
            className={`px-3.5 py-2.5 rounded-xl text-xs font-semibold flex items-center gap-1.5 transition-colors border whitespace-nowrap ${
              onlyActive
                ? 'bg-blue-50 text-[#0072BC] border-[#0072BC]/40 font-bold'
                : 'bg-[#fbfbfa] hover:bg-stone-100 text-stone-700 border-stone-200'
            }`}
          >
            <Layers className="w-3.5 h-3.5" />
            <span>Solo Activas</span>
          </button>

          {/* Toggle Tabla vs Tarjetas */}
          <div className="flex items-center p-1 bg-stone-100 rounded-xl text-xs border border-stone-200">
            <button
              onClick={() => setViewMode('table')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                viewMode === 'table'
                  ? 'bg-white text-[#0072BC] font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <TableIcon className="w-3.5 h-3.5" />
              <span>Tabla</span>
            </button>
            <button
              onClick={() => setViewMode('cards')}
              className={`px-3 py-1.5 rounded-lg flex items-center gap-1.5 transition-all ${
                viewMode === 'cards'
                  ? 'bg-white text-[#0072BC] font-bold shadow-2xs'
                  : 'text-stone-500 hover:text-stone-800'
              }`}
            >
              <LayoutGrid className="w-3.5 h-3.5" />
              <span>Tarjetas</span>
            </button>
          </div>

          {/* Action Button */}
          <button
            onClick={onNewAssessment}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>Nueva Evaluación</span>
          </button>
        </div>
      </div>

      {/* Main Table */}
      {viewMode === 'table' && (
        <div className="bg-white border border-stone-200/80 rounded-2xl overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#fbfbfa] border-b border-stone-200 text-[11px] font-mono uppercase tracking-wider text-stone-500 font-bold">
                  <th className="py-3.5 px-6">Assessment / Expediente ↕</th>
                  <th className="py-3.5 px-6">Cliente / Cuenta ↕</th>
                  <th className="py-3.5 px-6">Sector</th>
                  <th className="py-3.5 px-6">Fase / Estado</th>
                  <th className="py-3.5 px-6 text-right">Acción</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 text-xs">
                {filteredAssessments.map((item) => (
                  <tr key={item.id} className="hover:bg-blue-50/30 transition-colors group">
                    <td className="py-4 px-6 max-w-md">
                      <div className="font-bold text-sm text-[#1d1d1f] group-hover:text-[#0072BC] transition-colors">
                        {item.title}
                      </div>
                      <div className="text-stone-400 font-mono text-[11px] mt-0.5">
                        #{item.code} · {item.updatedAt}
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <div className="flex items-center gap-2.5">
                        <div className="h-7 w-7 rounded-lg bg-stone-100 border border-stone-200 flex items-center justify-center font-bold text-[#0072BC] text-xs shrink-0 font-mono">
                          {item.clientName.charAt(0)}
                        </div>
                        <span className="font-semibold text-stone-800 truncate max-w-[200px]">
                          {item.clientName}
                        </span>
                      </div>
                    </td>

                    <td className="py-4 px-6">
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-stone-100 text-stone-700 border border-stone-200/80">
                        {item.sector}
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
                        className="px-4 py-2 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white inline-flex items-center gap-1.5 shadow-sm transition-all"
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
        </div>
      )}

      {/* Cards View */}
      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredAssessments.map((item) => (
            <div
              key={item.id}
              className="bg-white border border-stone-200/80 rounded-2xl p-5 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4 hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <h3 className="font-bold text-sm text-[#1d1d1f] line-clamp-2">{item.title}</h3>
                    <p className="text-stone-400 font-mono text-xs mt-0.5">#{item.code}</p>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono bg-blue-50 text-[#0072BC] border border-blue-200 font-bold shrink-0">
                    {item.status}
                  </span>
                </div>

                <div className="space-y-1.5 pt-2 border-t border-stone-100 text-xs">
                  <div className="flex justify-between text-stone-500 font-mono text-[11px]">
                    <span>Cliente:</span>
                    <span className="font-bold text-stone-800 truncate max-w-[170px]">{item.clientName}</span>
                  </div>
                  <div className="flex justify-between text-stone-500 font-mono text-[11px]">
                    <span>Torres:</span>
                    <span className="text-stone-700 font-semibold truncate max-w-[170px]">{item.scopeTorres}</span>
                  </div>
                  <div className="flex justify-between text-stone-500 font-mono text-[11px]">
                    <span>FAIR ALE:</span>
                    <span className="text-[#0072BC] font-bold">{item.presupuestoFairAle}</span>
                  </div>
                </div>
              </div>

              <div className="pt-3 border-t border-stone-100 flex justify-end">
                <button
                  onClick={() => onOpenWorkspace(item.clientSlug)}
                  className="w-full py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center justify-center gap-1.5 shadow-sm transition-all"
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
