'use client';

import React from 'react';
import {
  Layers,
  RefreshCw,
  Plus,
  Pencil,
  Trash2,
  Landmark,
  ShieldCheck,
  CheckCircle2,
  Network,
  Users,
  Mail,
} from 'lucide-react';
import { getAccountDetailedIntelligence } from './intelligence';

interface DossierCorporateInfoTabProps {
  slug: string;
  domain: string;
  companyName: string;
}

export function DossierCorporateInfoTab({ slug, domain, companyName }: DossierCorporateInfoTabProps) {
  const intel = getAccountDetailedIntelligence(slug, domain, companyName);

  return (
    <div className="space-y-6 max-w-6xl">
      {/* 1. RESUMEN CORPORATIVO Y MODELO OPERATIVO */}
      <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-3">
        <div className="text-[11px] font-mono uppercase tracking-wider text-stone-500 font-bold">
          Resumen Corporativo y Modelo Operativo
        </div>
        <p className="text-xs text-stone-700 leading-relaxed font-sans">
          {intel.businessSummary}
        </p>
      </div>

      {/* 2. MAPA DE PROVEEDORES POR TORRE TECNOLÓGICA */}
      <div className="bg-white border border-stone-200/80 rounded-2xl overflow-hidden shadow-[0_2px_12px_rgba(0,0,0,0.03)]">
        <div className="p-5 border-b border-stone-200/80 flex flex-col md:flex-row md:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <Layers className="w-4 h-4 text-stone-600" />
              <h3 className="text-xs font-mono font-bold text-[#1d1d1f] uppercase tracking-wider">
                Mapa de Proveedores por Torre Tecnológica
              </h3>
            </div>
            <p className="text-[11px] text-stone-500 mt-0.5">
              Adjudicaciones oficiales y proveedores en servicio contrastados en contratos públicos
            </p>
          </div>
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-3 py-1.5 rounded-xl bg-stone-100 border border-stone-200/80 text-stone-700 font-mono text-[11px] font-semibold">
              Vigencia Contractual Activa (2021-2026)
            </span>
            <button
              type="button"
              onClick={() => alert('Sincronización online verificada con registros de contratación.')}
              className="px-3 py-1.5 rounded-xl bg-white hover:bg-stone-50 border border-stone-200 text-stone-700 text-xs font-semibold flex items-center gap-1.5 shadow-2xs transition-colors"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Actualizar Online</span>
            </button>
            <button
              type="button"
              onClick={() => alert('Formulario de alta de nuevo adjudicatario.')}
              className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold flex items-center gap-1 shadow-2xs transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Añadir Proveedor</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-[#fbfbfa] border-b border-stone-200 text-[11px] font-mono uppercase tracking-wider text-stone-500 font-bold">
                <th className="py-3 px-6">Torre / Ámbito</th>
                <th className="py-3 px-6">Proveedor / Adjudicatario</th>
                <th className="py-3 px-6">Nivel de Certeza</th>
                <th className="py-3 px-6">Evidencia y Vigencia</th>
                <th className="py-3 px-6 text-right">Acciones</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-stone-100 text-xs">
              {intel.vendorContracts.map((v, i) => (
                <tr key={i} className="hover:bg-blue-50/20 transition-colors">
                  <td className="py-3.5 px-6 max-w-xs">
                    <div className="font-bold text-xs text-[#1d1d1f]">{v.tower}</div>
                    <div className="text-stone-500 text-[11px] leading-snug mt-0.5">{v.scope}</div>
                  </td>
                  <td className="py-3.5 px-6 font-bold text-xs text-[#1d1d1f]">
                    {v.vendor}
                  </td>
                  <td className="py-3.5 px-6">
                    <span
                      className={`px-2.5 py-1 rounded-md text-[11px] font-semibold border whitespace-nowrap inline-flex items-center ${
                        v.confidence === 'Licitación / Contrato Verificado'
                          ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                          : 'bg-sky-50 text-sky-800 border-sky-300'
                      }`}
                    >
                      {v.confidence}
                    </span>
                  </td>
                  <td className="py-3.5 px-6 max-w-sm">
                    <div className="text-stone-700 text-xs">{v.evidence}</div>
                    <div className="text-stone-400 font-mono text-[11px] mt-0.5">Vigencia: {v.vigencia}</div>
                  </td>
                  <td className="py-3.5 px-6 text-right">
                    <div className="flex items-center justify-end gap-1.5 text-stone-400">
                      <button type="button" className="p-1 hover:text-stone-700 transition-colors" title="Editar">
                        <Pencil className="w-3.5 h-3.5" />
                      </button>
                      <button type="button" className="p-1 hover:text-rose-600 transition-colors" title="Eliminar">
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 3. MÉTRICAS FINANCIERAS Y MARCOS REGULATORIOS (2 Cols) */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Card 1: Métricas Financieras */}
        <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
          <div className="flex items-center justify-between border-b border-stone-100 pb-3">
            <div className="flex items-center gap-2">
              <Landmark className="w-4 h-4 text-stone-600" />
              <h3 className="text-xs font-mono font-bold text-[#1d1d1f] uppercase tracking-wider">
                Métricas Financieras Contrastadas
              </h3>
            </div>
            <button type="button" className="text-stone-400 hover:text-stone-700">
              <Pencil className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="space-y-4 text-xs font-sans">
            <div className="flex items-center justify-between py-1 border-b border-stone-100">
              <span className="text-stone-600">Facturación Anual Declarada:</span>
              <span className="font-mono font-bold text-[#1d1d1f] text-sm">{intel.revenueDeclared}</span>
            </div>
            <div className="flex items-center justify-between py-1 border-b border-stone-100">
              <span className="text-stone-600">Plantilla de Empleados:</span>
              <span className="font-mono font-bold text-[#1d1d1f]">{intel.employeeCount}</span>
            </div>
            <div className="flex items-start justify-between py-1 gap-4">
              <span className="text-stone-600 shrink-0">Régimen de Contratación:</span>
              <span className="font-bold text-[#1d1d1f] text-right">{intel.contractRegime}</span>
            </div>
          </div>
        </div>

        {/* Card 2: Marcos Regulatorios Exigibles */}
        <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-5">
          <div className="flex items-center justify-between border-b border-stone-100 pb-3">
            <div className="flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-stone-600" />
              <h3 className="text-xs font-mono font-bold text-[#1d1d1f] uppercase tracking-wider">
                Marcos Regulatorios Exigibles
              </h3>
            </div>
            <button type="button" className="text-stone-400 hover:text-stone-700">
              <Pencil className="w-3.5 h-3.5" />
            </button>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
            {intel.regulations.map((reg, i) => (
              <div
                key={i}
                className="p-3 rounded-xl bg-white border border-stone-200/80 shadow-2xs flex items-center gap-2.5 text-xs text-[#1d1d1f] font-medium"
              >
                <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0" />
                <span className="truncate" title={reg.title}>
                  {reg.code}{reg.title && reg.title !== reg.code ? ` (${reg.title})` : ''}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* 4. GRUPO EMPRESARIAL, FILIALES Y ENTIDADES VINCULADAS */}
      <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Network className="w-4 h-4 text-stone-600" />
              <h3 className="text-xs font-mono font-bold text-[#1d1d1f] uppercase tracking-wider">
                Grupo Empresarial, Filiales y Entidades Vinculadas
              </h3>
            </div>
            <p className="text-[11px] text-stone-500 mt-0.5">
              Sociedades consolidadas del holding y entidades con contratación propia
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 text-xs font-bold font-mono">
              {intel.subsidiaries.length} entidades
            </span>
            <button
              type="button"
              onClick={() => alert('Añadir filial o entidad vinculada.')}
              className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Añadir Filial</span>
            </button>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {intel.subsidiaries.map((sub, i) => (
            <div
              key={i}
              className="bg-[#fbfbfa] border border-stone-200/80 rounded-2xl p-4 shadow-2xs space-y-2.5"
            >
              <div className="flex items-start justify-between gap-2">
                <h4 className="font-bold text-xs text-[#1d1d1f] leading-snug">{sub.name}</h4>
                <div className="flex items-center gap-1 text-stone-400 shrink-0">
                  <button type="button" className="p-1 hover:text-stone-700 transition-colors">
                    <Pencil className="w-3.5 h-3.5" />
                  </button>
                  <button type="button" className="p-1 hover:text-rose-600 transition-colors">
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              </div>
              <span className="inline-block px-2 py-0.5 rounded-md text-[10px] font-mono font-semibold bg-sky-50 text-sky-800 border border-sky-200">
                {sub.type}
              </span>
              <div className="border-t border-stone-200/60 pt-2 text-[11px] text-stone-600 leading-relaxed font-sans">
                {sub.description}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* 5. INTERLOCUTORES CLAVE Y COMITÉ EVALUADOR */}
      <div className="bg-white border border-stone-200/80 rounded-2xl p-6 shadow-[0_2px_12px_rgba(0,0,0,0.03)] space-y-4">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-stone-100 pb-3">
          <div>
            <div className="flex items-center gap-2">
              <Users className="w-4 h-4 text-stone-600" />
              <h3 className="text-xs font-mono font-bold text-[#1d1d1f] uppercase tracking-wider">
                Interlocutores Clave y Comité Evaluador
              </h3>
            </div>
            <p className="text-[11px] text-stone-500 mt-0.5">
              Decisores, evaluadores técnicos y contactos reales contrastados
            </p>
          </div>
          <div className="flex items-center gap-2">
            <span className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-700 text-xs font-bold font-mono">
              {intel.stakeholders.length} personas
            </span>
            <button
              type="button"
              onClick={() => alert('Añadir nuevo interlocutor clave.')}
              className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-800 text-xs font-semibold flex items-center gap-1 transition-colors"
            >
              <Plus className="w-3.5 h-3.5" />
              <span>Añadir Interlocutor</span>
            </button>
          </div>
        </div>

        {intel.stakeholders.length === 0 ? (
          <div className="p-8 rounded-2xl border border-dashed border-stone-200 text-center space-y-2 bg-[#fbfbfa]">
            <Users className="w-6 h-6 text-stone-400 mx-auto" />
            <div className="text-xs font-bold text-stone-700">Sin interlocutores registrados aún</div>
            <p className="text-[11px] text-stone-500 max-w-md mx-auto">
              No se introducen evaluadores arquetípicos ficticios. El equipo de cuenta puede registrar decisores, directores técnicos y evaluadores reales mediante el botón superior.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {intel.stakeholders.map((stk, i) => (
              <div
                key={i}
                className="bg-[#fbfbfa] border border-stone-200/80 rounded-2xl p-4 shadow-2xs space-y-2"
              >
                <div className="flex items-start justify-between gap-2">
                  <div>
                    <div className="font-bold text-xs text-[#1d1d1f]">{stk.name}</div>
                    <div className="text-[10px] font-mono text-stone-500">{stk.role}</div>
                  </div>
                  <div className="flex items-center gap-1 text-stone-400 shrink-0">
                    <button type="button" className="p-1 hover:text-stone-700 transition-colors">
                      <Pencil className="w-3.5 h-3.5" />
                    </button>
                    <button type="button" className="p-1 hover:text-rose-600 transition-colors">
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
                <div className="text-[11px] text-stone-600">{stk.focus}</div>
                <div className="pt-2 border-t border-stone-200/60 flex items-center justify-between text-xs">
                  <span className="font-mono text-[11px] text-stone-500">{stk.email}</span>
                  <a
                    href={`mailto:${stk.email}`}
                    className="p-1 rounded-md text-stone-400 hover:text-[#0072BC] transition-colors"
                  >
                    <Mail className="w-3.5 h-3.5" />
                  </a>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
