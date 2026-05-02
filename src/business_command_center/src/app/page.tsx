// src/business_command_center/src/app/page.tsx
'use client';

import React, { useState } from 'react';
import KanbanColumn from './components/KanbanColumn';
import KanbanCard from './components/KanbanCard';
import CommandPalette from './components/CommandPalette';
import AgentContextSheet from './components/AgentContextSheet';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
  agentic_state?: 'thinking' | 'coding' | 'testing' | 'done';
};

type Columns = {
  backlog: Task[];
  inProgress: Task[];
  done: Task[];
};

const initialTasks: Columns = {
  backlog: [
    { id: 'task-2', title: 'Task 2: Refactorizar scripts a logger.info()', description: 'Reemplaza todos los print() en src/ por logger.info()' },
  ],
  inProgress: [
    { id: 'task-1', title: 'Task 1: Crear plantillas Golden Path', description: 'Crear plantilla base para workers y endpoints', status: 'Running Pytest...', agentic_state: 'thinking' },
  ],
  done: [],
};

export default function Home() {
  const [tasks] = useState<Columns>(initialTasks);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);

  return (
    <>
      <CommandPalette />
      <AgentContextSheet 
        task={selectedTask} 
        isOpen={!!selectedTask} 
        onClose={() => setSelectedTask(null)} 
      />
      <div className="flex h-screen bg-slate-950 text-white">
        {/* Sidebar */}
      <aside className="w-64 bg-slate-900 flex flex-col">
        <div className="h-16 flex items-center justify-center border-b border-slate-800">
          <h1 className="text-xl font-bold tracking-tight">Assessment Platform</h1>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          <a href="#" className="block px-4 py-2 rounded bg-slate-800 text-sm font-medium">Dashboard</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Assessments</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Blueprints</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Settings</a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-slate-900 border-b border-slate-800 flex items-center px-8 justify-between">
          <div className="flex items-center space-x-6">
            <h2 className="text-2xl font-semibold">Assessment Engine Command Center</h2>
            
            {/* Search Button (Triggers Command Palette) */}
            <button 
              onClick={() => document.dispatchEvent(new Event('openCommandPalette'))}
              className="hidden md:flex items-center space-x-2 bg-slate-800 hover:bg-slate-700 text-slate-400 px-3 py-1.5 rounded-md border border-slate-700 transition-colors text-sm"
            >
              <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              <span>Buscar o ejecutar comando...</span>
              <kbd className="pointer-events-none hidden sm:inline-flex h-5 select-none items-center gap-1 rounded border border-slate-600 bg-slate-800 px-1.5 font-mono text-[10px] font-medium opacity-100">
                <span className="text-xs">Ctrl+Shift+P</span>
              </kbd>
            </button>
          </div>
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-green-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-green-500"></span>
            </span>
            <span className="text-sm font-medium text-green-300">MCP Server Online</span>
          </div>
        </header>

        {/* Workspace */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="grid grid-cols-3 gap-8 h-full">
            <KanbanColumn id="backlog" title="Backlog">
              {tasks.backlog.map(task => (
                <KanbanCard key={task.id} task={task} onClick={setSelectedTask} />
              ))}
            </KanbanColumn>
            <KanbanColumn id="inProgress" title="In Progress">
              {tasks.inProgress.map(task => (
                <KanbanCard key={task.id} task={task} onClick={setSelectedTask} />
              ))}
            </KanbanColumn>
            <KanbanColumn id="done" title="Done">
              {tasks.done.map(task => (
                <KanbanCard key={task.id} task={task} onClick={setSelectedTask} />
              ))}
            </KanbanColumn>
          </div>
        </div>
      </main>
    </div>
    </>
  );
}
