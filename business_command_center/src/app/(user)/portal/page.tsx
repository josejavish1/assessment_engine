'use client';

import React from 'react';
import { 
  FileText, 
  UploadCloud, 
  Clock, 
  CheckCircle2, 
  ArrowUpRight 
} from 'lucide-react';

export default function UserPortalPage() {
  const pendingTasks = [
    { id: 1, title: 'Cargar Matriz de Evidencias de Seguridad (T2)', deadline: 'Hoy, 18:00', priority: 'High' },
    { id: 2, title: 'Confirm Data Catalog and DMBOK Lineage (T3)', deadline: 'Tomorrow', priority: 'Medium' },
    { id: 3, title: 'Validate DORA Deployment Metrics (T4)', deadline: '31 Oct', priority: 'Normal' },
  ];

  return (
    <div className="space-y-8">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-white">Mis Tareas y Evaluaciones Asignadas</h1>
        <p className="text-sm text-slate-400 mt-1">
          Documentary evidence submission and continuous assessment audit tracking.
        </p>
      </div>

      {/* Action Banner */}
      <div className="bg-gradient-to-r from-indigo-900/40 via-purple-900/30 to-slate-900 border border-indigo-500/30 p-6 rounded-2xl flex items-center justify-between">
        <div className="space-y-1">
          <h2 className="text-base font-semibold text-white">Rapid Evidence Ingestion</h2>
          <p className="text-xs text-slate-300">
            Upload architecture diagrams, screenshots, or JSON files for automated verification.
          </p>
        </div>
        <button className="flex items-center gap-2 px-4 py-2.5 rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white font-medium text-xs transition-colors shadow-lg shadow-indigo-600/30">
          <UploadCloud className="h-4 w-4" />
          Subir Evidencias
        </button>
      </div>

      {/* Task List */}
      <div className="bg-slate-900 border border-slate-800 rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-800 flex items-center justify-between">
          <h2 className="text-base font-semibold text-white">Pending Assessment Tasks</h2>
          <span className="text-xs text-indigo-400 font-mono">3 acciones requeridas</span>
        </div>

        <div className="divide-y divide-slate-800">
          {pendingTasks.map((task) => (
            <div key={task.id} className="p-4 px-6 flex items-center justify-between hover:bg-slate-800/40 transition-colors">
              <div className="flex items-center gap-4">
                <div className="h-8 w-8 rounded-lg bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center text-indigo-400">
                  <FileText className="h-4 w-4" />
                </div>
                <div>
                  <span className="font-medium text-sm text-white block">{task.title}</span>
                  <div className="flex items-center gap-3 mt-0.5">
                    <span className="text-xs text-slate-400 flex items-center gap-1">
                      <Clock className="h-3 w-3" />
                      Deadline: {task.deadline}
                    </span>
                    <span className="text-[10px] font-semibold px-1.5 py-0.5 rounded bg-indigo-950 text-indigo-300 border border-indigo-800/50">
                      Priority {task.priority}
                    </span>
                  </div>
                </div>
              </div>

              <button className="flex items-center gap-1 px-3 py-1.5 rounded-lg text-xs font-medium text-indigo-400 hover:text-indigo-300 hover:bg-indigo-500/10 transition-colors">
                Completar
                <ArrowUpRight className="h-3.5 w-3.5" />
              </button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
