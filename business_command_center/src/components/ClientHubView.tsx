'use client';

import React, { useState, useMemo } from 'react';
import {
  Building2,
  Search,
  ExternalLink,
  ShieldCheck,
  ArrowRight,
  TrendingUp,
  LayoutGrid,
  Table as TableIcon,
  Filter,
  CheckCircle2,
  FileText,
  Cpu,
  Layers,
  Globe
} from 'lucide-react';

export interface ClientProfile {
  id: string;
  name: string;
  sector: string;
  country: string;
  currency: string;
  standard: string;
  maturityScore: number;
  totalDeliverables: number;
  residualRisk: string;
  status: 'Certified' | 'In Assessment' | 'Pending';
  description: string;
}

const CANONICAL_CLIENTS: ClientProfile[] = [
  {
    id: 'nordic_grid_power_gmbh',
    name: 'Nordic Grid Power GmbH',
    sector: 'Energy & Utilities',
    country: 'Germany (DE)',
    currency: 'EUR (€)',
    standard: 'NIS2 / Critical Infrastructure',
    maturityScore: 4.4,
    totalDeliverables: 4,
    residualRisk: 'Bajo (€12.4k ALE)',
    status: 'Certified',
    description: 'European electric transmission grid operator with strict physical resilience and sovereign data protection requirements.',
  },
  {
    id: 'global_nippon_financial_group',
    name: 'Global Nippon Financial Group',
    sector: 'Banca & Finanzas',
    country: 'Japan (JP)',
    currency: 'JPY (¥) / USD ($)',
    standard: 'Basel III / Operational Resilience DORA',
    maturityScore: 4.2,
    totalDeliverables: 4,
    residualRisk: 'Bajo ($18.6k ALE)',
    status: 'Certified',
    description: 'International banking conglomerate under continuous business continuity audit and systemic risk mitigation.',
  },
  {
    id: 'meridian_biohealth_inc',
    name: 'Meridian BioHealth Inc.',
    sector: 'Healthcare & Pharma',
    country: 'United States (US)',
    currency: 'USD ($)',
    standard: 'HIPAA / Clinical Data Privacy',
    maturityScore: 4.1,
    totalDeliverables: 4,
    residualRisk: 'Moderado ($24.1k ALE)',
    status: 'Certified',
    description: 'Global biotechnology leader conducting clinical trials with strict genomic metadata governance and chain of custody.',
  },
  {
    id: 'iberia_retail_logistics_s_a',
    name: 'Iberia Retail Logistics S.A.',
    sector: 'Industria & Consumo',
    country: 'Spain (ES)',
    currency: 'EUR (€)',
    standard: 'ENS High / Local Sovereignty',
    maturityScore: 4.3,
    totalDeliverables: 4,
    residualRisk: 'Bajo (€14.2k ALE)',
    status: 'Certified',
    description: 'Logistics and distribution operator with national security certification and DMBOK data governance audit.',
  },
];

const SECTOR_PILLS = [
  'TODOS',
  'Energy & Utilities',
  'Banca & Finanzas',
  'Healthcare & Pharma',
  'Industria & Consumo',
];

interface ClientHubViewProps {
  onSelectClient: (clientId: string) => void;
  activeClientId?: string;
}

