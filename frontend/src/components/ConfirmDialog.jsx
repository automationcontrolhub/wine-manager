import React, { createContext, useContext, useState, useCallback } from 'react';
import { AlertTriangle, Info, CheckCircle, X } from 'lucide-react';

const ConfirmContext = createContext(null);

export function ConfirmProvider({ children }) {
  const [state, setState] = useState({
    open: false,
    title: '',
    message: '',
    confirmLabel: 'Conferma',
    cancelLabel: 'Annulla',
    variant: 'danger', // 'danger' | 'warning' | 'info'
    resolve: null,
  });

  const confirm = useCallback((options) => {
    return new Promise((resolve) => {
      setState({
        open: true,
        title: options.title || 'Conferma',
        message: options.message || 'Sei sicuro?',
        confirmLabel: options.confirmLabel || 'Conferma',
        cancelLabel: options.cancelLabel || 'Annulla',
        variant: options.variant || 'danger',
        resolve,
      });
    });
  }, []);

  const handleClose = (result) => {
    if (state.resolve) state.resolve(result);
    setState({ ...state, open: false, resolve: null });
  };

  return (
    <ConfirmContext.Provider value={confirm}>
      {children}
      {state.open && (
        <div className="fixed inset-0 z-[60] flex items-center justify-center p-4 animate-fade-in">
          <div
            className="absolute inset-0 bg-bark-950/50 backdrop-blur-sm"
            onClick={() => handleClose(false)}
          />
          <div className="relative bg-white rounded-2xl shadow-2xl w-full max-w-md overflow-hidden">
            {/* Header colorato in base alla variante */}
            <div className={`px-6 py-4 flex items-start gap-4 ${
              state.variant === 'danger' ? 'bg-red-50 border-b border-red-100' :
              state.variant === 'warning' ? 'bg-amber-50 border-b border-amber-100' :
              'bg-blue-50 border-b border-blue-100'
            }`}>
              <div className={`p-2 rounded-full ${
                state.variant === 'danger' ? 'bg-red-100 text-red-600' :
                state.variant === 'warning' ? 'bg-amber-100 text-amber-600' :
                'bg-blue-100 text-blue-600'
              }`}>
                {state.variant === 'danger' ? <AlertTriangle className="w-5 h-5" /> :
                 state.variant === 'warning' ? <AlertTriangle className="w-5 h-5" /> :
                 <Info className="w-5 h-5" />}
              </div>
              <div className="flex-1 pt-0.5">
                <h3 className="font-display text-lg font-bold text-bark-900">{state.title}</h3>
              </div>
              <button
                onClick={() => handleClose(false)}
                className="p-1 rounded-lg hover:bg-white/60 transition-colors"
              >
                <X className="w-5 h-5 text-bark-400" />
              </button>
            </div>

            {/* Messaggio */}
            <div className="px-6 py-5">
              <p className="text-bark-700 whitespace-pre-line">{state.message}</p>
            </div>

            {/* Pulsanti */}
            <div className="px-6 py-4 bg-bark-50 flex justify-end gap-3 border-t border-bark-100">
              <button
                onClick={() => handleClose(false)}
                className="btn-secondary"
              >
                {state.cancelLabel}
              </button>
              <button
                onClick={() => handleClose(true)}
                className={`px-5 py-2.5 font-semibold rounded-lg transition-all duration-200 shadow-sm hover:shadow-md active:scale-[0.98] text-white ${
                  state.variant === 'danger' ? 'bg-red-600 hover:bg-red-700' :
                  state.variant === 'warning' ? 'bg-amber-500 hover:bg-amber-600' :
                  'bg-blue-600 hover:bg-blue-700'
                }`}
              >
                {state.confirmLabel}
              </button>
            </div>
          </div>
        </div>
      )}
    </ConfirmContext.Provider>
  );
}

export function useConfirm() {
  const ctx = useContext(ConfirmContext);
  if (!ctx) throw new Error('useConfirm deve essere usato dentro ConfirmProvider');
  return ctx;
}
