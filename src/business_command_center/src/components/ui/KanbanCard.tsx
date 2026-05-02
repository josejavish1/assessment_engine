// src/business_command_center/src/components/ui/KanbanCard.tsx
import React from 'react';

interface KanbanCardProps {
  title: string;
  status?: string;
}

const KanbanCard: React.FC<KanbanCardProps> = ({ title, status }) => {
  return (
    <div className="bg-gray-800 p-4 rounded-lg shadow-md mb-4 cursor-grab">
      <h4 className="font-bold text-white">{title}</h4>
      {status && (
        <div className="flex items-center mt-2">
          <span className="bg-blue-600 text-white text-xs font-semibold mr-2 px-2.5 py-0.5 rounded-full">
            {status}
          </span>
        </div>
      )}
    </div>
  );
};

export default KanbanCard;
