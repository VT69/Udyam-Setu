import React from 'react';
import { Search } from 'lucide-react';

export default function EmptyState({ icon: Icon = Search, title, description, action }) {
  return (
    <div className="flex flex-col items-center justify-center p-12 text-center border border-dashed border-steel-dark rounded-xl bg-navy-light/30">
      <div className="p-4 rounded-full bg-navy-light mb-4 text-steel-light">
        <Icon size={32} />
      </div>
      <h3 className="text-lg font-sora font-semibold text-white mb-2">{title}</h3>
      <p className="text-steel-light max-w-sm mb-6">{description}</p>
      {action && <div>{action}</div>}
    </div>
  );
}
