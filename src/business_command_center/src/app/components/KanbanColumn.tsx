// src/business_command_center/src/app/components/KanbanColumn.tsx
'use client';

import { SortableContext } from '@dnd-kit/sortable';
import KanbanCard from './KanbanCard';
import { useDroppable } from '@dnd-kit/core';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
};

type KanbanColumnProps = {
  id: string;
  title: string;
  tasks: Task[];
};

const KanbanColumn: React.FC<KanbanColumnProps> = ({ id, title, tasks }) => {
    const { setNodeRef } = useDroppable({ id });
  
    return (
      <div className="bg-slate-900 rounded-lg flex flex-col">
        <div className="p-4 border-b border-slate-800">
          <h2 className="text-lg font-semibold">{title}</h2>
        </div>
        <SortableContext id={id} items={tasks}>
          <div ref={setNodeRef} className="p-4 flex-1">
            {tasks.map(task => (
              <KanbanCard key={task.id} task={task} />
            ))}
          </div>
        </SortableContext>
      </div>
    );
  };
  
  export default KanbanColumn;
