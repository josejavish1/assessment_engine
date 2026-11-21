'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import {
  Search,
  ArrowRight,
  LayoutGrid,
  Table as TableIcon,
  Filter,
  Plus,
  Layers,
  ChevronDown
} from 'lucide-react';

import { getAllClientAccountsAction, type ClientAccount } from '@/features/clients/actions';

export { type ClientAccount };

export const CANONICAL_ACCOUNTS: ClientAccount[] = [
  {
    id: 'acc_01',
    slug: 'nordic_grid_power_gmbh',
    name: 'Nordic Grid Power GmbH',
    domain: 'nordicgrid.de',
    sector: 'Energía & Utilities',
    country: 'Alemania (DE)',
    currency: 'EUR (€)',
    standard: 'NIS2 / Critical Infrastructure',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 1,
    maturityScore: '2.9 / 5.0',
    aleFormatted: '131.574,57 €',
    status: 'Activa',
    description: 'Operador europeo de red eléctrica con estrictos requisitos de resiliencia física y protección de datos soberanos.',
  },
  {
    id: 'acc_02',
    slug: 'global_nippon_financial_group',
    name: 'Global Nippon Financial Group',
    domain: 'globalnippon.jp',
    sector: 'Banca & Finanzas',
    country: 'Japón (JP)',
    currency: 'JPY (¥)',
    standard: 'Basel III / Operational Resilience DORA',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 0,
    maturityScore: '2.9 / 5.0',
    aleFormatted: '20.500.000 ¥',
    status: 'Activa',
    description: 'Conglomerado bancario internacional sometido a auditoría continua de resiliencia operativa y gestión de riesgo sistémico.',
  },
  {
    id: 'acc_03',
    slug: 'meridian_biohealth_inc',
    name: 'Meridian BioHealth Inc.',
    domain: 'meridianbio.com',
    sector: 'Salud & Farmacia',
    country: 'Estados Unidos (US)',
    currency: 'USD ($)',
    standard: 'HIPAA / Clinical Data Privacy',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 0,
    maturityScore: '2.9 / 5.0',
    aleFormatted: '185.000,00 $',
    status: 'Activa',
    description: 'Líder biotecnológico global que realiza ensayos clínicos con estricta gobernanza de metadatos genómicos y cadena de custodia.',
  },
  {
    id: 'acc_04',
    slug: 'iberia_retail_logistics_sa',
    name: 'Iberia Retail Logistics S.A.',
    domain: 'iberialogistics.es',
    sector: 'Industria & Logística',
    country: 'España (ES)',
    currency: 'EUR (€)',
    standard: 'ENS Categoría Alta / DMBOK',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 0,
    maturityScore: '2.9 / 5.0',
    aleFormatted: '95.000,00 €',
    status: 'Activa',
    description: 'Operador logístico y de distribución con certificación de seguridad nacional y auditoría de gobernanza de datos DMBOK.',
  },
  {
    id: 'acc_05',
    slug: 'once',
    name: 'Organización Nacional de Ciegos Españoles',
    domain: 'once.es',
    sector: 'Sector Público',
    country: 'España (ES)',
    currency: 'EUR (€)',
    standard: 'ENS Alto / Esquema Nacional de Seguridad',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 0,
    maturityScore: '3.2 / 5.0',
    aleFormatted: '140.000,00 €',
    status: 'Activa',
    description: 'Institución pública española de carácter social con infraestructuras críticas y CPDs híbridos.',
  },
  {
    id: 'acc_06',
    slug: 'repsol',
    name: 'Repsol',
    domain: 'repsol.com',
    sector: 'Energía & Utilities',
    country: 'España (ES)',
    currency: 'EUR (€)',
    standard: 'NIS2 / Critical Infrastructure',
    assessmentsEnCurso: 1,
    assessmentsFinalizados: 0,
    maturityScore: '2.8 / 5.0',
    aleFormatted: '95.000,00 €',
    status: 'Activa',
    description: 'Expediente de cuenta para Repsol (repsol.com) inicializado.',
  },
];