export function ClientHubView({ onSelectClient, activeClientId }: ClientHubViewProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('TODOS');
  const [viewMode, setViewMode] = useState<'cards' | 'table'>('cards');

  const filteredClients = useMemo(() => {
    return CANONICAL_CLIENTS.filter((c) => {
      const matchesSector = selectedSector === 'TODOS' || c.sector === selectedSector;
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        c.name.toLowerCase().includes(term) ||
        c.sector.toLowerCase().includes(term) ||
        c.standard.toLowerCase().includes(term) ||
        c.country.toLowerCase().includes(term);
      return matchesSector && matchesSearch;
    });
  }, [searchTerm, selectedSector]);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* Top Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-base font-bold text-white flex items-center gap-2">
            <Building2 className="h-5 w-5 text-blue-400" />
            Portafolio Sectorial de Cuentas y Evaluaciones
          </h2>
          <p className="text-xs text-slate-400 mt-0.5">
            Canonical enterprise classification aligned with engine_config industry profiles.
          </p>
        </div>

        {/* View Switcher */}
        <div className="flex items-center gap-1 p-1 rounded-xl bg-slate-900 border border-slate-800 text-xs font-mono">
          <button
            onClick={() => setViewMode('cards')}
            className={`p-1.5 px-3 rounded-lg flex items-center gap-1.5 transition-all ${
              viewMode === 'cards' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <LayoutGrid className="h-3.5 w-3.5" /> Grid View
          </button>
          <button
            onClick={() => setViewMode('table')}
            className={`p-1.5 px-3 rounded-lg flex items-center gap-1.5 transition-all ${
              viewMode === 'table' ? 'bg-blue-600 text-white font-semibold' : 'text-slate-400 hover:text-white'
            }`}
          >
            <TableIcon className="h-3.5 w-3.5" /> Tabla
          </button>
        </div>
      </div>

      {/* Filters Bar */}
      <div className="flex flex-col sm:flex-row items-center gap-3 bg-[#0d111a] border border-slate-800/80 p-3.5 rounded-2xl">
        <div className="relative flex-1 w-full">
          <Search className="h-4 w-4 text-slate-500 absolute left-3.5 top-2.5" />
          <input
            type="text"
            aria-label="Search by legal entity, regulation, country, or sector"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Search by legal entity, regulation (ENS, NIS2, DORA), country, or sector..."
            className="w-full bg-slate-950 border border-slate-800 rounded-xl pl-10 pr-4 py-2 text-xs text-slate-200 placeholder-slate-600 focus:outline-none focus:border-blue-500 transition-all font-mono"
          />
        </div>

        {/* Sector Pills */}
        <div className="flex items-center gap-1.5 overflow-x-auto w-full sm:w-auto py-1">
          {SECTOR_PILLS.map((s) => (
            <button
              key={s}
              onClick={() => setSelectedSector(s)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${
                selectedSector === s
                  ? 'bg-blue-600/20 text-blue-300 border border-blue-500/40 font-semibold'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-850'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* CARDS VIEW */}
      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {filteredClients.map((client) => {
            const isActive = client.id === activeClientId;
            return (
              <div
                key={client.id}
                className={`p-6 rounded-2xl border transition-all flex flex-col justify-between space-y-4 shadow-xl ${
                  isActive
                    ? 'bg-[#0f1524] border-blue-500/50 ring-1 ring-blue-500/20'
                    : 'bg-[#0d111a] border-slate-800/80 hover:border-slate-700'
                }`}
              >
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-mono uppercase px-2 py-0.5 rounded bg-blue-950 text-blue-300 border border-blue-800/50">
                      {client.sector}
                    </span>
                    <span className="text-[10px] font-mono text-emerald-400 flex items-center gap-1 font-semibold">
                      <CheckCircle2 className="h-3 w-3" /> {client.status}
                    </span>
                  </div>

                  <div>
                    <h3 className="text-sm font-bold text-white tracking-wide">{client.name}</h3>
                    <div className="flex items-center gap-2 mt-1 text-[11px] text-slate-400 font-mono">
                      <span>{client.country}</span>
                      <span>•</span>
                      <span>{client.currency}</span>
                    </div>
                  </div>

                  <p className="text-xs text-slate-400 leading-relaxed line-clamp-2">
                    {client.description}
                  </p>

                  <div className="p-3 rounded-xl bg-slate-950 border border-slate-800/80 grid grid-cols-3 gap-2 text-center text-xs font-mono">
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase">Score</div>
                      <div className="text-xs font-bold text-white">{client.maturityScore} / 5.0</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase">Risk FAIR</div>
                      <div className="text-xs font-bold text-emerald-400">{client.residualRisk.split(' ')[0]}</div>
                    </div>
                    <div>
                      <div className="text-[9px] text-slate-500 uppercase">Entregables</div>
                      <div className="text-xs font-bold text-blue-400">{client.totalDeliverables} Docs</div>
                    </div>
                  </div>
                </div>

                <div className="pt-2 border-t border-slate-800/80 flex items-center justify-between">
                  <span className="text-[10px] font-mono text-slate-500 truncate max-w-[200px]">
                    {client.standard}
                  </span>

                  <button
                    onClick={() => onSelectClient(client.id)}
                    className="flex items-center gap-1.5 px-4 py-2 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-md shadow-blue-600/30"
                  >
                    Open Expediente <ArrowRight className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* TABLE VIEW */}
      {viewMode === 'table' && (
        <div className="bg-[#0d111a] border border-slate-800/80 rounded-2xl overflow-hidden shadow-xl">
          <table className="w-full text-left text-xs">
            <thead className="bg-slate-950/80 border-b border-slate-800 text-[10px] font-mono uppercase text-slate-400 tracking-wider">
              <tr>
                <th className="p-4 px-6">Entidad Corporativa</th>
                <th className="p-4">Sector Industrial</th>
                <th className="p-4">Statutory Framework & Jurisdiction</th>
                <th className="p-4 text-center">Madurez</th>
                <th className="p-4 text-center">Risk ALE</th>
                <th className="p-4 text-right px-6">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800/80 font-mono">
              {filteredClients.map((client) => {
                const isActive = client.id === activeClientId;
                return (
                  <tr
                    key={client.id}
                    className={`hover:bg-slate-900/60 transition-colors ${
                      isActive ? 'bg-blue-950/20' : ''
                    }`}
                  >
                    <td className="p-4 px-6 font-sans font-semibold text-white">
                      <div>{client.name}</div>
                      <div className="text-[10px] text-slate-500 font-mono">{client.country}</div>
                    </td>
                    <td className="p-4 text-slate-300 font-sans">{client.sector}</td>
                    <td className="p-4 text-slate-400">{client.standard}</td>
                    <td className="p-4 text-center font-bold text-white">{client.maturityScore} / 5.0</td>
                    <td className="p-4 text-center text-emerald-400 font-bold">{client.residualRisk}</td>
                    <td className="p-4 text-right px-6 font-sans">
                      <button
                        onClick={() => onSelectClient(client.id)}
                        className="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-sm"
                      >
                        Open
                      </button>
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
