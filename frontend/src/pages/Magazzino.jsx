import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, Package, Wine, ArrowUpCircle } from 'lucide-react';
import Modal from '../components/Modal';
import {
  tipoCartone, tipoTappo, tipoBottiglia,
  tipoEtichetta, tipoCapsula, tipoCestello,
  tipologieVino, caricoMagazzino, aggiuntaVino,
} from '../api/client';

const CATEGORIE = [
  { key: 'cartone', label: 'Cartoni', api: tipoCartone, fields: ['nome', 'capacita_bottiglie', 'quantita'] },
  { key: 'tappo', label: 'Tappi', api: tipoTappo, fields: ['nome', 'quantita'] },
  { key: 'bottiglia', label: 'Bottiglie', api: tipoBottiglia, fields: ['nome', 'capacita_litri', 'quantita'] },
  { key: 'etichetta', label: 'Etichette', api: tipoEtichetta, fields: ['nome', 'quantita'] },
  { key: 'capsula', label: 'Capsule', api: tipoCapsula, fields: ['nome', 'quantita'] },
  { key: 'cestello', label: 'Cestelli', api: tipoCestello, fields: ['nome', 'quantita'] },
];

export default function Magazzino() {
  const [data, setData] = useState({});
  const [tipologie, setTipologie] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showCarico, setShowCarico] = useState(false);
  const [showVinoModal, setShowVinoModal] = useState(false);
  const [caricoForm, setCaricoForm] = useState({ categoria: '', tipo_id: '', quantita: '' });
  const [vinoForm, setVinoForm] = useState({ tipologia_vino_id: '', litri: '' });
  const [activeTab, setActiveTab] = useState('cartone');

  const loadAll = async () => {
    setLoading(true);
    try {
      const results = {};
      for (const cat of CATEGORIE) {
        const res = await cat.api.list();
        results[cat.key] = Array.isArray(res) ? res : [];
      }
      setData(results);
      const tip = await tipologieVino.list();
      setTipologie(Array.isArray(tip) ? tip : tip.results || []);
    } catch (e) {
      toast.error('Errore nel caricamento');
    }
    setLoading(false);
  };

  useEffect(() => { loadAll(); }, []);

  const handleCarico = async (e) => {
    e.preventDefault();
    try {
      await caricoMagazzino({
        categoria: caricoForm.categoria,
        tipo_id: Number(caricoForm.tipo_id),
        quantita: Number(caricoForm.quantita),
      });
      toast.success('Carico registrato!');
      setShowCarico(false);
      setCaricoForm({ categoria: '', tipo_id: '', quantita: '' });
      loadAll();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Errore');
    }
  };

  const handleAggiuntaVino = async (e) => {
    e.preventDefault();
    try {
      await aggiuntaVino({
        tipologia_vino_id: Number(vinoForm.tipologia_vino_id),
        litri: parseFloat(vinoForm.litri),
      });
      toast.success('Vino aggiunto al silos!');
      setShowVinoModal(false);
      setVinoForm({ tipologia_vino_id: '', litri: '' });
      loadAll();
    } catch (e) {
      toast.error(e.response?.data?.error || 'Errore');
    }
  };

  const catObj = CATEGORIE.find(c => c.key === caricoForm.categoria);
  const itemsForCarico = catObj ? (data[catObj.key] || []) : [];

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Magazzino</h1>
          <p className="text-bark-500">Gestisci le scorte di materiali e vino</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowVinoModal(true)} className="btn-secondary flex items-center gap-2">
            <Wine className="w-4 h-4" /> Aggiungi Vino
          </button>
          <button onClick={() => setShowCarico(true)} className="btn-primary flex items-center gap-2">
            <ArrowUpCircle className="w-4 h-4" /> Carico Materiale
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-bark-100 rounded-xl p-1">
        {CATEGORIE.map(cat => (
          <button
            key={cat.key}
            onClick={() => setActiveTab(cat.key)}
            className={`flex-1 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200
              ${activeTab === cat.key
                ? 'bg-white text-bark-900 shadow-sm'
                : 'text-bark-500 hover:text-bark-700'
              }`}
          >
            {cat.label}
          </button>
        ))}
      </div>

      {/* Contenuto tab attivo */}
      {CATEGORIE.filter(c => c.key === activeTab).map(cat => (
        <div key={cat.key} className="card animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0">{cat.label} in magazzino</h2>
          </div>
          {(data[cat.key] || []).length === 0 ? (
            <p className="text-bark-400 text-sm py-4">
              Nessun tipo di {cat.label.toLowerCase()} configurato. Vai in Configurazione per crearne.
            </p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-bark-100">
                    <th className="table-header">Nome</th>
                    {cat.key === 'cartone' && <th className="table-header">Capacità</th>}
                    {cat.key === 'bottiglia' && <th className="table-header">Capacità (L)</th>}
                    <th className="table-header text-right">Quantità</th>
                  </tr>
                </thead>
                <tbody>
                  {(data[cat.key] || []).map(item => (
                    <tr key={item.id} className="border-b border-bark-50 hover:bg-bark-50/50">
                      <td className="table-cell font-semibold">{item.nome}</td>
                      {cat.key === 'cartone' && (
                        <td className="table-cell text-bark-600">{item.capacita_bottiglie} bott.</td>
                      )}
                      {cat.key === 'bottiglia' && (
                        <td className="table-cell text-bark-600">{item.capacita_litri} L</td>
                      )}
                      <td className="table-cell text-right">
                        <span className={`text-lg font-display font-bold ${
                          item.quantita > 0 ? 'text-olive-700' : 'text-red-500'
                        }`}>
                          {item.quantita.toLocaleString('it-IT')}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ))}

      {/* Silos vino */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <Wine className="w-5 h-5 text-wine-600" /> Silos Vino
        </h2>
        {tipologie.length === 0 ? (
          <p className="text-bark-400 text-sm">Nessuna tipologia configurata.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {tipologie.map(t => (
              <div key={t.id} className="flex items-center justify-between p-4 rounded-xl bg-bark-50 border border-bark-100">
                <div>
                  <p className="font-semibold text-bark-900">{t.nome}</p>
                  <p className="text-xs text-bark-500">{t.famiglia_nome}</p>
                </div>
                <span className="text-lg font-display font-bold text-wine-700">
                  {parseFloat(t.quantita_litri).toLocaleString('it-IT')} L
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Modal Carico Materiale */}
      <Modal open={showCarico} onClose={() => setShowCarico(false)} title="Carico Materiale">
        <form onSubmit={handleCarico} className="space-y-4">
          <div>
            <label className="label">Categoria</label>
            <select className="select-field" required value={caricoForm.categoria}
              onChange={e => setCaricoForm({...caricoForm, categoria: e.target.value, tipo_id: ''})}>
              <option value="">Seleziona...</option>
              {CATEGORIE.map(c => (
                <option key={c.key} value={c.key}>{c.label}</option>
              ))}
            </select>
          </div>
          {caricoForm.categoria && (
            <div>
              <label className="label">Tipo</label>
              <select className="select-field" required value={caricoForm.tipo_id}
                onChange={e => setCaricoForm({...caricoForm, tipo_id: e.target.value})}>
                <option value="">Seleziona...</option>
                {itemsForCarico.map(item => (
                  <option key={item.id} value={item.id}>{item.nome}</option>
                ))}
              </select>
            </div>
          )}
          <div>
            <label className="label">Quantità</label>
            <input type="number" min="1" className="input-field" required
              value={caricoForm.quantita}
              onChange={e => setCaricoForm({...caricoForm, quantita: e.target.value})} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowCarico(false)} className="btn-secondary">Annulla</button>
            <button type="submit" className="btn-primary">Registra Carico</button>
          </div>
        </form>
      </Modal>

      {/* Modal Aggiunta Vino */}
      <Modal open={showVinoModal} onClose={() => setShowVinoModal(false)} title="Aggiungi Vino al Silos">
        <form onSubmit={handleAggiuntaVino} className="space-y-4">
          <div>
            <label className="label">Tipologia vino</label>
            <select className="select-field" required value={vinoForm.tipologia_vino_id}
              onChange={e => setVinoForm({...vinoForm, tipologia_vino_id: e.target.value})}>
              <option value="">Seleziona...</option>
              {tipologie.map(t => (
                <option key={t.id} value={t.id}>{t.famiglia_nome} — {t.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Litri da aggiungere</label>
            <input type="number" step="0.01" min="0.01" className="input-field" required
              value={vinoForm.litri}
              onChange={e => setVinoForm({...vinoForm, litri: e.target.value})} />
          </div>
          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowVinoModal(false)} className="btn-secondary">Annulla</button>
            <button type="submit" className="btn-success">Aggiungi Vino</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
