
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, GripVertical } from 'lucide-react';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
  agentic_state?: 'thinking' | 'coding' | 'testing' | 'done';
};

type KanbanCardProps = {
  task: Task;
  onDelete?: (id: string) => void;
  onEdit?: (task: Task) => void;
  onClick?: (task: Task) => void;
};

const KanbanCard: React.FC<KanbanCardProps> = ({ task, onClick }) => {
  const isThinking = task.agentic_state === 'thinking';
  
  return (
    <Card 
      onClick={() => onClick && onClick(task)}
      className={`mb-3 cursor-grab active:cursor-grabbing transition-colors bg-slate-900 text-slate-100 group
        ${isThinking ? 'border-transparent bg-[length:200%_100%] animate-shimmer bg-gradient-to-r from-slate-800 via-blue-500/20 to-slate-800' : 'border-slate-700 hover:border-slate-400'}
      `}
    >
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0 pointer-events-none">
        <CardTitle className="text-sm font-medium leading-none">
          {task.title}
        </CardTitle>
        <GripVertical className="h-4 w-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-auto" />
      </CardHeader>
      <CardContent className="p-4 pt-2 pointer-events-none">
        <p className="text-xs text-slate-400 line-clamp-2 mb-3">
          {task.description}
        </p>
        
        {task.status && (
          <Badge variant="outline" className={`${isThinking ? 'bg-blue-500/10 text-blue-400 border-blue-500/20' : 'bg-amber-500/10 text-amber-500 border-amber-500/20'} text-xs flex w-fit items-center gap-1`}>
            {isThinking ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
            {task.status}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
};

export default KanbanCard;
