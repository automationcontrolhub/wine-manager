import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, Trash2, Settings, Package, Hexagon, Circle, Tag, ShieldCheck, Grape, Edit3 } from 'lucide-react';
import Modal from '../components/Modal';
import { useConfirm } from '../components/ConfirmDialog';
import {
  tipoCartone, tipoTappo, tipoBottiglia,
  tipoEtichetta, tipoCapsula, tipoCestello,
} from '../api/client';

const SEZIONI = [
  {
    key: 'cartone', label: 'Cartoni', icon: Package, api: tipoCartone,
    campi: [
      { name: 'nome', label: 'Nome', type: 'text', required: true },
      { name: 'capacita_bottiglie', label: 'Capacità (n° bottiglie)', type: 'number', required: true },
    ],
    colonne: ['nome', 'capacita_bottiglie', 'quantita'],
    colonneLabel: ['Nome', 'Capacità', 'Scorta'],
  },
  {
    key: 'tappo', label: 'Tappi', icon: Hexagon, api: tipoTappo,
    campi: [{ name: 'nome', label: 'Nome', type: 'text', required: true }],
    colonne: ['nome', 'quantita'],
    colonneLabel: ['Nome', 'Scorta'],
  },
  {
    key: 'bottiglia', label: 'Bottiglie', icon: Circle, api: tipoBottiglia,
    campi: [
      { name: 'nome', label: 'Nome', type: 'text', required: true },
      { name: 'capacita_litri', label: 'Capacità (litri)', type: 'number', step: '0.01', required: true },
    ],
    colonne: ['nome', 'capacita_litri', 'quantita'],
    colonneLabel: ['Nome', 'Capacità (L)', 'Scorta'],
  },
  {
    key: 'etichetta', label: 'Etichette', icon: Tag, api: tipoEtichetta,
    campi: [{ name: 'nome', label: 'Nome', type: 'text', required: true }],
    colonne: ['nome', 'quantita'],
    colonneLabel: ['Nome', 'Scorta'],
  },
  {
    key: 'capsula', label: 'Capsule', icon: ShieldCheck, api: tipoCapsula,
    campi: [{ name: 'nome', label: 'Nome', type: 'text', required: true }],
    colonne: ['nome', 'quantita'],
    colonneLabel: ['Nome', 'Scorta'],
  },
  {
    key: 'cestello', label: 'Cestelli', icon: Grape, api: tipoCestello,
    campi: [{ name: 'nome', label: 'Nome', type: 'text', required: true }],
    colonne: ['nome', 'quantita'],
    colonneLabel: ['Nome', 'Scorta'],
  },
];

