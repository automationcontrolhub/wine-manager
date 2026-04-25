import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Plus, Wine, Trash2, Droplets } from 'lucide-react';
import Modal from '../components/Modal';
import {
  famiglie as famiglieApi,
  tipologieVino,
  tipoCartone, tipoTappo, tipoBottiglia,
  tipoEtichetta, tipoCapsula, tipoCestello,
} from '../api/client';

export default function TipologieVino() {
  const [tipologie, setTipologie] = useState([]);
  const [famiglieList, setFamiglieList] = useState([]);
  const [materiali, setMateriali] = useState({});
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [showFamigliaModal, setShowFamigliaModal] = useState(false);

  // Form nuova tipologia
  const [form, setForm] = useState({
    nome: '', famiglia: '', quantita_litri: 0,
    tipo_cartone: '', tipo_tappo: '', tipo_bottiglia: '',
    tipo_etichetta: '', tipo_capsula: '', tipo_cestello: '',
  });

  // Form nuova famiglia
  const [famigliaForm, setFamigliaForm] = useState({ nome: '', is_spumante: false });

  const loadAll = async () => {
    setLoading(true);
    try {
      const [tip, fam, cart, tap, bot, eti, cap, ces] = await Promise.all([
        tipologieVino.list(),
        famiglieApi.list(),
        tipoCartone.list(),
        tipoTappo.list(),
        tipoBottiglia.list(),
        tipoEtichetta.list(),
        tipoCapsula.list(),
        tipoCestello.list(),
      ]);
      setTipologie(Array.isArray(tip) ? tip : tip.results || []);
      setFamiglieList(Array.isArray(fam) ? fam : fam.results || []);
      setMateriali({
        cartoni: Array.isArray(cart) ? cart : [],
        tappi: Array.isArray(tap) ? tap : [],
        bottiglie: Array.isArray(bot) ? bot : [],
        etichette: Array.isArray(eti) ? eti : [],
        capsule: Array.isArray(cap) ? cap : [],
        cestelli: Array.isArray(ces) ? ces : [],
      });
    } catch (e) {
      toast.error('Errore nel caricamento');
    }
    setLoading(false);
  };

  useEffect(() => { loadAll(); }, []);

  const selectedFamiglia = famiglieList.find(f => f.id === Number(form.famiglia));
  const isSpumante = selectedFamiglia?.is_spumante || false;

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      await tipologieVino.create({
        nome: form.nome,
        famiglia: Number(form.famiglia),
        quantita_litri: parseFloat(form.quantita_litri) || 0,
        tipo_cartone: Number(form.tipo_cartone),
        tipo_tappo: Number(form.tipo_tappo),
        tipo_bottiglia: Number(form.tipo_bottiglia),
        tipo_etichetta: Number(form.tipo_etichetta),
        tipo_capsula: Number(form.tipo_capsula),
        tipo_cestello: isSpumante ? Number(form.tipo_cestello) || null : null,
      });
      toast.success('Tipologia creata!');
      setShowModal(false);
      setForm({ nome: '', famiglia: '', quantita_litri: 0, tipo_cartone: '', tipo_tappo: '', tipo_bottiglia: '', tipo_etichetta: '', tipo_capsula: '', tipo_cestello: '' });
      loadAll();
    } catch (e) {
      const msg = e.response?.data;
      toast.error(typeof msg === 'string' ? msg : JSON.stringify(msg) || 'Errore');
    }
  };

  const handleFamigliaSubmit = async (e) => {
    e.preventDefault();
    try {
      await famiglieApi.create(famigliaForm);
      toast.success('Famiglia creata!');
      setShowFamigliaModal(false);
      setFamigliaForm({ nome: '', is_spumante: false });
      loadAll();
    } catch (e) {
      toast.error('Errore nella creazione famiglia');
    }
  };

  const handleDelete = async (id) => {
    if (!confirm('Eliminare questa tipologia?')) return;
    try {
      await tipologieVino.delete(id);
      toast.success('Eliminata');
      loadAll();
    } catch (e) {
      toast.error('Impossibile eliminare: potrebbe essere in uso');
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  // Raggruppa per famiglia
  const grouped = {};
  tipologie.forEach(t => {
    const fam = t.famiglia_nome || 'Senza famiglia';
    if (!grouped[fam]) grouped[fam] = [];
    grouped[fam].push(t);
  });

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="page-title">Tipologie Vino</h1>
          <p className="text-bark-500">Gestisci le tipologie di vino e i materiali associati</p>
        </div>
        <div className="flex gap-3">
          <button onClick={() => setShowFamigliaModal(true)} className="btn-secondary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuova Famiglia
          </button>
          <button onClick={() => setShowModal(true)} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuova Tipologia
          </button>
        </div>
      </div>

      {Object.keys(grouped).length === 0 ? (
        <div className="card text-center py-12">
          <Wine className="w-12 h-12 text-bark-300 mx-auto mb-3" />
          <p className="text-bark-500">Nessuna tipologia di vino configurata.</p>
          <p className="text-bark-400 text-sm mt-1">Crea prima le famiglie e poi aggiungi le tipologie.</p>
        </div>
      ) : (
        Object.entries(grouped).map(([fam, items]) => (
          <div key={fam} className="card animate-fade-in">
            <h2 className="section-title flex items-center gap-2">
              <Wine className="w-5 h-5 text-wine-600" />
              {fam}
              {items[0]?.famiglia_is_spumante && (
                <span className="badge-wine ml-2">Spumante</span>
              )}
            </h2>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-bark-100">
                    <th className="table-header">Nome</th>
                    <th className="table-header">Silos (L)</th>
                    <th className="table-header">Bottiglia</th>
                    <th className="table-header">Tappo</th>
                    <th className="table-header">Etichetta</th>
                    <th className="table-header">Capsula</th>
                    <th className="table-header">Cartone</th>
                    {items[0]?.famiglia_is_spumante && <th className="table-header">Cestello</th>}
                    <th className="table-header w-16"></th>
                  </tr>
                </thead>
                <tbody>
                  {items.map(t => (
                    <tr key={t.id} className="border-b border-bark-50 hover:bg-bark-50/50 transition-colors">
                      <td className="table-cell font-semibold text-bark-900">{t.nome}</td>
                      <td className="table-cell">
                        <span className="flex items-center gap-1">
                          <Droplets className="w-3.5 h-3.5 text-wine-500" />
                          {parseFloat(t.quantita_litri).toLocaleString('it-IT')}
                        </span>
                      </td>
                      <td className="table-cell text-bark-600">{t.tipo_bottiglia_nome}</td>
                      <td className="table-cell text-bark-600">{t.tipo_tappo_nome}</td>
                      <td className="table-cell text-bark-600">{t.tipo_etichetta_nome}</td>
                      <td className="table-cell text-bark-600">{t.tipo_capsula_nome}</td>
                      <td className="table-cell text-bark-600">{t.tipo_cartone_nome}</td>
                      {t.famiglia_is_spumante && (
                        <td className="table-cell text-bark-600">{t.tipo_cestello_nome || '—'}</td>
                      )}
                      <td className="table-cell">
                        <button onClick={() => handleDelete(t.id)}
                          className="p-1.5 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors">
                          <Trash2 className="w-4 h-4" />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        ))
      )}

      {/* Modal Nuova Tipologia */}
      <Modal open={showModal} onClose={() => setShowModal(false)} title="Nuova Tipologia di Vino" wide>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Famiglia</label>
              <select className="select-field" required value={form.famiglia}
                onChange={e => setForm({...form, famiglia: e.target.value})}>
                <option value="">Seleziona...</option>
                {famiglieList.map(f => (
                  <option key={f.id} value={f.id}>
                    {f.nome} {f.is_spumante ? '(Spumante)' : ''}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Nome tipologia</label>
              <input className="input-field" required placeholder="es: Rosso, Brut Nature..."
                value={form.nome} onChange={e => setForm({...form, nome: e.target.value})} />
            </div>
          </div>

          <div>
            <label className="label">Quantità iniziale nel silos (litri)</label>
            <input type="number" step="0.01" min="0" className="input-field"
              value={form.quantita_litri} onChange={e => setForm({...form, quantita_litri: e.target.value})} />
          </div>

          <hr className="border-bark-100" />
          <p className="text-sm font-semibold text-bark-600 uppercase tracking-wider">Materiali associati</p>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="label">Tipo bottiglia</label>
              <select className="select-field" required value={form.tipo_bottiglia}
                onChange={e => setForm({...form, tipo_bottiglia: e.target.value})}>
                <option value="">Seleziona...</option>
                {(materiali.bottiglie || []).map(b => (
                  <option key={b.id} value={b.id}>{b.nome} ({b.capacita_litri}L)</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Tipo tappo</label>
              <select className="select-field" required value={form.tipo_tappo}
                onChange={e => setForm({...form, tipo_tappo: e.target.value})}>
                <option value="">Seleziona...</option>
                {(materiali.tappi || []).map(t => (
                  <option key={t.id} value={t.id}>{t.nome}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Tipo etichetta</label>
              <select className="select-field" required value={form.tipo_etichetta}
                onChange={e => setForm({...form, tipo_etichetta: e.target.value})}>
                <option value="">Seleziona...</option>
                {(materiali.etichette || []).map(e2 => (
                  <option key={e2.id} value={e2.id}>{e2.nome}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Tipo capsula</label>
              <select className="select-field" required value={form.tipo_capsula}
                onChange={e => setForm({...form, tipo_capsula: e.target.value})}>
                <option value="">Seleziona...</option>
                {(materiali.capsule || []).map(c => (
                  <option key={c.id} value={c.id}>{c.nome}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="label">Tipo cartone</label>
              <select className="select-field" required value={form.tipo_cartone}
                onChange={e => setForm({...form, tipo_cartone: e.target.value})}>
                <option value="">Seleziona...</option>
                {(materiali.cartoni || []).map(c => (
                  <option key={c.id} value={c.id}>{c.nome} ({c.capacita_bottiglie} bott.)</option>
                ))}
              </select>
            </div>
            {isSpumante && (
              <div>
                <label className="label">Tipo cestello</label>
                <select className="select-field" value={form.tipo_cestello}
                  onChange={e => setForm({...form, tipo_cestello: e.target.value})}>
                  <option value="">Seleziona...</option>
                  {(materiali.cestelli || []).map(c => (
                    <option key={c.id} value={c.id}>{c.nome}</option>
                  ))}
                </select>
              </div>
            )}
          </div>

          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Annulla</button>
            <button type="submit" className="btn-primary">Crea Tipologia</button>
          </div>
        </form>
      </Modal>

      {/* Modal Nuova Famiglia */}
      <Modal open={showFamigliaModal} onClose={() => setShowFamigliaModal(false)} title="Nuova Famiglia">
        <form onSubmit={handleFamigliaSubmit} className="space-y-4">
          <div>
            <label className="label">Nome famiglia</label>
            <input className="input-field" required placeholder="es: Etna DOC, Contrade..."
              value={famigliaForm.nome} onChange={e => setFamigliaForm({...famigliaForm, nome: e.target.value})} />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="w-5 h-5 rounded border-bark-300 text-wine-600 focus:ring-wine-500"
              checked={famigliaForm.is_spumante}
              onChange={e => setFamigliaForm({...famigliaForm, is_spumante: e.target.checked})} />
            <span className="text-sm text-bark-800 font-medium">È uno spumante (richiede cestello)</span>
          </label>
          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowFamigliaModal(false)} className="btn-secondary">Annulla</button>
            <button type="submit" className="btn-primary">Crea Famiglia</button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
