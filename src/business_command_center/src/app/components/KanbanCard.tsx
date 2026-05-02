
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
      className={`mb-3 cursor-grab active:cursor-grabbing transition-all duration-200 bg-card text-card-foreground group shadow-sm hover:shadow-md
        ${isThinking ? 'border-transparent bg-[length:200%_100%] animate-shimmer bg-gradient-to-r from-card via-primary/10 to-card' : 'border-border/50 hover:border-border'}
      `}
    >
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0 pointer-events-none">
        <CardTitle className="text-sm font-medium leading-tight">
          {task.title}
        </CardTitle>
        <GripVertical className="h-4 w-4 text-muted-foreground/50 group-hover:text-muted-foreground opacity-0 group-hover:opacity-100 transition-all pointer-events-auto" />
      </CardHeader>
      <CardContent className="p-4 pt-2 pointer-events-none">
        <p className="text-xs text-muted-foreground/80 line-clamp-2 mb-3 leading-relaxed">
          {task.description}
        </p>
        
        {task.status && (
          <Badge variant="outline" className={`${isThinking ? 'bg-primary/10 text-primary border-primary/20' : 'bg-secondary text-secondary-foreground border-border/50'} text-[10px] font-medium flex w-fit items-center gap-1.5 px-2 py-0.5 rounded-md`}>
            {isThinking ? <Loader2 className="h-3 w-3 animate-spin" /> : null}
            {task.status}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
};

export default KanbanCard;
