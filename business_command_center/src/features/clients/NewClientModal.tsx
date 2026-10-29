'use client';

import React, { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { clientSchema, type ClientFormValues } from './schema';
import { createNewClientAssessment } from './actions';
import {
  Building2,
  X,
  Plus,
  Loader2,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Globe,
  Coins,
  Layers,
  FileText
} from 'lucide-react';

interface NewClientModalProps {
  isOpen: boolean;
  onClose: () => void;
  onClientCreated: (slug: string) => void;
}

export function NewClientModal({ isOpen, onClose, onClientCreated }: NewClientModalProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors },
    reset,
  } = useForm<ClientFormValues>({
    resolver: zodResolver(clientSchema),
    defaultValues: {
      name: '',
      slug: '',
      sector: 'Banca & Finanzas',
      country: 'Spain (ES)',
      currency: 'EUR (€)',
      standard: 'ENS High Category',
      description: '',
    },
  });

  if (!isOpen) return null;

  const onNameInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const val = e.target.value;
    const generatedSlug = val
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .replace(/[^a-z0-9]+/g, '_')
      .replace(/^_+|_+$/g, '');
    setValue('slug', generatedSlug, { shouldValidate: true });
  };

  const onSubmit = async (values: ClientFormValues) => {
    setIsSubmitting(true);
    setErrorMsg(null);

    try {
      const res = await createNewClientAssessment(values);
      if (res.success && res.slug) {
        reset();
        onClientCreated(res.slug);
        onClose();
      } else {
        setErrorMsg(res.message || 'Error al aprovisionar el cliente');
      }
    } catch (err: any) {
      setErrorMsg(err.message || 'Connection error');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#0f141f] border border-white/[0.1] rounded-2xl max-w-xl w-full p-6 shadow-2xl space-y-5 relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <Building2 className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">
                High de New Expediente / Cliente
              </h2>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Physical provisioning in source_docs and registration in Supabase
              </p>
            </div>
          </div>

          <button
            onClick={onClose}
            aria-label="Close modal"
            className="text-slate-400 hover:text-white p-1 rounded-lg hover:bg-slate-800 transition-colors"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        {errorMsg && (
          <div className="p-3.5 rounded-xl bg-rose-950/40 border border-rose-800/60 text-rose-300 text-xs flex items-start gap-2.5">
            <AlertCircle className="w-4 h-4 text-rose-400 shrink-0 mt-0.5" />
            <span>{errorMsg}</span>
          </div>
        )}

        {/* Form */}
        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            {/* Nombre Corporativo */}
            <div className="space-y-1.5 sm:col-span-2">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                Legal Entity Name / Organization Corporativo *
              </label>
              <input
                type="text"
                aria-label="Legal Entity Name"
                autoFocus
                placeholder="Ej. Banco Santander Spain"
                {...register('name', { onChange: onNameInput })}
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
              />
              {errors.name && (
                <p className="text-[11px] text-rose-400 font-mono">{errors.name.message}</p>
              )}
            </div>

            {/* Slug Identificador */}
            <div className="space-y-1.5 sm:col-span-2">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider">
                System Physical Slug * (On-disk directory name)
              </label>
              <input
                type="text"
                aria-label="System Physical Slug"
                {...register('slug')}
                placeholder="banco_santander_es"
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all font-mono"
              />
              {errors.slug && (
                <p className="text-[11px] text-rose-400 font-mono">{errors.slug.message}</p>
              )}
            </div>

            {/* Sector Industrial */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                <Layers className="h-3 w-3 text-blue-400" /> Sector Industrial *
              </label>
              <select
                {...register('sector')}
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-all"
              >
                <option value="Banca & Finanzas">Banca & Finanzas</option>
                <option value="Energy & Utilities">Energy & Utilities</option>
                <option value="Healthcare & Pharma">Healthcare & Pharma</option>
                <option value="Industria & Consumo">Industria & Consumo</option>
                <option value="Public Sector">Public Sector</option>
                <option value="Telco & Medium">Telco & Medium</option>
              </select>
            </div>

            {/* Jurisdiction / Country */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                <Globe className="h-3 w-3 text-emerald-400" /> Country / Jurisdiction *
              </label>
              <select
                {...register('country')}
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-all"
              >
                <option value="Spain (ES)">Spain (ES)</option>
                <option value="Germany (DE)">Germany (DE)</option>
                <option value="United Kingdom (UK)">United Kingdom (UK)</option>
                <option value="United States (US)">United States (US)</option>
                <option value="Japan (JP)">Japan (JP)</option>
                <option value="Global / Multirregional">Global / Multirregional</option>
              </select>
            </div>

            {/* Divisa */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                <Coins className="h-3 w-3 text-amber-400" /> Divisa Operativa *
              </label>
              <select
                {...register('currency')}
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-all font-mono"
              >
                <option value="EUR (€)">EUR (€)</option>
                <option value="USD ($)">USD ($)</option>
                <option value="GBP (£)">GBP (£)</option>
                <option value="JPY (¥)">JPY (¥)</option>
              </select>
            </div>

            {/* Marco Normativo */}
            <div className="space-y-1.5">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                <ShieldCheck className="h-3 w-3 text-purple-400" /> Marco Normativo *
              </label>
              <select
                {...register('standard')}
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2.5 text-xs text-white focus:outline-none focus:border-blue-500 transition-all"
              >
                <option value="ENS High Category">ENS High Category (Spain)</option>
                <option value="DORA / Basel III">DORA / Basel III (Financiero)</option>
                <option value="NIS2 / Critical Infrastructure">NIS2 / Critical Infrastructure (UE)</option>
                <option value="DAMA DMBOK">DAMA DMBOK (Gobierno del Dato)</option>
                <option value="HIPAA / Healthcare Privacy">HIPAA (Healthcare / US)</option>
                <option value="ISO 27001">ISO 27001 (Internacional)</option>
              </select>
            </div>

            {/* Description / Notes */}
            <div className="space-y-1.5 sm:col-span-2">
              <label className="block text-[11px] font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1">
                <FileText className="h-3 w-3 text-slate-400" /> Alcance del Expediente / Observaciones
              </label>
              <textarea
                {...register('description')}
                rows={2}
                placeholder="Technical RFP for infrastructure modernization and sovereign cybersecurity compliance..."
                className="w-full bg-[#080b12] border border-white/[0.08] rounded-xl px-3.5 py-2 text-xs text-white placeholder-slate-600 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all resize-none"
              />
            </div>
          </div>

          {/* Footer Actions */}
          <div className="pt-4 border-t border-white/[0.08] flex items-center justify-between">
            <span className="text-[10px] font-mono text-slate-500">
              Deterministic physical and logical provisioning
            </span>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={onClose}
                className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
              >
                Cancelar
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white transition-all shadow-md shadow-blue-600/30 disabled:opacity-50"
              >
                {isSubmitting ? (
                  <>
                    <Loader2 className="h-3.5 w-3.5 animate-spin" />
                    Aprovisionando Expediente...
                  </>
                ) : (
                  <>
                    <Plus className="h-3.5 w-3.5" />
                    Registrar y Open Expediente
                  </>
                )}
              </button>
            </div>
          </div>
        </form>
      </div>
    </div>
  );
}
