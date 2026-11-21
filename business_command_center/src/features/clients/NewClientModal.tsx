'use client';

import React, { useState, useMemo } from 'react';
import {
  X,
  Loader2,
  AlertTriangle,
  Globe,
  ArrowRight
} from 'lucide-react';
import { createNewClientAssessment } from './actions';
import { CANONICAL_ACCOUNTS } from '@/components/AccountsCatalogView';

interface NewClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClientCreated: (slug: string) => void;
}

export function NewClientModal({ isOpen, onClose, onClientCreated }: NewClientModalProps) {
  const [companyName, setCompanyName] = useState('');
  const [domain, setDomain] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const cleanDomain = useMemo(() => {
    return domain
      .trim()
      .toLowerCase()
      .replace(/https?:\/\//, '')
      .replace(/^www\./, '')
      .split('/')[0];
  }, [domain]);

  const duplicateAccount = useMemo(() => {
    if (!cleanDomain) return null;
    return CANONICAL_ACCOUNTS.find((acc) => {
      const accDom = (acc.domain || '')
        .trim()
        .toLowerCase()
        .replace(/https?:\/\//, '')
        .replace(/^www\./, '')
        .split('/')[0];
      return accDom === cleanDomain;
    });
  }, [cleanDomain]);

  if (!isOpen) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!cleanDomain) {
      setErrorMsg('Por favor introduzca el dominio web corporativo.');
      return;
    }

    if (duplicateAccount) {
      setErrorMsg(`El dominio ${cleanDomain} ya pertenece a ${duplicateAccount.name}. No se permiten cuentas duplicadas.`);
      return;
    }

    setIsSubmitting(true);
    setErrorMsg(null);

    // Auto-derive commercial name if omitted
    const derivedName =
      companyName.trim() ||
      cleanDomain
        .split('.')[0]
        .replace(/[-_]/g, ' ')
        .replace(/\b\w/g, (c) => c.toUpperCase());

    // Auto-derive clean slug
    const derivedSlug = derivedName
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');

    try {
      const res = await createNewClientAssessment({
        name: derivedName,
        slug: derivedSlug,
        domain: cleanDomain,
        sector: 'Servicios Corporativos',
        country: cleanDomain.endsWith('.es') ? 'España (ES)' : cleanDomain.endsWith('.de') ? 'Alemania (DE)' : 'Internacional',
        currency: cleanDomain.endsWith('.es') || cleanDomain.endsWith('.de') ? 'EUR (€)' : 'USD ($)',
        standard: 'NIS2 / Critical Infrastructure',
        description: `Expediente de cuenta para ${derivedName} (${cleanDomain}) inicializado.`,
      });

      if (!res.success) {
        setErrorMsg(res.message || 'Error al inicializar la cuenta.');
        return;
      }

      onClientCreated(res.slug || derivedSlug);
      onClose();
    } catch (err: unknown) {
      setErrorMsg(err instanceof Error ? err.message : 'Error de conexión al crear cuenta.');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 bg-black/60 backdrop-blur-xs flex items-center justify-center p-4">
      <div className="bg-white border border-stone-200 rounded-3xl p-6 sm:p-8 max-w-lg w-full shadow-2xl space-y-5 animate-in fade-in zoom-in-95">
        {/* Header (Exact BidStrategy KAIROS Architecture) */}
        <div className="flex items-start justify-between border-b border-stone-100 pb-4">
          <div className="space-y-1">
            <h2 className="text-lg font-bold text-[#1d1d1f]">
              Alta de Cuenta Estratégica
            </h2>
            <p className="text-xs sm:text-sm text-stone-500 leading-relaxed font-sans">
              Introduce el dominio web corporativo para inicializar el expediente de inteligencia de la cuenta.
            </p>
          </div>
          <button
            onClick={onClose}
            className="text-stone-400 hover:text-stone-700 p-1 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-700 text-xs font-medium">
            {errorMsg}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          {/* Nombre Comercial (Opcional) */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-stone-700">
              Nombre Comercial (Opcional)
            </label>
            <input
              type="text"
              value={companyName}
              onChange={(e) => setCompanyName(e.target.value)}
              placeholder="ej. Telefónica, Repsol, CaixaBank"
              className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:bg-white focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/10 transition-all font-sans"
            />
          </div>

          {/* Dominio Web Corporativo (Obligatorio) */}
          <div className="space-y-1.5">
            <label className="block text-xs font-semibold text-stone-700">
              Dominio Web Corporativo (Obligatorio)
            </label>
            <div className="relative">
              <Globe className="w-4 h-4 text-stone-400 absolute left-3.5 top-3" />
              <input
                type="text"
                required
                value={domain}
                onChange={(e) => setDomain(e.target.value)}
                placeholder="ej. repsol.com o caixabank.es"
                className="w-full bg-[#fbfbfa] border border-stone-200 rounded-xl pl-10 pr-4 py-2.5 text-xs sm:text-sm text-[#1d1d1f] placeholder-stone-400 focus:outline-none focus:bg-white focus:border-[#0072BC] focus:ring-2 focus:ring-[#0072BC]/10 transition-all font-sans"
              />
            </div>
          </div>

          {/* Detección de duplicado en tiempo real */}
          {duplicateAccount && (
            <div className="p-3.5 rounded-xl bg-amber-50 border border-amber-200/80 text-xs text-amber-900 space-y-1.5 animate-fadeIn">
              <div className="font-bold flex items-center gap-1.5 text-amber-800">
                <AlertTriangle className="w-4 h-4 text-amber-600 shrink-0" />
                <span>Dominio ya registrado</span>
              </div>
              <p className="text-[11px] leading-relaxed">
                El dominio <strong>{cleanDomain}</strong> ya pertenece a <strong>{duplicateAccount.name}</strong>. No se permiten cuentas duplicadas.
              </p>
              <button
                type="button"
                onClick={() => {
                  onClose();
                  onClientCreated(duplicateAccount.slug);
                }}
                className="text-[11px] font-bold text-[#0072BC] hover:underline flex items-center gap-1 pt-0.5 cursor-pointer"
              >
                <span>Abrir expediente de {duplicateAccount.name} →</span>
              </button>
            </div>
          )}

          {/* Botón de Acción Principal */}
          <div className="pt-2">
            <button
              type="submit"
              disabled={isSubmitting || !!duplicateAccount || !cleanDomain}
              className="w-full py-3 px-4 rounded-xl text-xs sm:text-sm font-semibold bg-[#0072BC] hover:bg-[#0086dd] text-white flex items-center justify-center gap-2 shadow-sm transition-all disabled:opacity-50"
            >
              {isSubmitting ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" />
                  <span>Inicializando expediente...</span>
                </>
              ) : (
                <>
                  <span>Inicializar Cuenta</span>
                  <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
}
