'use client';

import React, { useState, useRef } from 'react';
import JSZip from 'jszip';
import {
  UploadCloud,
  CheckCircle2,
  AlertTriangle,
  X,
  FileText,
  Clock,
  ShieldCheck,
  RefreshCw,
  Trash2,
  Check,
  ArrowRight,
  Loader2,
  FolderArchive
} from 'lucide-react';

interface UploadItem {
  id: string;
  name: string;
  size: number;
  status: 'queued' | 'uploading' | 'admitted' | 'error';
  progress: number;
  errorMsg?: string;
  file?: File;
}

interface KnowledgeHubModalProps {
  isOpen: boolean;
  onClose: () => void;
  clientSlug: string;
  clientName: string;
  onUploadComplete?: () => void;
}

const ALLOWED_EXTENSIONS_SET = new Set([
  '.pdf', '.docx', '.doc', '.xlsx', '.xls', '.pptx', '.ppt',
  '.txt', '.csv', '.xml', '.json', '.png', '.jpg', '.jpeg'
]);

export function KnowledgeHubModal({
  isOpen,
  onClose,
  clientSlug,
  clientName,
  onUploadComplete,
}: KnowledgeHubModalProps) {
  const [items, setItems] = useState<UploadItem[]>([]);
  const [isDragging, setIsDragging] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [statusNotice, setStatusNotice] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  if (!isOpen) return null;

  const extractFiles = async (fileList: FileList | File[]): Promise<File[]> => {
    const result: File[] = [];
    const filesArray = Array.from(fileList);

    for (const file of filesArray) {
      const ext = '.' + file.name.split('.').pop()?.toLowerCase();
      if (ext === '.zip') {
        setStatusNotice(`Descomprimiendo archivo ZIP "${file.name}" en el navegador...`);
        try {
          const zip = await JSZip.loadAsync(await file.arrayBuffer());
          const entries = Object.keys(zip.files);
          for (const path of entries) {
            const entry = zip.files[path];
            if (entry.dir) continue;
            const rawName = path.split('/').pop() || path;
            if (rawName.startsWith('.') || rawName.startsWith('__MACOSX')) continue;
            const entryExt = '.' + rawName.split('.').pop()?.toLowerCase();
            if (ALLOWED_EXTENSIONS_SET.has(entryExt)) {
              const blob = await entry.async('blob');
              result.push(new File([blob], rawName, { type: blob.type }));
            }
          }
        } catch (err: any) {
          console.error('Error descomprimiendo ZIP:', err);
        }
      } else if (ALLOWED_EXTENSIONS_SET.has(ext)) {
        result.push(file);
      }
    }
    setStatusNotice(null);
    return result;
  };

  const handleFilesAdded = async (addedFiles: FileList | File[]) => {
    const extracted = await extractFiles(addedFiles);
    const newItems: UploadItem[] = extracted.map((f, i) => ({
      id: `${Date.now()}_${i}_${f.name}`,
      name: f.name,
      size: f.size,
      status: 'queued',
      progress: 0,
      file: f,
    }));
    setItems((prev) => [...prev, ...newItems]);
  };

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  const handleDragLeave = (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  };

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      await handleFilesAdded(e.dataTransfer.files);
    }
  };

  const handleStartUpload = async () => {
    setIsProcessing(true);
    const queued = items.filter((i) => i.status === 'queued' && i.file);

    for (const item of queued) {
      setItems((prev) =>
        prev.map((it) => (it.id === item.id ? { ...it, status: 'uploading', progress: 30 } : it))
      );

      try {
        const formData = new FormData();
        formData.append('file', item.file!);
        formData.append('client_slug', clientSlug);

        const res = await fetch('/api/upload', {
          method: 'POST',
          body: formData,
        });

        if (!res.ok) {
          const errData = await res.json();
          throw new Error(errData.error || 'Error en subida');
        }

        setItems((prev) =>
          prev.map((it) => (it.id === item.id ? { ...it, status: 'admitted', progress: 100 } : it))
        );
      } catch (err: any) {
        setItems((prev) =>
          prev.map((it) =>
            it.id === item.id ? { ...it, status: 'error', errorMsg: err.message } : it
          )
        );
      }
    }

    setIsProcessing(false);
    if (onUploadComplete) onUploadComplete();
  };

  const removeItem = (id: string) => {
    setItems((prev) => prev.filter((i) => i.id !== id));
  };

  const totalUploaded = items.filter((i) => i.status === 'admitted').length;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 animate-in fade-in duration-200">
      <div className="bg-[#0f141f] border border-white/[0.1] rounded-2xl max-w-2xl w-full p-6 shadow-2xl space-y-5 relative">
        {/* Header */}
        <div className="flex items-center justify-between pb-4 border-b border-white/[0.08]">
          <div className="flex items-center gap-3">
            <div className="h-10 w-10 rounded-xl bg-blue-600/15 border border-blue-500/30 flex items-center justify-center text-blue-400">
              <UploadCloud className="h-5 w-5" />
            </div>
            <div>
              <h2 className="text-sm font-bold text-white tracking-wide">
                Technical Evidence Ingestion · {clientName}
              </h2>
              <p className="text-[11px] text-slate-400 font-mono mt-0.5">
                Destino soberano: <span className="text-blue-400">source_docs/{clientSlug}/</span>
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

        {statusNotice && (
          <div className="p-3 rounded-xl bg-blue-950/60 border border-blue-800/50 text-blue-300 text-xs flex items-center gap-2">
            <Loader2 className="h-4 w-4 animate-spin shrink-0" />
            <span>{statusNotice}</span>
          </div>
        )}

        {/* Drag and Drop Box */}
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`border-2 border-dashed rounded-2xl p-8 text-center cursor-pointer transition-all ${
            isDragging
              ? 'border-blue-500 bg-blue-500/10'
              : 'border-white/[0.1] hover:border-white/[0.2] bg-slate-950/50'
          }`}
        >
          <input
            ref={fileInputRef}
            type="file"
            aria-label="Upload evidence files"
            multiple
            accept=".pdf,.docx,.doc,.xlsx,.xls,.pptx,.txt,.csv,.json,.png,.jpg,.jpeg,.zip"
            onChange={(e) => e.target.files && handleFilesAdded(e.target.files)}
            className="hidden"
          />
          <div className="h-12 w-12 mx-auto rounded-full bg-slate-900 border border-slate-800 flex items-center justify-center text-blue-400 mb-3">
            <FolderArchive className="h-6 w-6" />
          </div>
          <p className="text-xs font-semibold text-white">
            Drag and drop specifications, architecture diagrams, or <span className="text-blue-400 font-mono">.ZIP</span> files here
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            ZIP archives decompress locally in browser saving network bandwidth.
          </p>
          <p className="text-[10px] text-slate-600 font-mono mt-2">
            Formatos admitidos: PDF, DOCX, XLSX, PPTX, JSON, CSV, PNG (Hasta 200MB)
          </p>
        </div>

        {/* Staging List */}
        {items.length > 0 && (
          <div className="space-y-3">
            <div className="flex items-center justify-between text-xs font-mono text-slate-400">
              <span>Archivos en cola ({items.length})</span>
              <span>{totalUploaded} / {items.length} subidos</span>
            </div>

            <div className="max-h-48 overflow-y-auto space-y-2 pr-1">
              {items.map((it) => (
                <div
                  key={it.id}
                  className="p-2.5 px-3.5 rounded-xl bg-slate-950/80 border border-white/[0.06] flex items-center justify-between text-xs font-mono"
                >
                  <div className="flex items-center gap-2.5 overflow-hidden">
                    <FileText className="h-4 w-4 text-blue-400 shrink-0" />
                    <span className="text-white truncate max-w-[280px]">{it.name}</span>
                    <span className="text-[10px] text-slate-500 shrink-0">
                      {(it.size / 1024).toFixed(1)} KB
                    </span>
                  </div>

                  <div className="flex items-center gap-3">
                    {it.status === 'queued' && (
                      <span className="text-[10px] text-slate-400">En cola</span>
                    )}
                    {it.status === 'uploading' && (
                      <span className="text-[10px] text-blue-400 flex items-center gap-1">
                        <Loader2 className="h-3 w-3 animate-spin" /> Subiendo...
                      </span>
                    )}
                    {it.status === 'admitted' && (
                      <span className="text-[10px] text-emerald-400 flex items-center gap-1">
                        <CheckCircle2 className="h-3.5 w-3.5" /> Ingestado
                      </span>
                    )}
                    {it.status === 'error' && (
                      <span className="text-[10px] text-rose-400 flex items-center gap-1" title={it.errorMsg}>
                        <AlertTriangle className="h-3.5 w-3.5" /> Error
                      </span>
                    )}

                    {it.status !== 'uploading' && it.status !== 'admitted' && (
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          removeItem(it.id);
                        }}
                        className="text-slate-500 hover:text-rose-400 p-0.5"
                      >
                        <Trash2 className="h-3.5 w-3.5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Footer Actions */}
        <div className="pt-4 border-t border-white/[0.08] flex items-center justify-between">
          <span className="text-[10px] font-mono text-slate-500">
            Client cryptographic isolation guaranteed
          </span>

          <div className="flex items-center gap-2">
            <button
              onClick={onClose}
              className="px-4 py-2 rounded-xl text-xs font-medium text-slate-400 hover:text-white transition-colors"
            >
              Close
            </button>
            <button
              onClick={handleStartUpload}
              disabled={isProcessing || items.filter((i) => i.status === 'queued').length === 0}
              className="flex items-center gap-2 px-5 py-2.5 rounded-xl text-xs font-semibold bg-blue-600 hover:bg-blue-500 text-white transition-all shadow-md shadow-blue-600/30 disabled:opacity-50"
            >
              {isProcessing ? (
                <>
                  <Loader2 className="h-3.5 w-3.5 animate-spin" />
                  Ingestando en source_docs...
                </>
              ) : (
                <>
                  <UploadCloud className="h-3.5 w-3.5" />
                  Ingestar Evidencias
                </>
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
