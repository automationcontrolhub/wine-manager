import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import { Package, Tag, CheckCircle, AlertTriangle, Wine, Trash2 } from 'lucide-react';
import Modal from '../components/Modal';
import { useConfirm } from '../components/ConfirmDialog';
import {
  tipologieVino, creaSenzaEtichetta, creaConEtichetta,
  associaEtichetta, getBottiglieSenzaEtichetta, lotti as lottiApi,
  operazioni as operazioniApi,
} from '../api/client';

export default function Imbottigliamento() {
  const confirm = useConfirm();
  const [tipologie, setTipologie] = useState([]);
  const [senzaEtichetta, setSenzaEtichetta] = useState([]);
  const [allLotti, setAllLotti] = useState([]);
  const [allOperazioni, setAllOperazioni] = useState([]);
  const [loading, setLoading] = useState(true);

  const [showSenza, setShowSenza] = useState(false);
  const [showCon, setShowCon] = useState(false);
  const [showAssocia, setShowAssocia] = useState(false);

  const [formSenza, setFormSenza] = useState({ tipologia_vino_id: '', quantita: '', con_capsula: false });
  const [formCon, setFormCon] = useState({ tipologia_vino_id: '', quantita: '', con_capsula: true });
  const [formAssocia, setFormAssocia] = useState({ 
    tipologia_vino_origine_id: '', 
    tipologia_vino_destinazione_id: '',
    quantita: '', 
    con_capsula: false 
  });

  const [submitting, setSubmitting] = useState(false);

  const loadAll = async () => {
    setLoading(true);
    try {
      const [tip, se, lo, op] = await Promise.all([
        tipologieVino.list(),
        getBottiglieSenzaEtichetta(),
        lottiApi.list(),
        operazioniApi.list(),
      ]);
      setTipologie(Array.isArray(tip) ? tip : tip.results || []);
      setSenzaEtichetta(Array.isArray(se) ? se : []);
      setAllLotti(Array.isArray(lo) ? lo : lo.results || []);
      setAllOperazioni(Array.isArray(op) ? op : op.results || []);
    } catch (e) {
      toast.error('Errore nel caricamento');
    }
    setLoading(false);
  };

  useEffect(() => { loadAll(); }, []);

  // Helper: mostra materiali che verranno usati
  const MaterialPreview = ({ tipId, qty, conEtichetta, conCapsula }) => {
    const tip = tipologie.find(t => t.id === Number(tipId));
    if (!tip || !qty) return null;
    const q = Number(qty);
    const cap = tip.tipo_bottiglia_capacita ? parseFloat(tip.tipo_bottiglia_capacita) : 0.75;
    const litri = q * cap;
    // Capacità reale del cartone associato a questa tipologia
    const cartoneCap = tip.tipo_cartone_capacita || 1;
    const cartoniNecessari = Math.ceil(q / cartoneCap);

    return (
      <div className="bg-bark-50 rounded-xl p-4 mt-4 space-y-2 animate-fade-in">
        <p className="text-sm font-bold text-bark-700 uppercase tracking-wider">Riepilogo materiali</p>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="flex justify-between p-2 rounded-lg bg-white">
            <span className="text-bark-600">Vino dal silos</span>
            <span className="font-semibold text-wine-700">{litri.toFixed(1)} L</span>
          </div>
          <div className="flex justify-between p-2 rounded-lg bg-white">
            <span className="text-bark-600">Bottiglie ({tip.tipo_bottiglia_nome})</span>
            <span className="font-semibold">{q}</span>
          </div>
          <div className="flex justify-between p-2 rounded-lg bg-white">
            <span className="text-bark-600">Tappi ({tip.tipo_tappo_nome})</span>
            <span className="font-semibold">{q}</span>
          </div>
          {conEtichetta && (
            <div className="flex justify-between p-2 rounded-lg bg-white">
              <span className="text-bark-600">Etichette ({tip.tipo_etichetta_nome})</span>
              <span className="font-semibold">{q}</span>
            </div>
          )}
          {conCapsula && (
            <div className="flex justify-between p-2 rounded-lg bg-white">
              <span className="text-bark-600">Capsule ({tip.tipo_capsula_nome})</span>
              <span className="font-semibold">{q}</span>
            </div>
          )}
          <div className="flex justify-between p-2 rounded-lg bg-white">
            <span className="text-bark-600">
              Cartoni ({tip.tipo_cartone_nome}, {cartoneCap}/cad)
            </span>
            <span className="font-semibold">{cartoniNecessari}</span>
          </div>
          {tip.famiglia_is_spumante && tip.tipo_cestello_nome && (
            <div className="flex justify-between p-2 rounded-lg bg-white">
              <span className="text-bark-600">Cestelli ({tip.tipo_cestello_nome})</span>
              <span className="font-semibold">{q}</span>
            </div>
          )}
        </div>
      </div>
    );
  };

  const handleCreaSenza = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await creaSenzaEtichetta({
        tipologia_vino_id: Number(formSenza.tipologia_vino_id),
        quantita: Number(formSenza.quantita),
        con_capsula: formSenza.con_capsula,
      });
      toast.success(`${formSenza.quantita} bottiglie create (senza etichetta)`);
      setShowSenza(false);
      setFormSenza({ tipologia_vino_id: '', quantita: '', con_capsula: false });
      loadAll();
    } catch (e) {
      const errors = e.response?.data?.errors;
      if (errors) {
        errors.forEach(err => toast.error(err));
      } else {
        toast.error(e.response?.data?.error || 'Errore nella creazione');
      }
    }
    setSubmitting(false);
  };

  const handleCreaCon = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await creaConEtichetta({
        tipologia_vino_id: Number(formCon.tipologia_vino_id),
        quantita: Number(formCon.quantita),
        con_capsula: formCon.con_capsula,
      });
      toast.success(`${formCon.quantita} bottiglie create (complete)`);
      setShowCon(false);
      setFormCon({ tipologia_vino_id: '', quantita: '', con_capsula: true });
      loadAll();
    } catch (e) {
      const errors = e.response?.data?.errors;
      if (errors) {
        errors.forEach(err => toast.error(err));
      } else {
        toast.error(e.response?.data?.error || 'Errore nella creazione');
      }
    }
    setSubmitting(false);
  };

  const handleAssocia = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await associaEtichetta({
        tipologia_vino_origine_id: Number(formAssocia.tipologia_vino_origine_id),
        tipologia_vino_destinazione_id: Number(formAssocia.tipologia_vino_destinazione_id),
        quantita: Number(formAssocia.quantita),
        con_capsula: formAssocia.con_capsula,
      });
      toast.success(`Etichetta associata a ${formAssocia.quantita} bottiglie`);
      setShowAssocia(false);
      setFormAssocia({ tipologia_vino_origine_id: '', tipologia_vino_destinazione_id: '', quantita: '', con_capsula: false });
      loadAll();
    } catch (e) {
      const errors = e.response?.data?.errors;
      if (errors) {
        errors.forEach(err => toast.error(err));
      } else {
        toast.error(e.response?.data?.error || 'Errore');
      }
    }
    setSubmitting(false);
  };

  // Disponibilità per associa etichetta (basata su origine)
  const selectedAssociaTip = senzaEtichetta.filter(
    s => s.tipologia_vino__id === Number(formAssocia.tipologia_vino_origine_id)
  );
  const maxDisponibile = selectedAssociaTip.reduce((sum, s) => sum + s.totale, 0);

  const handleAnnulla = async (op) => {
    const tipoLabel = {
      'CREA_SENZA_ETICHETTA': 'creazione senza etichetta',
      'CREA_CON_ETICHETTA': 'creazione con etichetta',
      'ASSOCIA_ETICHETTA': 'associazione etichetta',
    }[op.tipo] || 'operazione';

    const ok = await confirm({
      title: 'Annullare l\'operazione?',
      message: `Stai per annullare la ${tipoLabel} di ${op.quantita} bottiglie (${op.tipologia_vino_nome}).\n\nVerranno ripristinati i materiali in magazzino e il vino nei silos. Le bottiglie create verranno rimosse dai lotti.`,
      confirmLabel: 'Annulla operazione',
      cancelLabel: 'Mantieni',
      variant: 'warning',
    });
    if (!ok) return;
    try {
      await operazioniApi.annulla(op.id);
      toast.success('Operazione annullata');
      loadAll();
    } catch (e) {
      const errors = e.response?.data?.errors;
      if (errors) {
        errors.forEach(err => toast.error(err));
      } else {
        toast.error(e.response?.data?.error || 'Errore nell\'annullamento');
      }
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  // Lotti raggruppati
  const lottiCompleti = allLotti.filter(l => l.stato === 'COMPLETA');
  const lottiSenza = allLotti.filter(l => l.stato === 'SENZA_ETICHETTA');

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="page-title">Imbottigliamento</h1>
          <p className="text-bark-500">Crea bottiglie e gestisci le etichette</p>
        </div>
        <div className="flex gap-3 flex-wrap">
          <button onClick={() => setShowSenza(true)}
            className="btn-warning flex items-center gap-2">
            <Package className="w-4 h-4" /> Crea senza etichetta
          </button>
          <button onClick={() => setShowCon(true)}
            className="btn-primary flex items-center gap-2">
            <CheckCircle className="w-4 h-4" /> Crea con etichetta
          </button>
          <button onClick={() => setShowAssocia(true)}
            className="btn-success flex items-center gap-2"
            disabled={senzaEtichetta.length === 0}>
            <Tag className="w-4 h-4" /> Associa etichetta
          </button>
        </div>
      </div>

      {/* Riepilogo senza etichetta */}
      {senzaEtichetta.length > 0 && (
        <div className="card border-l-4 border-l-amber-400 animate-fade-in">
          <h2 className="section-title flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-500" />
            Bottiglie in attesa di etichetta
          </h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {senzaEtichetta.map((s, i) => (
              <div key={i} className="flex items-center justify-between p-4 rounded-xl bg-amber-50 border border-amber-200">
                <div>
                  <p className="font-semibold text-bark-900">{s.tipologia_vino__nome}</p>
                  <p className="text-xs text-bark-500">{s.tipologia_vino__famiglia__nome}</p>
                  <p className="text-xs text-bark-400">
                    {s.ha_capsula ? 'Con capsula' : 'Senza capsula'}
                  </p>
                </div>
                <span className="text-2xl font-display font-bold text-amber-700">
                  {s.totale.toLocaleString('it-IT')}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Lotti completi */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <CheckCircle className="w-5 h-5 text-olive-600" />
          Bottiglie complete
        </h2>
        {lottiCompleti.length === 0 ? (
          <p className="text-bark-400 text-sm">Nessuna bottiglia completa.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Tipologia</th>
                  <th className="table-header">Quantità</th>
                  <th className="table-header">Etichetta</th>
                  <th className="table-header">Capsula</th>
                  <th className="table-header">Data</th>
                  <th className="table-header w-16"></th>
                </tr>
              </thead>
              <tbody>
                {lottiCompleti.map(l => (
                  <tr key={l.id} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell font-semibold">{l.tipologia_vino_nome}</td>
                    <td className="table-cell">
                      <span className="text-lg font-display font-bold text-olive-700">
                        {l.quantita.toLocaleString('it-IT')}
                      </span>
                    </td>
                    <td className="table-cell">
                      <span className="badge-olive">✓ Sì</span>
                    </td>
                    <td className="table-cell">
                      {l.ha_capsula
                        ? <span className="badge-olive">✓ Sì</span>
                        : <span className="badge-amber">✗ No</span>
                      }
                    </td>
                    <td className="table-cell text-bark-500 text-xs">
                      {new Date(l.data_creazione).toLocaleString('it-IT')}
                    </td>
                    <td className="table-cell">
                      {(() => {
                        const op = allOperazioni.find(o =>
                          o.stato === 'ATTIVA' &&
                          o.tipologia_vino === l.tipologia_vino &&
                          ((o.tipo === 'CREA_CON_ETICHETTA') || (o.tipo === 'ASSOCIA_ETICHETTA'))
                        );
                        return op ? (
                          <button onClick={() => handleAnnulla(op)}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors"
                            title="Annulla operazione">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        ) : null;
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Lotti senza etichetta */}
      {lottiSenza.length > 0 && (
        <div className="card">
          <h2 className="section-title flex items-center gap-2">
            <Package className="w-5 h-5 text-amber-500" />
            Lotti senza etichetta (dettaglio)
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Tipologia</th>
                  <th className="table-header">Quantità</th>
                  <th className="table-header">Capsula</th>
                  <th className="table-header">Data</th>
                  <th className="table-header w-16"></th>
                </tr>
              </thead>
              <tbody>
                {lottiSenza.map(l => (
                  <tr key={l.id} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell font-semibold">{l.tipologia_vino_nome}</td>
                    <td className="table-cell">
                      <span className="text-lg font-display font-bold text-amber-700">
                        {l.quantita.toLocaleString('it-IT')}
                      </span>
                    </td>
                    <td className="table-cell">
                      {l.ha_capsula
                        ? <span className="badge-olive">✓ Sì</span>
                        : <span className="badge-amber">✗ No</span>
                      }
                    </td>
                    <td className="table-cell text-bark-500 text-xs">
                      {new Date(l.data_creazione).toLocaleString('it-IT')}
                    </td>
                    <td className="table-cell">
                      {(() => {
                        const op = allOperazioni.find(o =>
                          o.stato === 'ATTIVA' &&
                          o.tipologia_vino === l.tipologia_vino &&
                          o.tipo === 'CREA_SENZA_ETICHETTA'
                        );
                        return op ? (
                          <button onClick={() => handleAnnulla(op)}
                            className="p-1.5 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors"
                            title="Annulla operazione">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        ) : null;
                      })()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* ─── MODAL: Crea SENZA etichetta ─── */}
      <Modal open={showSenza} onClose={() => setShowSenza(false)} title="Crea bottiglie senza etichetta" wide>
        <form onSubmit={handleCreaSenza} className="space-y-4">
          <div>
            <label className="label">Tipologia vino</label>
            <select className="select-field" required value={formSenza.tipologia_vino_id}
              onChange={e => setFormSenza({...formSenza, tipologia_vino_id: e.target.value})}>
              <option value="">Seleziona tipologia...</option>
              {tipologie.map(t => (
                <option key={t.id} value={t.id}>{t.famiglia_nome} — {t.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Quantità bottiglie</label>
            <input type="number" min="1" className="input-field" required
              placeholder="es: 100"
              value={formSenza.quantita}
              onChange={e => setFormSenza({...formSenza, quantita: e.target.value})} />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="w-5 h-5 rounded border-bark-300 text-wine-600 focus:ring-wine-500"
              checked={formSenza.con_capsula}
              onChange={e => setFormSenza({...formSenza, con_capsula: e.target.checked})} />
            <span className="text-sm text-bark-800 font-medium">Applica capsula in questo step</span>
          </label>

          <MaterialPreview
            tipId={formSenza.tipologia_vino_id}
            qty={formSenza.quantita}
            conEtichetta={false}
            conCapsula={formSenza.con_capsula}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowSenza(false)} className="btn-secondary">Annulla</button>
            <button type="submit" disabled={submitting} className="btn-warning">
              {submitting ? 'Creazione...' : 'Crea senza etichetta'}
            </button>
          </div>
        </form>
      </Modal>

      {/* ─── MODAL: Crea CON etichetta ─── */}
      <Modal open={showCon} onClose={() => setShowCon(false)} title="Crea bottiglie con etichetta" wide>
        <form onSubmit={handleCreaCon} className="space-y-4">
          <div>
            <label className="label">Tipologia vino</label>
            <select className="select-field" required value={formCon.tipologia_vino_id}
              onChange={e => setFormCon({...formCon, tipologia_vino_id: e.target.value})}>
              <option value="">Seleziona tipologia...</option>
              {tipologie.map(t => (
                <option key={t.id} value={t.id}>{t.famiglia_nome} — {t.nome}</option>
              ))}
            </select>
          </div>
          <div>
            <label className="label">Quantità bottiglie</label>
            <input type="number" min="1" className="input-field" required
              placeholder="es: 200"
              value={formCon.quantita}
              onChange={e => setFormCon({...formCon, quantita: e.target.value})} />
          </div>
          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="w-5 h-5 rounded border-bark-300 text-wine-600 focus:ring-wine-500"
              checked={formCon.con_capsula}
              onChange={e => setFormCon({...formCon, con_capsula: e.target.checked})} />
            <span className="text-sm text-bark-800 font-medium">Applica capsula</span>
          </label>

          <MaterialPreview
            tipId={formCon.tipologia_vino_id}
            qty={formCon.quantita}
            conEtichetta={true}
            conCapsula={formCon.con_capsula}
          />

          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowCon(false)} className="btn-secondary">Annulla</button>
            <button type="submit" disabled={submitting} className="btn-primary">
              {submitting ? 'Creazione...' : 'Crea con etichetta'}
            </button>
          </div>
        </form>
      </Modal>

      {/* ─── MODAL: Associa etichetta ─── */}
      <Modal open={showAssocia} onClose={() => setShowAssocia(false)} title="Associa etichetta a bottiglie esistenti" wide>
        <form onSubmit={handleAssocia} className="space-y-4">
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 text-sm text-amber-800">
            <p className="font-semibold flex items-center gap-2">
              <AlertTriangle className="w-4 h-4" />
              Prendi bottiglie senza etichetta da una tipologia e applica l'etichetta di un'altra tipologia (anche diversa).
            </p>
            <p className="mt-1 text-amber-700">
              Puoi riutilizzare bottiglie per vini diversi cambiando solo l'etichetta.
            </p>
          </div>

          <div>
            <label className="label">Tipologia origine (bottiglie senza etichetta)</label>
            <select className="select-field" required value={formAssocia.tipologia_vino_origine_id}
              onChange={e => setFormAssocia({...formAssocia, tipologia_vino_origine_id: e.target.value})}>
              <option value="">Seleziona tipologia di partenza...</option>
              {/* Solo tipologie con bottiglie senza etichetta */}
              {[...new Set(senzaEtichetta.map(s => s.tipologia_vino__id))].map(tipId => {
                const info = senzaEtichetta.find(s => s.tipologia_vino__id === tipId);
                const tot = senzaEtichetta
                  .filter(s => s.tipologia_vino__id === tipId)
                  .reduce((sum, s) => sum + s.totale, 0);
                return (
                  <option key={tipId} value={tipId}>
                    {info.tipologia_vino__famiglia__nome} — {info.tipologia_vino__nome} ({tot} disponibili)
                  </option>
                );
              })}
            </select>
          </div>

          {formAssocia.tipologia_vino_origine_id && (
            <div className="bg-bark-50 rounded-lg p-3 text-sm space-y-2">
              <div className="flex justify-between">
                <span className="text-bark-600">Disponibili senza capsula:</span>
                <span className="font-bold text-bark-900">
                  {selectedAssociaTip
                    .filter(s => !s.ha_capsula)
                    .reduce((sum, s) => sum + s.totale, 0)
                    .toLocaleString('it-IT')}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-bark-600">Disponibili con capsula:</span>
                <span className="font-bold text-bark-900">
                  {selectedAssociaTip
                    .filter(s => s.ha_capsula)
                    .reduce((sum, s) => sum + s.totale, 0)
                    .toLocaleString('it-IT')}
                </span>
              </div>
              <div className="flex justify-between border-t border-bark-200 pt-2">
                <span className="text-bark-700 font-semibold">Totale disponibili:</span>
                <span className="font-bold text-wine-700">{maxDisponibile.toLocaleString('it-IT')}</span>
              </div>
              {formAssocia.con_capsula && selectedAssociaTip.filter(s => !s.ha_capsula).reduce((sum, s) => sum + s.totale, 0) > 0 && (
                <p className="text-xs text-olive-700 bg-olive-50 px-2 py-1 rounded">
                  ℹ️ Con flag capsula attivo, verranno prese prima quelle senza capsula
                </p>
              )}
            </div>
          )}

          <div>
            <label className="label">Tipologia destinazione (etichetta da applicare)</label>
            <select className="select-field" required value={formAssocia.tipologia_vino_destinazione_id}
              onChange={e => setFormAssocia({...formAssocia, tipologia_vino_destinazione_id: e.target.value})}>
              <option value="">Seleziona etichetta da applicare...</option>
              {tipologie.map(t => (
                <option key={t.id} value={t.id}>
                  {t.famiglia_nome} — {t.nome} (etichetta: {t.tipo_etichetta_nome})
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Quantità da etichettare</label>
            <input type="number" min="1" max={maxDisponibile || undefined}
              className="input-field" required
              placeholder={`max ${maxDisponibile}`}
              value={formAssocia.quantita}
              onChange={e => setFormAssocia({...formAssocia, quantita: e.target.value})} />
          </div>

          <label className="flex items-center gap-3 cursor-pointer">
            <input type="checkbox" className="w-5 h-5 rounded border-bark-300 text-wine-600 focus:ring-wine-500"
              checked={formAssocia.con_capsula}
              onChange={e => setFormAssocia({...formAssocia, con_capsula: e.target.checked})} />
            <span className="text-sm text-bark-800 font-medium">
              Applica capsula (se non già applicata nello step precedente)
            </span>
          </label>

          <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
            <button type="button" onClick={() => setShowAssocia(false)} className="btn-secondary">Annulla</button>
            <button type="submit" disabled={submitting} className="btn-success">
              {submitting ? 'Associazione...' : 'Associa Etichetta'}
            </button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
