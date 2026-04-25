import React from 'react';
import { X } from 'lucide-react';

export default function Modal({ open, onClose, title, children, wide }) {
  if (!open) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-bark-950/40 backdrop-blur-sm" onClick={onClose} />
      <div className={`relative bg-white rounded-2xl shadow-2xl animate-fade-in
        ${wide ? 'w-full max-w-2xl' : 'w-full max-w-lg'} max-h-[90vh] flex flex-col`}>
        <div className="flex items-center justify-between px-6 py-4 border-b border-bark-100">
          <h3 className="font-display text-xl font-semibold text-bark-900">{title}</h3>
          <button onClick={onClose} className="p-1.5 rounded-lg hover:bg-bark-100 transition-colors">
            <X className="w-5 h-5 text-bark-500" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