export default function Configurazione() {
  const confirm = useConfirm();
  const [data, setData] = useState({});
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('cartone');
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({});
  const [editingId, setEditingId] = useState(null);

  const loadAll = async () => {
    setLoading(true);
    const results = {};
    for (const sez of SEZIONI) {
      try {
        const res = await sez.api.list();
        results[sez.key] = Array.isArray(res) ? res : [];
      } catch {
        results[sez.key] = [];
      }
    }
    setData(results);
    setLoading(false);
  };

  useEffect(() => { loadAll(); }, []);

  const currentSection = SEZIONI.find(s => s.key === activeTab);

  const openCreate = () => {
    setEditingId(null);
    setForm({});
    setShowModal(true);
  };

  const openEdit = (item) => {
    setEditingId(item.id);
    const initialForm = {};
    currentSection.campi.forEach(c => {
      initialForm[c.name] = item[c.name];
    });
    setForm(initialForm);
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      if (editingId) {
        await currentSection.api.update(editingId, form);
        toast.success(`${currentSection.label.slice(0, -1)} aggiornato!`);
      } else {
        await currentSection.api.create(form);
        toast.success(`${currentSection.label.slice(0, -1)} creato!`);
      }
      setShowModal(false);
      setForm({});
      setEditingId(null);
      loadAll();
    } catch (e) {
      const msg = e.response?.data;
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg) || 'Errore');
    }
  };

  const handleDelete = async (item) => {
    const ok = await confirm({
      title: 'Conferma eliminazione',
      message: `Stai per eliminare "${item.nome}". Questa azione non può essere annullata.\n\nNota: l'eliminazione fallirà se è in uso da una tipologia di vino.`,
      confirmLabel: 'Elimina',
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await currentSection.api.delete(item.id);
      toast.success('Eliminato!');
      loadAll();
    } catch (e) {
      toast.error('Impossibile eliminare: potrebbe essere in uso da una tipologia di vino.');
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  const items = data[activeTab] || [];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title flex items-center gap-3">
          <Settings className="w-8 h-8 text-bark-400" />
          Configurazione
        </h1>
        <p className="text-bark-500">Gestisci le tipologie di materiali</p>
      </div>

      <div className="flex gap-1 bg-bark-100 rounded-xl p-1 flex-wrap">
        {SEZIONI.map(sez => {
          const Icon = sez.icon;
          return (
            <button
              key={sez.key}
              onClick={() => setActiveTab(sez.key)}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200
                ${activeTab === sez.key
                  ? 'bg-white text-bark-900 shadow-sm'
                  : 'text-bark-500 hover:text-bark-700'
                }`}
            >
              <Icon className="w-4 h-4" />
              {sez.label}
              <span className={`text-xs px-1.5 py-0.5 rounded-full ${
                activeTab === sez.key ? 'bg-bark-100 text-bark-600' : 'bg-bark-200/50 text-bark-400'
              }`}>
                {(data[sez.key] || []).length}
              </span>
            </button>
          );
        })}
      </div>

      <div className="card animate-fade-in">
        <div className="flex items-center justify-between mb-4">
          <h2 className="section-title mb-0 flex items-center gap-2">
            {React.createElement(currentSection.icon, { className: 'w-5 h-5 text-wine-600' })}
            {currentSection.label}
          </h2>
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Aggiungi
          </button>
        </div>

        {items.length === 0 ? (
          <div className="text-center py-8">
            {React.createElement(currentSection.icon, { className: 'w-12 h-12 text-bark-300 mx-auto mb-3' })}
            <p className="text-bark-500">Nessun tipo di {currentSection.label.toLowerCase()} configurato.</p>
            <p className="text-bark-400 text-sm mt-1">Clicca "Aggiungi" per crearne uno.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  {currentSection.colonneLabel.map((col, i) => (
                    <th key={i} className="table-header">{col}</th>
                  ))}
                  <th className="table-header w-24">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {items.map(item => (
                  <tr key={item.id} className="border-b border-bark-50 hover:bg-bark-50/50 transition-colors">
                    {currentSection.colonne.map((col, i) => (
                      <td key={i} className={`table-cell ${
                        col === 'quantita' ? 'font-semibold' :
                        col === 'nome' ? 'font-semibold text-bark-900' : ''
                      }`}>
                        {col === 'quantita' ? (
                          <span className={item[col] > 0 ? 'text-olive-700' : 'text-red-500'}>
                            {item[col]?.toLocaleString('it-IT')}
                          </span>
                        ) : (
                          item[col]
                        )}
                      </td>
                    ))}
                    <td className="table-cell">
                      <div className="flex gap-1">
                        <button onClick={() => openEdit(item)}
                          className="p-1.5 rounded-lg hover:bg-wine-50 text-bark-400 hover:text-wine-600 transition-colors"
                          title="Modifica">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        <button onClick={() => handleDelete(item)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors"
                          title="Elimina">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <Modal open={showModal} onClose={() => setShowModal(false)}
        title={editingId
          ? `Modifica ${currentSection?.label.toLowerCase().slice(0, -1) || ''}`
          : `Nuovo tipo di ${currentSection?.label.toLowerCase().slice(0, -1) || ''}`}>
        <form onSubmit={handleSubmit} className="space-y-4">
          {currentSection?.campi.map(campo => (
            <div key={campo.name}>
              <label className="label">{campo.label}</label>
              <input
                type={campo.type}
                step={campo.step}
                required={campo.required}
                className="input-field"
                placeholder={campo.label}
                value={form[campo.name] ?? ''}
                onChange={e => setForm({...form, [campo.name]: e.target.value})}
              />
            </div>
          ))}
          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Annulla</button>
            <button type="submit" className="btn-primary">
              {editingId ? 'Salva Modifiche' : 'Crea'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
