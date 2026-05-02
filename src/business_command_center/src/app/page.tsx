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
          <h2 className="text-2xl font-semibold">Assessment Engine Command Center</h2>
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