function getCorporateLogoUrl(domain: string): string | null {
  const clean = (domain || '').toLowerCase().trim();
  const knownDomains = [
    'repsol.com',
    'santander.com',
    'bbva.com',
    'telefonica.com',
    'once.es',
    'molins.com',
    'cementosmolins.es',
    'starlingbank.co.uk',
    'rededor.com.br',
  ];
  if (knownDomains.some((kd) => clean === kd || clean.endsWith('.' + kd))) {
    return `https://www.google.com/s2/favicons?domain=${clean}&sz=128`;
  }
  if (
    clean &&
    !clean.includes('nordicgrid') &&
    !clean.includes('globalnippon') &&
    !clean.includes('meridianbio') &&
    !clean.includes('iberialogistics')
  ) {
    return `https://www.google.com/s2/favicons?domain=${clean}&sz=128`;
  }
  return null;
}

interface AccountsCatalogViewProps {
  accounts?: ClientAccount[];
  onOpenDossier: (clientSlug: string) => void;
  onNewAssessment: (clientSlug?: string) => void;
  onNewClient: () => void;
}

export function AccountsCatalogView({
  accounts,
  onOpenDossier,
  onNewAssessment,
  onNewClient,
}: AccountsCatalogViewProps) {
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedSector, setSelectedSector] = useState<string>('Todos los sectores');
  const [onlyActive, setOnlyActive] = useState(false);
  const [viewMode, setViewMode] = useState<'table' | 'cards'>('table');
  const [sectorMenuOpen, setSectorMenuOpen] = useState(false);
  const [dynamicAccounts, setDynamicAccounts] = useState<ClientAccount[]>([]);

  // Automatically fetch dynamic accounts on mount
  React.useEffect(() => {
    getAllClientAccountsAction().then((res) => {
      if (res.success && res.data && res.data.length > 0) {
        setDynamicAccounts(res.data);
      }
    });
  }, []);

  const accountsToDisplay = useMemo(() => {
    if (accounts && accounts.length > 0) return accounts;
    if (dynamicAccounts && dynamicAccounts.length > 0) return dynamicAccounts;
    return CANONICAL_ACCOUNTS;
  }, [accounts, dynamicAccounts]);

  const sortedAccounts = useMemo(() => {
    return [...accountsToDisplay].sort((a, b) =>
      a.name.localeCompare(b.name, 'es', { sensitivity: 'base' })
    );
  }, [accountsToDisplay]);

  const availableSectors = useMemo(() => {
    const list = sortedAccounts.map((a) => a.sector).filter(Boolean);
    return ['Todos los sectores', ...Array.from(new Set(list))];
  }, [sortedAccounts]);

  const filteredAccounts = useMemo(() => {
    return sortedAccounts.filter((acc) => {
      const matchesSector =
        selectedSector === 'Todos los sectores' || acc.sector === selectedSector;
      const matchesActive = !onlyActive || acc.assessmentsEnCurso > 0;
      const term = searchTerm.toLowerCase();
      const matchesSearch =
        acc.name.toLowerCase().includes(term) ||
        acc.domain.toLowerCase().includes(term) ||
        acc.sector.toLowerCase().includes(term) ||
        acc.country.toLowerCase().includes(term);
      return matchesSector && matchesActive && matchesSearch;
    });
  }, [sortedAccounts, searchTerm, selectedSector, onlyActive]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Filter and Action Bar (Identical to BidStrategy KAIROS) */}
      <div className="bg-white border border-stone-200/80 p-3 sm:p-4 rounded-2xl shadow-[0_2px_12px_rgba(0,0,0,0.03)] flex flex-col md:flex-row items-center justify-between gap-3">
        {/* Search Input */}
        <div className="relative flex-1 w-full">
          <Search className="h-4 w-4 text-stone-400 absolute left-3.5 top-3" />
          <input
            type="text"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            placeholder="Buscar cuenta por nombre comercial o dominio web..."
            className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-xs text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:border-[#0072BC] focus:bg-white transition-all font-sans"
          />
        </div>

        {/* Filters Group */}
        <div className="flex items-center gap-2 w-full md:w-auto flex-wrap sm:flex-nowrap">
          {/* Sector Selector Dropdown */}
          <div className="relative">
            <button
              onClick={() => setSectorMenuOpen(!sectorMenuOpen)}
              className="px-3.5 py-2.5 rounded-xl text-xs font-semibold bg-[#fbfbfa] hover:bg-stone-100 border border-stone-200 text-stone-700 flex items-center gap-2 transition-colors whitespace-nowrap"
            >
              <Filter className="w-3.5 h-3.5 text-stone-500" />
              <span>{selectedSector} ({availableSectors.length - 1})</span>
              <ChevronDown className="w-3 h-3 text-stone-400" />
            </button>

            {sectorMenuOpen && (
              <>
                <div className="fixed inset-0 z-30" onClick={() => setSectorMenuOpen(false)} />
                <div className="absolute left-0 mt-2 w-56 rounded-xl bg-white border border-stone-200 shadow-xl p-1 z-40 text-xs space-y-0.5">
                  {availableSectors.map((s) => (
                    <button
                      key={s}
                      onClick={() => {
                        setSelectedSector(s);
                        setSectorMenuOpen(false);
                      }}
                      className={`w-full text-left px-3 py-2 rounded-lg transition-colors ${
                        selectedSector === s
                          ? 'bg-blue-50 text-[#0072BC] font-semibold'
                          : 'hover:bg-stone-50 text-stone-700'
                      }`}
                    >
                      {s}
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
            <span>Solo Assessments Activos</span>
          </button>

          {/* View Mode Toggle: Tabla vs Tarjetas */}
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

          {/* Primary Action Button: + Alta de Cuenta */}
          <button
            onClick={onNewClient}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all whitespace-nowrap"
          >
            <Plus className="w-4 h-4" />
            <span>Alta de Cuenta</span>
          </button>
        </div>
      </div>

      {/* Main Table View */}
      {viewMode === 'table' && (
        <div className="bg-white border border-stone-200/80 rounded-2xl overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse">
              <thead>
                <tr className="bg-[#fbfbfa] border-b border-stone-200 text-[11px] font-mono uppercase tracking-wider text-stone-500 font-bold">
                  <th className="py-3.5 px-6">Cuenta / Empresa ↕</th>
                  <th className="py-3.5 px-6">Sector</th>
                  <th className="py-3.5 px-6 text-center">
                    <div>Assessments ↕</div>
                    <div className="text-[9px] text-stone-400 font-normal">
                      <span className="text-[#0072BC] font-bold">EN CURSO</span> · FINALIZADAS
                    </div>
                  </th>
                  <th className="py-3.5 px-6 text-right">Acciones</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-stone-100 text-xs">
                {filteredAccounts.map((acc) => {
                  const logoUrl = getCorporateLogoUrl(acc.domain);
                  return (
                  <tr key={acc.id} className="hover:bg-blue-50/30 transition-colors group">
                    {/* Cuenta / Empresa */}
                    <td className="py-4 px-6">
                      <div className="flex items-center gap-3.5">
                        <div className="h-10 w-10 rounded-xl bg-white border border-stone-200/80 flex items-center justify-center p-1.5 shrink-0 overflow-hidden shadow-2xs group-hover:scale-105 transition-transform">
                          {logoUrl ? (
                            <Image
                              src={logoUrl}
                              alt={acc.name}
                              width={40}
                              height={40}
                              unoptimized
                              className="w-full h-full object-contain"
                            />
                          ) : (
                            <span className="font-bold text-[#0072BC] font-mono text-sm">
                              {acc.name.charAt(0)}
                            </span>
                          )}
                        </div>
                        <div>
                          <div className="font-bold text-sm text-[#1d1d1f] group-hover:text-[#0072BC] transition-colors">
                            {acc.name}
                          </div>
                          <div className="text-stone-400 font-mono text-[11px] mt-0.5">
                            {acc.domain}
                          </div>
                        </div>
                      </div>
                    </td>

                    {/* Sector */}
                    <td className="py-4 px-6">
                      <span className="px-3 py-1 rounded-full text-xs font-medium bg-stone-100 text-stone-700 border border-stone-200/80">
                        {acc.sector}
                      </span>
                    </td>

                    {/* Assessments (En Curso / Finalizadas) */}
                    <td className="py-4 px-6 text-center">
                      <div className="inline-flex items-center gap-4 font-mono font-bold text-xs">
                        <span className="px-2.5 py-0.5 rounded-full bg-blue-50 text-[#0072BC] border border-blue-200">
                          ● {acc.assessmentsEnCurso}
                        </span>
                        <span className="text-stone-400">{acc.assessmentsFinalizados}</span>
                      </div>
                    </td>

                    {/* Action Buttons */}
                    <td className="py-4 px-6 text-right">
                      <div className="inline-flex items-center gap-2">
                        <button
                          onClick={() => onOpenDossier(acc.slug)}
                          className="px-4 py-1.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all"
                        >
                          <span>Acceder</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>

                        <button
                          onClick={() => onNewAssessment(acc.slug)}
                          className="px-3 py-1.5 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 border border-stone-200 text-stone-700 flex items-center gap-1 transition-colors"
                        >
                          <Plus className="w-3.5 h-3.5" />
                          <span>Nuevo Assessment</span>
                        </button>
                      </div>
                    </td>
                  </tr>
                );
              })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Grid of Cards View */}
      {viewMode === 'cards' && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
          {filteredAccounts.map((acc) => {
            const logoUrl = getCorporateLogoUrl(acc.domain);
            return (
            <div
              key={acc.id}
              className="bg-white border border-stone-200/80 rounded-2xl p-5 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4 hover:shadow-md transition-shadow flex flex-col justify-between"
            >
              <div className="space-y-3">
                <div className="flex items-start justify-between gap-3">
                  <div className="flex items-center gap-3">
                    <div className="h-11 w-11 rounded-xl bg-white border border-stone-200/80 flex items-center justify-center p-1.5 shrink-0 overflow-hidden shadow-2xs group-hover:scale-105 transition-transform">
                      {logoUrl ? (
                        <Image
                          src={logoUrl}
                          alt={acc.name}
                          width={44}
                          height={44}
                          unoptimized
                          className="w-full h-full object-contain"
                        />
                      ) : (
                        <span className="font-bold text-[#0072BC] font-mono text-base">
                          {acc.name.charAt(0)}
                        </span>
                      )}
                    </div>
                    <div>
                      <h3 className="font-bold text-sm text-[#1d1d1f] line-clamp-1">{acc.name}</h3>
                      <p className="text-stone-400 font-mono text-xs">{acc.domain}</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-mono uppercase bg-emerald-50 text-emerald-700 border border-emerald-200 font-bold shrink-0">
                    {acc.status}
                  </span>
                </div>

                <div className="flex items-center justify-between text-xs pt-1 border-t border-stone-100 text-stone-600">
                  <span>{acc.sector}</span>
                  <span className="font-mono text-[#0072BC] font-bold">
                    {acc.assessmentsEnCurso} assessment{acc.assessmentsEnCurso === 1 ? '' : 's'}
                  </span>
                </div>
              </div>

              <div className="flex items-center justify-between pt-3 border-t border-stone-100">
                <button
                  onClick={() => onOpenDossier(acc.slug)}
                  className="text-xs font-bold text-[#0072BC] hover:text-[#0086dd] flex items-center gap-1 transition-colors"
                >
                  <span>Acceder</span>
                  <ArrowRight className="w-3.5 h-3.5" />
                </button>

                <button
                  onClick={() => onNewAssessment(acc.slug)}
                  className="px-2.5 py-1 rounded-lg text-xs font-medium bg-stone-50 hover:bg-stone-100 border border-stone-200 text-stone-700 transition-colors"
                >
                  Nuevo Assessment
                </button>
              </div>
            </div>
          );
        })}
        </div>
      )}
    </div>
  );
}
