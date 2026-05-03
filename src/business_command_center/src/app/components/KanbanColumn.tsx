// src/business_command_center/src/app/components/KanbanColumn.tsx
'use client';

import React from 'react';

type KanbanColumnProps = {
  id: string;
  title: string;
  children: React.ReactNode;
};

const KanbanColumn: React.FC<KanbanColumnProps> = ({ id, title, children }) => {
  const hasChildren = React.Children.count(children) > 0;

  return (
    <div className="bg-muted/30 border border-border/50 rounded-lg flex flex-col h-full overflow-hidden">
      <div className="p-4 border-b border-border/50 bg-muted/20">
        <h2 className="text-sm font-semibold text-foreground tracking-tight flex items-center justify-between">
          {title}
          <span className="bg-background border border-border/50 text-muted-foreground text-xs px-2 py-0.5 rounded-full">
            {React.Children.count(children)}
          </span>
        </h2>
      </div>
      <div className="p-4 flex-1 overflow-y-auto">
        {hasChildren ? (
          children
        ) : (
          <div className="h-full min-h-[100px] flex items-center justify-center border-2 border-dashed border-border/50 rounded-lg">
            <span className="text-xs text-muted-foreground/70 font-medium">Arrastra tareas aquí</span>
          </div>
        )}
      </div>
    </div>
  );
};

export default KanbanColumn;
