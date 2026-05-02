// src/business_command_center/src/app/components/KanbanColumn.tsx
'use client';

import React from 'react';

type KanbanColumnProps = {
  id: string;
  title: string;
  children: React.ReactNode;
};

const KanbanColumn: React.FC<KanbanColumnProps> = ({ id, title, children }) => {
  return (
    <div className="bg-slate-900 rounded-lg flex flex-col">
      <div className="p-4 border-b border-slate-800">
        <h2 className="text-lg font-semibold">{title}</h2>
      </div>
      <div className="p-4 flex-1">
        {children}
      </div>
    </div>
  );
};

export default KanbanColumn;
