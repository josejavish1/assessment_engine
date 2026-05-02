// src/business_command_center/src/app/components/KanbanCard.tsx
import React from 'react';

type Task = {
  id: string;
  title: string;
  description: string;
  status?: string;
};

type KanbanCardProps = {
  task: Task;
};

const KanbanCard: React.FC<KanbanCardProps> = ({ task }) => {
  return (
    <div
      className="bg-gray-800 border border-gray-700 rounded-lg p-4 mb-4 cursor-grab shadow-sm hover:shadow-md transition-shadow duration-200"
    >
        <div className="flex justify-between items-start">
            <h4 className="font-semibold text-white mb-2">{task.title}</h4>
        </div>
      
      {task.status && (
        <div className="flex items-center text-xs text-yellow-400 mt-2">
          <svg className="animate-spin h-4 w-4 mr-2 text-yellow-400" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
            <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
            <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {task.status}
        </div>
      )}
    </div>
  );
};

export default KanbanCard;
