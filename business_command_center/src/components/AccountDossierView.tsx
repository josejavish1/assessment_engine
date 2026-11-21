'use client';

import React, { useState, useMemo } from 'react';
import Image from 'next/image';
import {
  Building2,
  ArrowLeft,
  FileText,
  Users,
  Globe,
  Plus,
} from 'lucide-react';
import { CANONICAL_ACCOUNTS, type ClientAccount } from './AccountsCatalogView';
import { CANONICAL_ASSESSMENTS, type AccountAssessment } from './dossier/intelligence';
import { DossierAssessmentsTab } from './dossier/DossierAssessmentsTab';
import { DossierCorporateInfoTab } from './dossier/DossierCorporateInfoTab';
import { DossierNotesTab } from './dossier/DossierNotesTab';
import { DossierUsersTab } from './dossier/DossierUsersTab';

export { CANONICAL_ASSESSMENTS, type AccountAssessment } from './dossier/intelligence';

interface AccountDossierViewProps {
  clientSlug: string;
  accounts?: ClientAccount[];
  onBack: () => void;
  onOpenWorkspace: (clientSlug: string) => void;
  onNewAssessment: (clientSlug: string) => void;
}

export function AccountDossierView({
  clientSlug,
  accounts,
  onBack,
  onOpenWorkspace,
  onNewAssessment,
}: AccountDossierViewProps) {
  const [subTab, setSubTab] = useState<'assessments' | 'info' | 'notes' | 'users'>('assessments');

  const accountsPool = accounts && accounts.length > 0 ? accounts : CANONICAL_ACCOUNTS;

  const account = useMemo(() => {
    return (
      accountsPool.find((a) => a.slug === clientSlug) ||
      CANONICAL_ACCOUNTS.find((a) => a.slug === clientSlug) ||
      CANONICAL_ACCOUNTS[0]
    );
  }, [accountsPool, clientSlug]);

  const clientAssessments: AccountAssessment[] = useMemo(() => {
    const list = CANONICAL_ASSESSMENTS.filter((a) => a.clientSlug === account.slug);
    if (list.length > 0) return list;
    return [
      {
        id: `as_${account.slug}`,
        code: `${account.slug.slice(0, 4)}01`,
        title: `Evaluación Inicial de Madurez y Resiliencia Tecnológica — ${account.standard || 'NIS2'}`,
        clientSlug: account.slug,
        scopeTorres: 'Cloud, K8s, Sec, DR, Gov',
        presupuestoFairAle: account.aleFormatted || '95.000,00 €',
        standard: account.standard || 'NIS2 / Critical Infrastructure',
        status: 'En Curso',
        maturityScore: account.maturityScore || '2.8 / 5.0 (Definido)',
        updatedAt: new Date().toLocaleDateString('es-ES'),
      },
    ];
  }, [account]);

  return (
    <div className="space-y-6 max-w-7xl mx-auto p-4 sm:p-6 lg:p-8">
      {/* Top Breadcrumb & Account Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="px-3.5 py-2 rounded-xl text-xs font-semibold bg-white hover:bg-stone-50 border border-stone-200 text-stone-700 flex items-center gap-1.5 shadow-2xs transition-colors shrink-0"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>Volver a Cuentas</span>
          </button>

          <div className="h-12 w-12 rounded-2xl bg-white border border-stone-200/80 flex items-center justify-center p-2 shrink-0 overflow-hidden shadow-xs">
            <Image
              src={`https://www.google.com/s2/favicons?domain=${account.domain}&sz=128`}
              alt={account.name}
              width={48}
              height={48}
              unoptimized
              className="w-full h-full object-contain"
            />
          </div>

          <div>
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-lg sm:text-xl font-bold text-[#1d1d1f] tracking-tight">
                {account.name}
              </h1>
            </div>
            <div className="flex items-center gap-2.5 text-xs text-stone-500 font-mono mt-0.5 flex-wrap">
              <span className="px-2 py-0.5 rounded-full bg-stone-100 border border-stone-200 text-stone-700 font-sans">
                {account.sector}
              </span>
              <span>·</span>
              <a
                href={`https://${account.domain}`}
                target="_blank"
                rel="noreferrer"
                className="hover:text-[#0072BC] flex items-center gap-1 transition-colors"
              >
                <Globe className="w-3 h-3" />
                <span>{account.domain}</span>
              </a>
              <span>·</span>
              <span className="text-stone-400">Jurisdicción: {account.country}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 self-start md:self-auto flex-wrap">
          <button
            onClick={() => onNewAssessment(account.slug)}
            className="px-4 py-2.5 rounded-xl text-xs font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center gap-1.5 shadow-sm transition-all"
          >
            <Plus className="w-4 h-4" />
            <span>Nuevo Assessment</span>
          </button>
        </div>
      </div>

      {/* Account KPI Ribbon */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-white border border-stone-200/80 rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-stone-400">Puntaje de Madurez</div>
          <div className="text-base sm:text-lg font-bold text-[#1d1d1f] font-mono mt-1">
            {account.maturityScore}
          </div>
          <div className="text-[10px] text-stone-500 mt-0.5">Media ponderada CMMI/O-FAIR</div>
        </div>

        <div className="bg-white border border-stone-200/80 rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-stone-400">FAIR Loss Exposure (ALE)</div>
          <div className="text-base sm:text-lg font-bold text-[#0072BC] font-mono mt-1">
            {account.aleFormatted}
          </div>
          <div className="text-[10px] text-stone-500 mt-0.5">Pérdida anual esperada p95</div>
        </div>

        <div className="bg-white border border-stone-200/80 rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-stone-400">Marco de Referencia</div>
          <div className="text-xs sm:text-sm font-bold text-[#1d1d1f] truncate mt-1">
            {account.standard}
          </div>
          <div className="text-[10px] text-stone-500 mt-0.5">Directiva o estándar auditado</div>
        </div>

        <div className="bg-white border border-stone-200/80 rounded-2xl p-4 shadow-[0_2px_10px_rgba(0,0,0,0.02)]">
          <div className="text-[11px] font-mono uppercase tracking-wider text-stone-400">Estado de Cuenta</div>
          <div className="flex items-center gap-2 mt-1">
            <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
            <span className="text-xs sm:text-sm font-bold text-stone-800">{account.status}</span>
          </div>
          <div className="text-[10px] text-stone-500 mt-0.5">Expediente contractual activo</div>
        </div>
      </div>

      {/* Subtab Navigation Bar */}
      <div className="flex items-center gap-2 border-b border-stone-200/80 overflow-x-auto pb-1">
        <button
          onClick={() => setSubTab('assessments')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            subTab === 'assessments'
              ? 'border-[#0072BC] text-[#0072BC] font-bold'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Assessments ({clientAssessments.length})</span>
        </button>

        <button
          onClick={() => setSubTab('info')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            subTab === 'info'
              ? 'border-[#0072BC] text-[#0072BC] font-bold'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <Building2 className="w-3.5 h-3.5" />
          <span>Información de Cuenta (Intel Corporativo)</span>
        </button>

        <button
          onClick={() => setSubTab('notes')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            subTab === 'notes'
              ? 'border-[#0072BC] text-[#0072BC] font-bold'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Bitácora de Notas</span>
        </button>

        <button
          onClick={() => setSubTab('users')}
          className={`py-3 px-4 text-xs font-semibold border-b-2 transition-all flex items-center gap-2 whitespace-nowrap ${
            subTab === 'users'
              ? 'border-[#0072BC] text-[#0072BC] font-bold'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <Users className="w-3.5 h-3.5" />
          <span>Usuarios del Cliente</span>
        </button>
      </div>

      {/* Render Subtabs */}
      {subTab === 'assessments' && (
        <DossierAssessmentsTab
          clientAssessments={clientAssessments}
          onOpenWorkspace={onOpenWorkspace}
        />
      )}

      {subTab === 'info' && (
        <DossierCorporateInfoTab
          slug={account.slug}
          domain={account.domain}
          companyName={account.name}
        />
      )}

      {subTab === 'notes' && (
        <DossierNotesTab
          initialNotes={[
            `[16/11/2026 - Consultoría NTT DATA]: Se verificó la alineación del expediente con el marco regulatorio ${account.standard}.`,
            `[14/11/2026 - Auditoría Actuarial]: Calibración Monte Carlo de pérdida anualizada (ALE) confirmada en ${account.aleFormatted}.`,
          ]}
        />
      )}

      {subTab === 'users' && (
        <DossierUsersTab
          accountSlug={account.slug}
          accountName={account.name}
        />
      )}
    </div>
  );
}
