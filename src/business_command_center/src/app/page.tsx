// src/business_command_center/src/app/page.tsx
'use client';

import React, { useState } from 'react';
import KanbanColumn from './components/KanbanColumn';
import KanbanCard from './components/KanbanCard';
import { FloatingOmnibar } from './components/FloatingOmnibar';
import { ArtifactCanvas } from './components/ArtifactCanvas';
import { ExecutiveExecutionDashboard } from './components/ExecutiveExecutionDashboard';
import { AgentChat, Message } from './components/AgentChat';
import { ThemeToggle } from './components/ThemeToggle';
import { LayoutDashboard, CheckSquare, Map, Settings } from 'lucide-react';
import { submitProductOwnerRequest, checkPlanStatus } from './actions/mcp';

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
  backlog: [],
  inProgress: [],
  done: [],
};

type ViewMode = 'dashboard' | 'planning' | 'execution';

export default function Home() {
  const [tasks, setTasks] = useState<Columns>(initialTasks);
  const [selectedTask, setSelectedTask] = useState<Task | null>(null);
  const [generatedPlan, setGeneratedPlan] = useState<any>(null);
  const [requestDir, setRequestDir] = useState<string>('');
  const [viewMode, setViewMode] = useState<ViewMode>('dashboard');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [chatMessages, setChatMessages] = useState<Message[]>([]);
  const [approvedAltIndex, setApprovedAltIndex] = useState(0);

  const generateId = () => Math.random().toString(36).substring(2, 9);

  const requestPlanFromAgent = async (prompt: string, history: Message[]) => {
    setIsSubmitting(true);
    
    // Build context-aware prompt for the backend
    let fullPrompt = prompt;
    if (history.length > 0) {
      const historyContext = history.map(m => `${m.role === 'user' ? 'Product Owner' : 'Architect'}: ${m.content}`).join('\n\n');
      fullPrompt = `Historial de la conversación:\n${historyContext}\n\nNueva instrucción/feedback del Product Owner:\n${prompt}`;
    }

    const response = await submitProductOwnerRequest(fullPrompt);
    
    if (response.success && response.jobId) {
      const pollInterval = setInterval(async () => {
        const statusRes = await checkPlanStatus(response.jobId);
        if (!statusRes.success || statusRes.status === "error") {
          clearInterval(pollInterval);
          setIsSubmitting(false);
          console.error("Job error:", statusRes.error || statusRes.result);
          alert("El orquestador devolvió un error. Revisa la consola.");
          return;
        }
        if (statusRes.status === "completed") {
          clearInterval(pollInterval);
          setIsSubmitting(false);
          
          let planData = null;
          let reqDir = "";
          try {
              const textContent = statusRes.result;
              if (textContent && textContent.startsWith("✅")) {
                const lines = textContent.split('\n');
                const requestDirLine = lines.find((l: string) => l.startsWith('REQUEST_DIR='));
                if (requestDirLine) {
                  reqDir = requestDirLine.replace('REQUEST_DIR=', '').trim();
                }
                const jsonPart = lines.slice(requestDirLine ? 2 : 1).join('\n');
                planData = JSON.parse(jsonPart);
                
                setGeneratedPlan(planData);
                setRequestDir(reqDir);
                setViewMode('planning');
                
                let assistantMessage = 'He generado una nueva versión del plan de arquitectura basada en tus indicaciones. Revisa las alternativas a la derecha.';
                if (planData.is_ambiguous) {
                  assistantMessage = planData.clarification_question;
                }
                setChatMessages(prev => [...prev, {
                  id: generateId(),
                  role: 'assistant',
                  content: assistantMessage
                }]);
              } else {
                console.error("Orchestrator returned an error:", textContent);
                alert("El orquestador devolvió un error. Revisa la consola.");
              }
          } catch (e) {
              console.error("Could not parse plan json:", e);
              alert("Error al parsear el plan generado.");
          }
        }
      }, 2000);
    } else {
      setIsSubmitting(false);
      console.error("Error:", response.error);
      alert("Error al contactar con el orquestador MCP. Revisa la consola.");
    }
  };

  const handleOmnibarSubmit = (plan: any, initialRequest: string, reqDir: string) => {
    let assistantMessage = 'He analizado tu petición y he generado alternativas para el plan. Puedes revisarlas a la derecha y sugerirme cualquier cambio en este chat.';
    if (plan.is_ambiguous) {
      assistantMessage = plan.clarification_question;
    }
    // Se ejecuta en la primera petición desde el Dashboard
    setChatMessages([{
      id: generateId(),
      role: 'user',
      content: initialRequest
    }, {
      id: generateId(),
      role: 'assistant',
      content: assistantMessage
    }]);
    setGeneratedPlan(plan);
    setRequestDir(reqDir);
    setViewMode('planning');
  };

  const handleChatSendMessage = async (content: string) => {
    // Añadimos el mensaje del usuario al chat visual
    const newUserMsg: Message = { id: generateId(), role: 'user', content };
    const newHistory = [...chatMessages, newUserMsg];
    setChatMessages(newHistory);
    
    // Solicitamos el nuevo plan iterado
    await requestPlanFromAgent(content, chatMessages);
  };

  const handleApprovePlan = (altIndex: number) => {
    setApprovedAltIndex(altIndex);
    
    // Inyectar tareas al Kanban Backlog
    const approvedPlan = generatedPlan.alternatives ? generatedPlan.alternatives[altIndex] : generatedPlan;
    if (approvedPlan && approvedPlan.tasks) {
      setTasks(prev => ({
        ...prev,
        backlog: approvedPlan.tasks.map((t: any) => ({
          id: t.id || Math.random().toString(36).substring(2, 9),
          title: t.title,
          description: t.objective || t.description || '',
          agentic_state: 'thinking'
        }))
      }));
    }
    
    setViewMode('execution');
  };

  const handleRejectPlan = () => {
    setGeneratedPlan(null);
    setRequestDir('');
    setChatMessages([]);
    setViewMode('dashboard');
  };

  return (
    <>
      {viewMode !== 'planning' && (
        <FloatingOmnibar 
          onPlanGenerated={(plan, request, requestDir) => handleOmnibarSubmit(plan, request, requestDir)} 
          isSubmitting={isSubmitting}
          setIsSubmitting={setIsSubmitting}
        />
      )}
      
      <div className="flex h-screen bg-background text-foreground">
        {/* Sidebar */}
        <aside className="w-16 lg:w-64 bg-muted/30 border-r border-border flex flex-col justify-between z-10 relative transition-all">
          <div>
            <div className="h-16 flex items-center justify-center border-b border-border">
              <h1 className="text-xl font-bold tracking-tight hidden lg:block">Assessment Platform</h1>
              <LayoutDashboard className="h-6 w-6 lg:hidden text-primary" />
            </div>
            <nav className="px-2 lg:px-4 py-6 space-y-2">
              <a href="#" onClick={(e) => {e.preventDefault(); setViewMode('dashboard');}} className="flex items-center gap-3 px-2 lg:px-4 py-2 rounded-md bg-muted text-foreground text-sm font-medium transition-colors justify-center lg:justify-start hover:bg-muted/80">
                <LayoutDashboard className="h-5 w-5 shrink-0" />
                <span className="hidden lg:block">Dashboard</span>
              </a>
              <a href="#" className="flex items-center gap-3 px-2 lg:px-4 py-2 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground text-sm font-medium transition-colors justify-center lg:justify-start">
                <CheckSquare className="h-5 w-5 shrink-0" />
                <span className="hidden lg:block">Assessments</span>
              </a>
              <a href="#" className="flex items-center gap-3 px-2 lg:px-4 py-2 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground text-sm font-medium transition-colors justify-center lg:justify-start">
                <Map className="h-5 w-5 shrink-0" />
                <span className="hidden lg:block">Blueprints</span>
              </a>
              <a href="#" className="flex items-center gap-3 px-2 lg:px-4 py-2 rounded-md text-muted-foreground hover:bg-muted hover:text-foreground text-sm font-medium transition-colors justify-center lg:justify-start">
                <Settings className="h-5 w-5 shrink-0" />
                <span className="hidden lg:block">Settings</span>
              </a>
            </nav>
          </div>
          <div className="p-2 lg:p-4 border-t border-border/50 flex justify-center lg:justify-start">
            <ThemeToggle />
          </div>
        </aside>

        {/* Main Content Area (Liquid Layout) */}
        <main className="flex-1 flex flex-col overflow-hidden relative">
          {/* Header */}
          <header className="h-16 sticky top-0 z-10 bg-background/80 backdrop-blur-md border-b border-border flex items-center px-8 justify-between shrink-0">
            <div className="flex items-center space-x-6">
              <h2 className="text-2xl font-semibold">
                {viewMode === 'planning' ? 'Workspace: Architect Review' : 'Assessment Engine Command Center'}
              </h2>
            </div>
            <div className="flex items-center space-x-2 bg-green-500/10 px-2.5 py-1 rounded-md border border-green-500/20">
              <span className="relative flex h-2 w-2">
                <span className="animate-pulse absolute inline-flex h-full w-full rounded-full bg-green-500 opacity-75"></span>
                <span className="relative inline-flex rounded-full h-2 w-2 bg-green-500"></span>
              </span>
              <span className="text-xs font-medium text-green-600 dark:text-green-400">MCP Server Online</span>
            </div>
          </header>

          {/* Liquid Render */}
          {viewMode === 'execution' && generatedPlan ? (
            <ExecutiveExecutionDashboard 
              plan={generatedPlan.alternatives ? generatedPlan.alternatives[approvedAltIndex] : generatedPlan} 
              requestDir={requestDir} 
              altIndex={approvedAltIndex}
              onBack={() => setViewMode('planning')} 
            />
          ) : viewMode === 'planning' && generatedPlan ? (
            <div className="flex-1 flex overflow-hidden">
              {/* Left Panel: Chat Interface */}
              <div className="w-[350px] shrink-0 border-r border-border/50 shadow-xl z-10 hidden md:block">
                <AgentChat 
                  messages={chatMessages} 
                  isSubmitting={isSubmitting} 
                  onSendMessage={handleChatSendMessage} 
                />
              </div>
              
              {/* Right Panel: Artifact Canvas */}
              <div className="flex-1 overflow-hidden relative">
                {isSubmitting && (
                  <div className="absolute inset-0 z-20 bg-background/50 backdrop-blur-[2px] flex flex-col items-center justify-center animate-in fade-in">
                  </div>
                )}
                <ArtifactCanvas 
                  plan={generatedPlan} 
                  onApprove={handleApprovePlan}
                  onReject={handleRejectPlan}
                />
              </div>
            </div>
          ) : (
            <div className="flex-1 p-8 overflow-y-auto pb-32">
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
          )}
        </main>
      </div>
    </>
  );
}
