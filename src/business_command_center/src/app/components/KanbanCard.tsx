
import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Loader2, GripVertical } from 'lucide-react';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
};

type KanbanCardProps = {
  task: Task;
  onDelete: (id: string) => void;
  onEdit: (task: Task) => void;
};

const KanbanCard: React.FC<KanbanCardProps> = ({ task, onDelete, onEdit }) => {
  return (
    <Card className="mb-3 cursor-grab active:cursor-grabbing hover:border-slate-400 transition-colors bg-slate-900 border-slate-700 text-slate-100 group">
      <CardHeader className="p-4 pb-2 flex flex-row items-start justify-between space-y-0">
        <CardTitle className="text-sm font-medium leading-none">
          {task.title}
        </CardTitle>
        <GripVertical className="h-4 w-4 text-slate-500 opacity-0 group-hover:opacity-100 transition-opacity" />
      </CardHeader>
      <CardContent className="p-4 pt-2">
        <p className="text-xs text-slate-400 line-clamp-2 mb-3">
          {task.description}
        </p>
        
        {task.status && (
          <Badge variant="outline" className="bg-amber-500/10 text-amber-500 border-amber-500/20 text-xs flex w-fit items-center gap-1">
            <Loader2 className="h-3 w-3 animate-spin" />
            {task.status}
          </Badge>
        )}
      </CardContent>
    </Card>
  );
};

export default KanbanCard;
