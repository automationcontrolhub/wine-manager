import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import {
  ShoppingCart, Plus, Edit3, XCircle, Trash2, Eye, Truck, CheckCircle2,
  Receipt, Tag as TagIcon, Wine, Gift, User, UserCog, RefreshCcw, PackageCheck,
} from 'lucide-react';
import { useConfirm } from '../components/ConfirmDialog';
import {
  ordini, clienti, agenti, tipoGadget,
  getBottiglieDisponibili,
} from '../api/client';

const STATO_BADGE = {
  CONFERMATO: 'bg-olive-100 text-olive-800 border border-olive-200',
  ANNULLATO: 'bg-red-50 text-red-700 border border-red-200',
};

const fmtCurrency = (v) =>
  Number(v ?? 0).toLocaleString('it-IT', { style: 'currency', currency: 'EUR' });

const fmtDate = (d) => {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleString('it-IT', {
      day: '2-digit', month: '2-digit', year: 'numeric',
      hour: '2-digit', minute: '2-digit',
    });
  } catch { return d; }
};

const fmtDateShort = (d) => {
  if (!d) return '—';
  try {
    return new Date(d).toLocaleDateString('it-IT', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch { return d; }
};

export default function Ordini() {
  const confirm = useConfirm();
  const [loading, setLoading] = useState(true);
  const [ordiniList, setOrdiniList] = useState([]);
  const [filterStato, setFilterStato] = useState('');

  // Dataset condivisi per i form
  const [clientiList, setClientiList] = useState([]);
  const [agentiList, setAgentiList] = useState([]);
  const [gadgetList, setGadgetList] = useState([]);
  const [bottiglieDisponibili, setBottiglieDisponibili] = useState([]);

  // Modali
  const [showForm, setShowForm] = useState(false);
  const [editingOrdine, setEditingOrdine] = useState(null); // null = creazione, oggetto = modifica
  const [showDettaglio, setShowDettaglio] = useState(false);
  const [ordineDettaglio, setOrdineDettaglio] = useState(null);

  const loadOrdini = async () => {
    setLoading(true);
    try {
      const params = filterStato ? { stato: filterStato } : {};
      const res = await ordini.list(params);
      setOrdiniList(Array.isArray(res) ? res : res.results || []);
    } catch (e) {
      toast.error('Errore nel caricamento ordini');
    }
    setLoading(false);
  };

  const loadDatasets = async () => {
    try {
      const [c, a, g, b] = await Promise.all([
        clienti.list(),
        agenti.list(),
        tipoGadget.list(),
        getBottiglieDisponibili(),
      ]);
      setClientiList(Array.isArray(c) ? c : c.results || []);
      setAgentiList(Array.isArray(a) ? a : a.results || []);
      setGadgetList(Array.isArray(g) ? g : g.results || []);
      setBottiglieDisponibili(Array.isArray(b) ? b : b.results || []);
    } catch {
      toast.error('Errore nel caricamento dati');
    }
  };

  useEffect(() => { loadOrdini(); }, [filterStato]);
  useEffect(() => { loadDatasets(); }, []);

  const openCreate = async () => {
    await loadDatasets();
    setEditingOrdine(null);
    setShowForm(true);
  };

  const openEdit = async (ord) => {
    await loadDatasets();
    setEditingOrdine(ord);
    setShowForm(true);
  };

  const openDettaglio = async (id) => {
    try {
      const o = await ordini.retrieve(id);
      setOrdineDettaglio(o);
      setShowDettaglio(true);
    } catch {
      toast.error('Errore nel caricamento ordine');
    }
  };

  const handleAnnulla = async (ord) => {
    const ok = await confirm({
      title: `Annullare ordine #${ord.numero}?`,
      message: `Le bottiglie e i gadget verranno automaticamente ripristinati in magazzino. L'ordine resterà visibile nello storico con stato "Annullato".`,
      confirmLabel: 'Annulla ordine',
      variant: 'warning',
    });
    if (!ok) return;
    try {
      await ordini.annulla(ord.id);
      toast.success(`Ordine #${ord.numero} annullato. Magazzino ripristinato.`);
      loadOrdini();
    } catch (e) {
      const msg = e.response?.data?.error || JSON.stringify(e.response?.data);
      toast.error(msg || "Errore nell'annullamento");
    }
  };

  const handleRipristina = async (ord) => {
    const ok = await confirm({
      title: `Ripristinare ordine #${ord.numero}?`,
      message: `L'ordine tornerà CONFERMATO e le bottiglie/gadget verranno nuovamente scalate dal magazzino. L'operazione fallirà se non c'è disponibilità sufficiente.`,
      confirmLabel: 'Ripristina',
      variant: 'info',
    });
    if (!ok) return;
    try {
      await ordini.ripristina(ord.id);
      toast.success(`Ordine #${ord.numero} ripristinato`);
      loadOrdini();
    } catch (e) {
      const errs = e.response?.data?.errors;
      if (Array.isArray(errs)) {
        toast.error(errs.join('\n'), { duration: 6000 });
      } else {
        toast.error(e.response?.data?.error || 'Errore nel ripristino');
      }
    }
  };

  const handleDelete = async (ord) => {
    const ok = await confirm({
      title: `Eliminare ordine #${ord.numero}?`,
      message: `${ord.stato === 'CONFERMATO'
        ? 'Le bottiglie e i gadget verranno ripristinati in magazzino, poi l\'ordine sarà eliminato in modo definitivo.'
        : 'L\'ordine verrà eliminato in modo definitivo dallo storico.'}\n\nQuesta operazione non può essere annullata.`,
      confirmLabel: 'Elimina definitivamente',
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await ordini.delete(ord.id);
      toast.success(`Ordine #${ord.numero} eliminato`);
      loadOrdini();
    } catch (e) {
      toast.error("Errore nell'eliminazione");
    }
  };

  // Quick toggle dei flag (tracking, pacco arrivato, fattura pagata) dalla lista
  const handleQuickToggle = async (ord, campo) => {
    try {
      await ordini.update(ord.id, { [campo]: !ord[campo] });
      loadOrdini();
    } catch {
      toast.error('Errore aggiornamento');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-3">
        <div>
          <h1 className="page-title flex items-center gap-3">
            <ShoppingCart className="w-8 h-8 text-wine-600" />
            Ordini
          </h1>
          <p className="text-bark-500">Crea, modifica e gestisci gli ordini clienti</p>
        </div>
        <div className="flex gap-3">
          <button onClick={loadOrdini} className="btn-secondary flex items-center gap-2" title="Ricarica">
            <RefreshCcw className="w-4 h-4" />
          </button>
          <button onClick={openCreate} className="btn-primary flex items-center gap-2">
            <Plus className="w-4 h-4" /> Nuovo Ordine
          </button>
        </div>
      </div>

      {/* Filtri */}
      <div className="flex gap-1 bg-bark-100 rounded-xl p-1 w-fit">
        {[
          { v: '', l: 'Tutti' },
          { v: 'CONFERMATO', l: 'Confermati' },
          { v: 'ANNULLATO', l: 'Annullati' },
        ].map(o => (
          <button key={o.v} onClick={() => setFilterStato(o.v)}
            className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
              filterStato === o.v ? 'bg-white text-bark-900 shadow-sm' : 'text-bark-500 hover:text-bark-700'
            }`}>
            {o.l}
          </button>
        ))}
      </div>

      <div className="card">
        {loading ? (
          <div className="flex items-center justify-center h-32">
            <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
          </div>
        ) : ordiniList.length === 0 ? (
          <div className="text-center py-12">
            <ShoppingCart className="w-12 h-12 text-bark-300 mx-auto mb-3" />
            <p className="text-bark-500">Nessun ordine presente.</p>
            <p className="text-bark-400 text-sm mt-1">Clicca "Nuovo Ordine" per crearne uno.</p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">#</th>
                  <th className="table-header">Data</th>
                  <th className="table-header">Cliente</th>
                  <th className="table-header">Agente</th>
                  <th className="table-header text-right">Totale</th>
                  <th className="table-header">Stato</th>
                  <th className="table-header text-center">Spedizione</th>
                  <th className="table-header text-center">Pagamento</th>
                  <th className="table-header w-32">Azioni</th>
                </tr>
              </thead>
              <tbody>
                {ordiniList.map(ord => (
                  <tr key={ord.id} className="border-b border-bark-50 hover:bg-bark-50/50 transition-colors">
                    <td className="table-cell font-bold text-bark-900">#{ord.numero}</td>
                    <td className="table-cell text-bark-600">{fmtDateShort(ord.data)}</td>
                    <td className="table-cell font-semibold text-bark-900">{ord.cliente_label || '—'}</td>
                    <td className="table-cell text-bark-600">{ord.agente_label || <span className="text-bark-300">—</span>}</td>
                    <td className="table-cell text-right font-display font-bold text-wine-700">
                      {fmtCurrency(ord.totale)}
                    </td>
                    <td className="table-cell">
                      <span className={`badge ${STATO_BADGE[ord.stato] || 'badge-amber'}`}>
                        {ord.stato_display || ord.stato}
                      </span>
                    </td>
                    <td className="table-cell text-center">
                      {ord.tracking_number ? (
                        <span title={`Tracking: ${ord.tracking_number}`}
                          className="inline-flex items-center gap-1 text-xs text-bark-600">
                          <Truck className="w-3.5 h-3.5" /> {ord.tracking_number.slice(0, 10)}
                        </span>
                      ) : (
                        <span className="text-xs text-bark-300">—</span>
                      )}
                      <button onClick={() => handleQuickToggle(ord, 'pacco_arrivato')}
                        title={ord.pacco_arrivato ? 'Pacco arrivato' : 'Pacco non arrivato'}
                        className={`block mx-auto mt-1 p-1 rounded ${
                          ord.pacco_arrivato ? 'text-olive-600' : 'text-bark-300 hover:text-bark-500'
                        }`}>
                        <PackageCheck className="w-4 h-4" />
                      </button>
                    </td>
                    <td className="table-cell text-center">
                      <button onClick={() => handleQuickToggle(ord, 'fattura_pagata')}
                        title={ord.fattura_pagata ? 'Fattura pagata' : 'Fattura non pagata'}
                        className={`p-1 rounded ${
                          ord.fattura_pagata ? 'text-olive-600' : 'text-bark-300 hover:text-bark-500'
                        }`}>
                        <Receipt className="w-4 h-4" />
                      </button>
                    </td>
                    <td className="table-cell">
                      <div className="flex gap-1">
                        <button onClick={() => openDettaglio(ord.id)}
                          className="p-1.5 rounded-lg hover:bg-bark-100 text-bark-500 hover:text-bark-700 transition-colors"
                          title="Visualizza dettaglio">
                          <Eye className="w-4 h-4" />
                        </button>
                        <button onClick={() => openEdit(ord)}
                          className="p-1.5 rounded-lg hover:bg-wine-50 text-bark-400 hover:text-wine-600 transition-colors"
                          title="Modifica">
                          <Edit3 className="w-4 h-4" />
                        </button>
                        {ord.stato === 'CONFERMATO' ? (
                          <button onClick={() => handleAnnulla(ord)}
                            className="p-1.5 rounded-lg hover:bg-amber-50 text-bark-400 hover:text-amber-600 transition-colors"
                            title="Annulla ordine">
                            <XCircle className="w-4 h-4" />
                          </button>
                        ) : (
                          <button onClick={() => handleRipristina(ord)}
                            className="p-1.5 rounded-lg hover:bg-olive-50 text-bark-400 hover:text-olive-600 transition-colors"
                            title="Ripristina ordine">
                            <CheckCircle2 className="w-4 h-4" />
                          </button>
                        )}
                        <button onClick={() => handleDelete(ord)}
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

      {/* Modal Form Creazione/Modifica */}
      {showForm && (
        <OrdineForm
          editingOrdine={editingOrdine}
          clientiList={clientiList}
          agentiList={agentiList}
          gadgetList={gadgetList}
          bottiglieDisponibili={bottiglieDisponibili}
          onClose={() => setShowForm(false)}
          onSaved={() => {
            setShowForm(false);
            loadOrdini();
            loadDatasets();
          }}
        />
      )}

      {/* Modal Dettaglio */}
      {showDettaglio && ordineDettaglio && (
        <OrdineDettaglioModal
          ordine={ordineDettaglio}
          onClose={() => setShowDettaglio(false)}
        />
      )}
    </div>
  );
}

// ─────────────────────────────────────────────────────────────────────────
//                          FORM CREAZIONE / MODIFICA
// ─────────────────────────────────────────────────────────────────────────

function OrdineForm({ editingOrdine, clientiList, agentiList, gadgetList, bottiglieDisponibili, onClose, onSaved }) {
  const isEdit = !!editingOrdine;

  const [submitting, setSubmitting] = useState(false);
  const [clienteId, setClienteId] = useState(editingOrdine?.cliente ?? '');
  const [agenteId, setAgenteId] = useState(editingOrdine?.agente ?? '');
  const [sconto, setSconto] = useState(editingOrdine?.sconto_percentuale ?? '0');
  const [iva, setIva] = useState(editingOrdine?.aliquota_iva ?? '22');
  const [tracking, setTracking] = useState(editingOrdine?.tracking_number ?? '');
  const [paccoArrivato, setPaccoArrivato] = useState(editingOrdine?.pacco_arrivato ?? false);
  const [fatturaPagata, setFatturaPagata] = useState(editingOrdine?.fattura_pagata ?? false);
  const [note, setNote] = useState(editingOrdine?.note ?? '');

  // Righe bottiglie e gadget
  const [righeBott, setRigheBott] = useState(() => {
    if (editingOrdine?.righe_bottiglie?.length) {
      return editingOrdine.righe_bottiglie.map(r => ({
        tipologia_vino_id: r.tipologia_vino,
        ha_etichetta: r.ha_etichetta,
        ha_capsula: r.ha_capsula,
        quantita: r.quantita,
        prezzo_unitario: r.prezzo_unitario,
      }));
    }
    return [emptyRigaBott()];
  });
  const [righeGad, setRigheGad] = useState(() => {
    if (editingOrdine?.righe_gadget?.length) {
      return editingOrdine.righe_gadget.map(r => ({
        tipo_gadget_id: r.tipo_gadget,
        quantita: r.quantita,
      }));
    }
    return [];
  });

  function emptyRigaBott() {
    return { tipologia_vino_id: '', ha_etichetta: true, ha_capsula: true, quantita: 1, prezzo_unitario: '' };
  }
  function emptyRigaGadget() {
    return { tipo_gadget_id: '', quantita: 1 };
  }

  // Cliente e agente selezionati (per i dati auto-popolati)
  const clienteSel = useMemo(
    () => clientiList.find(c => String(c.id) === String(clienteId)),
    [clientiList, clienteId]
  );
  const agenteSel = useMemo(
    () => agentiList.find(a => String(a.id) === String(agenteId)),
    [agentiList, agenteId]
  );

  // Calcolo totali real-time
  const imponibileLordo = useMemo(() => {
    return righeBott.reduce((acc, r) => {
      const q = Number(r.quantita) || 0;
      const p = Number(r.prezzo_unitario) || 0;
      return acc + q * p;
    }, 0);
  }, [righeBott]);

  const scontoNum = Number(sconto) || 0;
  const ivaNum = Number(iva) || 0;
  const importoSconto = imponibileLordo * scontoNum / 100;
  const imponibileNetto = imponibileLordo - importoSconto;
  const importoIva = imponibileNetto * ivaNum / 100;
  const totale = imponibileNetto + importoIva;

  // Funzioni manipolazione righe bottiglie
  const updateRigaBott = (idx, patch) => {
    setRigheBott(prev => prev.map((r, i) => i === idx ? { ...r, ...patch } : r));
  };
  const addRigaBott = () => setRigheBott(prev => [...prev, emptyRigaBott()]);
  const removeRigaBott = (idx) => setRigheBott(prev => prev.filter((_, i) => i !== idx));

  const updateRigaGad = (idx, patch) => {
    setRigheGad(prev => prev.map((r, i) => i === idx ? { ...r, ...patch } : r));
  };
  const addRigaGad = () => setRigheGad(prev => [...prev, emptyRigaGadget()]);
  const removeRigaGad = (idx) => setRigheGad(prev => prev.filter((_, i) => i !== idx));

  // Quando l'utente seleziona una bottiglia dal dropdown, valorizza i 3 campi (tipologia, eti, cap)
  const handleSelectBottiglia = (idx, key) => {
    if (!key) {
      updateRigaBott(idx, { tipologia_vino_id: '', ha_etichetta: true, ha_capsula: true });
      return;
    }
    const [tipId, eti, cap] = key.split('|');
    // Avvisa se la stessa tipologia è già presente in un'altra riga
    const duplicato = righeBott.some((r, i) =>
      i !== idx &&
      String(r.tipologia_vino_id) === tipId &&
      !!r.ha_etichetta === (eti === 'true') &&
      !!r.ha_capsula === (cap === 'true')
    );
    if (duplicato) {
      toast('⚠️ Tipologia già presente in un\'altra riga. All\'invio le quantità verranno sommate automaticamente.', { duration: 5000 });
    }
    updateRigaBott(idx, {
      tipologia_vino_id: Number(tipId),
      ha_etichetta: eti === 'true',
      ha_capsula: cap === 'true',
    });
  };

  // Calcola giacenza NETTA per una riga: stock totale − quantità già richieste nelle ALTRE righe dello stesso tipo
  const getDisponibile = (riga, idx) => {
    if (!riga.tipologia_vino_id) return null;
    const found = bottiglieDisponibili.find(b =>
      b.tipologia_vino_id === Number(riga.tipologia_vino_id) &&
      b.ha_etichetta === !!riga.ha_etichetta &&
      b.ha_capsula === !!riga.ha_capsula
    );
    const stockTotale = found?.quantita_totale ?? 0;
    // Sottrai le quantità delle altre righe che usano lo stesso tipo
    const altreRighe = righeBott.reduce((acc, r, i) => {
      if (
        i !== idx &&
        Number(r.tipologia_vino_id) === Number(riga.tipologia_vino_id) &&
        !!r.ha_etichetta === !!riga.ha_etichetta &&
        !!r.ha_capsula === !!riga.ha_capsula
      ) {
        return acc + (Number(r.quantita) || 0);
      }
      return acc;
    }, 0);
    return Math.max(0, stockTotale - altreRighe);
  };

  const getGadgetDisp = (gid) => {
    const g = gadgetList.find(x => x.id === Number(gid));
    return g?.quantita ?? null;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!clienteId) return toast.error('Seleziona un cliente');
    if (!righeBott.length) return toast.error('Aggiungi almeno una riga bottiglie');

    // Validazioni client-side
    for (const [i, r] of righeBott.entries()) {
      if (!r.tipologia_vino_id) return toast.error(`Riga ${i + 1}: seleziona la bottiglia`);
      if (!r.quantita || Number(r.quantita) < 1) return toast.error(`Riga ${i + 1}: quantità non valida`);
      if (r.prezzo_unitario === '' || Number(r.prezzo_unitario) < 0)
        return toast.error(`Riga ${i + 1}: prezzo unitario non valido`);
    }
    for (const [i, r] of righeGad.entries()) {
      if (!r.tipo_gadget_id) return toast.error(`Riga gadget ${i + 1}: seleziona il gadget`);
      if (!r.quantita || Number(r.quantita) < 1) return toast.error(`Riga gadget ${i + 1}: quantità non valida`);
    }

    setSubmitting(true);
    try {
      // Fondi righe con la stessa chiave (tipologia + etichetta + capsula):
      // somma le quantità e usa il prezzo dell'ultima riga (più recente)
      const mergedBott = [];
      for (const r of righeBott) {
        const existing = mergedBott.find(x =>
          Number(x.tipologia_vino_id) === Number(r.tipologia_vino_id) &&
          !!x.ha_etichetta === !!r.ha_etichetta &&
          !!x.ha_capsula === !!r.ha_capsula
        );
        if (existing) {
          existing.quantita = Number(existing.quantita) + Number(r.quantita);
          existing.prezzo_unitario = r.prezzo_unitario; // usa l'ultimo prezzo inserito
        } else {
          mergedBott.push({ ...r });
        }
      }
      if (mergedBott.length < righeBott.length) {
        toast('ℹ️ Righe duplicate unite automaticamente.', { duration: 3000 });
      }

      const payload = {
        cliente_id: Number(clienteId),
        agente_id: agenteId ? Number(agenteId) : null,
        sconto_percentuale: scontoNum,
        aliquota_iva: ivaNum,
        tracking_number: tracking,
        pacco_arrivato: paccoArrivato,
        fattura_pagata: fatturaPagata,
        note,
        righe_bottiglie: mergedBott.map(r => ({
          tipologia_vino_id: Number(r.tipologia_vino_id),
          ha_etichetta: !!r.ha_etichetta,
          ha_capsula: !!r.ha_capsula,
          quantita: Number(r.quantita),
          prezzo_unitario: Number(r.prezzo_unitario),
        })),
        righe_gadget: righeGad.map(r => ({
          tipo_gadget_id: Number(r.tipo_gadget_id),
          quantita: Number(r.quantita),
        })),
      };

      if (isEdit) {
        await ordini.update(editingOrdine.id, payload);
        toast.success(`Ordine #${editingOrdine.numero} aggiornato`);
      } else {
        const created = await ordini.create(payload);
        toast.success(`Ordine #${created.numero} creato. Magazzino scalato.`);
      }
      onSaved();
    } catch (err) {
      const data = err.response?.data;
      if (data?.errors && Array.isArray(data.errors)) {
        toast.error(data.errors.join('\n'), { duration: 7000 });
      } else if (data?.error) {
        toast.error(data.error);
      } else {
        toast.error(JSON.stringify(data) || 'Errore');
      }
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <ModalFullscreen
      onClose={onClose}
      title={isEdit
        ? `Modifica Ordine #${editingOrdine.numero}`
        : 'Nuovo Ordine'}
      subtitle={isEdit && editingOrdine.stato === 'ANNULLATO'
        ? 'Ordine annullato — le modifiche non toccheranno il magazzino'
        : isEdit && editingOrdine.stato === 'CONFERMATO'
          ? 'Le modifiche alle righe ripristineranno e riscaleranno il magazzino'
          : 'Compila i dati dell\'ordine. Le bottiglie e i gadget verranno scalate dal magazzino.'}
    >
      <form onSubmit={handleSubmit} className="space-y-6">

        {/* ───── Cliente + Agente ───── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SezioneCard icon={User} title="Cliente" required>
            <select className="select-field" required
              value={clienteId} onChange={e => setClienteId(e.target.value)}>
              <option value="">Seleziona cliente...</option>
              {clientiList.map(c => (
                <option key={c.id} value={c.id}>{c.label || (c.azienda ? `${c.azienda} — ${c.nome}` : c.nome)}</option>
              ))}
            </select>
            {clienteSel && (
              <div className="mt-3 text-sm bg-bark-50 rounded-lg p-3 space-y-1">
                {clienteSel.azienda && <div><span className="text-bark-500">Azienda:</span> <span className="font-semibold">{clienteSel.azienda}</span></div>}
                <div><span className="text-bark-500">Nome:</span> {clienteSel.nome}</div>
                {clienteSel.via && <div><span className="text-bark-500">Indirizzo:</span> {clienteSel.via}</div>}
                {clienteSel.partita_iva && <div><span className="text-bark-500">P. IVA:</span> {clienteSel.partita_iva}</div>}
                {clienteSel.telefono && <div><span className="text-bark-500">Tel:</span> {clienteSel.telefono}</div>}
                {clienteSel.email && <div><span className="text-bark-500">Email:</span> {clienteSel.email}</div>}
              </div>
            )}
          </SezioneCard>

          <SezioneCard icon={UserCog} title="Agente (opzionale)">
            <select className="select-field"
              value={agenteId} onChange={e => setAgenteId(e.target.value)}>
              <option value="">Nessun agente</option>
              {agentiList.map(a => (
                <option key={a.id} value={a.id}>{a.cognome} {a.nome}</option>
              ))}
            </select>
            {agenteSel && (
              <div className="mt-3 text-sm bg-bark-50 rounded-lg p-3 space-y-1">
                <div><span className="text-bark-500">Nome:</span> <span className="font-semibold">{agenteSel.cognome} {agenteSel.nome}</span></div>
                {agenteSel.telefono && <div><span className="text-bark-500">Tel:</span> {agenteSel.telefono}</div>}
                {agenteSel.email && <div><span className="text-bark-500">Email:</span> {agenteSel.email}</div>}
              </div>
            )}
          </SezioneCard>
        </div>

        {/* ───── Righe bottiglie ───── */}
        <SezioneCard icon={Wine} title="Bottiglie" required>
          <div className="space-y-3">
            {righeBott.map((r, idx) => {
              const disp = getDisponibile(r, idx);
              const subtotale = (Number(r.quantita) || 0) * (Number(r.prezzo_unitario) || 0);
              const selKey = r.tipologia_vino_id ? `${r.tipologia_vino_id}|${r.ha_etichetta}|${r.ha_capsula}` : '';
              return (
                <div key={idx} className="grid grid-cols-12 gap-2 items-end border border-bark-100 rounded-lg p-3 bg-bark-50/40">
                  <div className="col-span-12 sm:col-span-5">
                    <label className="label text-xs">Bottiglia</label>
                    <select className="select-field" required
                      value={selKey}
                      onChange={e => handleSelectBottiglia(idx, e.target.value)}>
                      <option value="">Seleziona...</option>
                      {bottiglieDisponibili.map(b => {
                        const key = `${b.tipologia_vino_id}|${b.ha_etichetta}|${b.ha_capsula}`;
                        const tag = [
                          b.ha_etichetta ? 'etichettata' : 'NON etichettata',
                          b.ha_capsula ? 'con capsula' : 'senza capsula',
                        ].join(', ');
                        return (
                          <option key={key} value={key}>
                            {b.famiglia_nome} — {b.tipologia_vino_nome} ({tag}) — disp. {b.quantita_totale}
                          </option>
                        );
                      })}
                    </select>
                    {disp !== null && (
                      <p className={`text-xs mt-1 ${
                        Number(r.quantita) > disp ? 'text-red-600 font-semibold' : 'text-bark-500'
                      }`}>
                        Giacenza disponibile: <span className="font-semibold">{disp}</span>
                        {Number(r.quantita) > disp && <span> — quantità eccessiva!</span>}
                      </p>
                    )}
                  </div>
                  <div className="col-span-4 sm:col-span-2">
                    <label className="label text-xs">Quantità</label>
                    <input type="number" min="1" className="input-field" required
                      value={r.quantita}
                      onChange={e => updateRigaBott(idx, { quantita: e.target.value })} />
                  </div>
                  <div className="col-span-4 sm:col-span-2">
                    <label className="label text-xs">€ / bott.</label>
                    <input type="number" step="0.01" min="0" className="input-field" required
                      placeholder="0.00"
                      value={r.prezzo_unitario}
                      onChange={e => updateRigaBott(idx, { prezzo_unitario: e.target.value })} />
                  </div>
                  <div className="col-span-3 sm:col-span-2 text-right">
                    <label className="label text-xs">Subtotale</label>
                    <p className="font-display font-bold text-wine-700">{fmtCurrency(subtotale)}</p>
                  </div>
                  <div className="col-span-1 sm:col-span-1 flex justify-end">
                    <button type="button"
                      onClick={() => removeRigaBott(idx)}
                      className="p-2 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors"
                      title="Rimuovi riga"
                      disabled={righeBott.length === 1}>
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              );
            })}
            <button type="button" onClick={addRigaBott}
              className="w-full py-2 rounded-lg border-2 border-dashed border-bark-200 text-bark-500 hover:border-wine-300 hover:text-wine-600 transition-colors text-sm font-semibold flex items-center justify-center gap-2">
              <Plus className="w-4 h-4" /> Aggiungi tipologia bottiglia
            </button>
          </div>
        </SezioneCard>

        {/* ───── Righe gadget (omaggio) ───── */}
        <SezioneCard icon={Gift} title="Gadget omaggio (opzionale)">
          {righeGad.length === 0 ? (
            <p className="text-bark-400 text-sm mb-3">Nessun gadget aggiunto.</p>
          ) : (
            <div className="space-y-3 mb-3">
              {righeGad.map((r, idx) => {
                const dispG = getGadgetDisp(r.tipo_gadget_id);
                return (
                  <div key={idx} className="grid grid-cols-12 gap-2 items-end border border-bark-100 rounded-lg p-3 bg-bark-50/40">
                    <div className="col-span-12 sm:col-span-8">
                      <label className="label text-xs">Gadget</label>
                      <select className="select-field" required
                        value={r.tipo_gadget_id}
                        onChange={e => updateRigaGad(idx, { tipo_gadget_id: e.target.value })}>
                        <option value="">Seleziona...</option>
                        {gadgetList.map(g => (
                          <option key={g.id} value={g.id}>{g.nome} — disp. {g.quantita}</option>
                        ))}
                      </select>
                      {dispG !== null && (
                        <p className={`text-xs mt-1 ${
                          Number(r.quantita) > dispG ? 'text-red-600 font-semibold' : 'text-bark-500'
                        }`}>
                          Disponibili: <span className="font-semibold">{dispG}</span>
                        </p>
                      )}
                    </div>
                    <div className="col-span-8 sm:col-span-3">
                      <label className="label text-xs">Quantità</label>
                      <input type="number" min="1" className="input-field" required
                        value={r.quantita}
                        onChange={e => updateRigaGad(idx, { quantita: e.target.value })} />
                    </div>
                    <div className="col-span-4 sm:col-span-1 flex justify-end">
                      <button type="button"
                        onClick={() => removeRigaGad(idx)}
                        className="p-2 rounded-lg hover:bg-red-50 text-bark-400 hover:text-red-500 transition-colors"
                        title="Rimuovi">
                        <Trash2 className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
          <button type="button" onClick={addRigaGad}
            className="w-full py-2 rounded-lg border-2 border-dashed border-bark-200 text-bark-500 hover:border-wine-300 hover:text-wine-600 transition-colors text-sm font-semibold flex items-center justify-center gap-2">
            <Plus className="w-4 h-4" /> Aggiungi gadget omaggio
          </button>
        </SezioneCard>

        {/* ───── Sconto / IVA / Tracking / Flag ───── */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">

          <SezioneCard icon={TagIcon} title="Sconto & IVA">
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="label">Sconto %</label>
                <input type="number" min="0" max="100" step="0.01" className="input-field"
                  value={sconto} onChange={e => setSconto(e.target.value)} />
              </div>
              <div>
                <label className="label">Aliquota IVA %</label>
                <input type="number" min="0" step="0.01" className="input-field"
                  value={iva} onChange={e => setIva(e.target.value)} />
              </div>
            </div>
          </SezioneCard>

          <SezioneCard icon={Truck} title="Spedizione & Pagamento">
            <div className="space-y-3">
              <div>
                <label className="label">Tracking number (opzionale)</label>
                <input type="text" className="input-field" placeholder="Numero tracking"
                  value={tracking} onChange={e => setTracking(e.target.value)} />
              </div>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 accent-wine-600"
                  checked={paccoArrivato} onChange={e => setPaccoArrivato(e.target.checked)} />
                <span className="text-sm text-bark-700 font-semibold">Pacco arrivato</span>
              </label>
              <label className="flex items-center gap-2 cursor-pointer">
                <input type="checkbox" className="w-4 h-4 accent-wine-600"
                  checked={fatturaPagata} onChange={e => setFatturaPagata(e.target.checked)} />
                <span className="text-sm text-bark-700 font-semibold">Fattura pagata</span>
              </label>
            </div>
          </SezioneCard>
        </div>

        {/* ───── Note ───── */}
        <SezioneCard title="Note (opzionali)">
          <textarea className="input-field min-h-[60px]"
            placeholder="Eventuali note interne sull'ordine..."
            value={note} onChange={e => setNote(e.target.value)} />
        </SezioneCard>

        {/* ───── Totali ───── */}
        <div className="bg-gradient-to-br from-bark-50 to-wine-50/50 rounded-xl p-5 border border-bark-100">
          <h3 className="text-sm font-bold uppercase tracking-wider text-bark-500 mb-3">Riepilogo Totali</h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xs text-bark-500">Imponibile lordo</p>
              <p className="font-display font-bold text-bark-800">{fmtCurrency(imponibileLordo)}</p>
            </div>
            <div>
              <p className="text-xs text-bark-500">Sconto ({scontoNum}%)</p>
              <p className="font-display font-bold text-amber-700">– {fmtCurrency(importoSconto)}</p>
            </div>
            <div>
              <p className="text-xs text-bark-500">IVA ({ivaNum}%)</p>
              <p className="font-display font-bold text-bark-800">{fmtCurrency(importoIva)}</p>
            </div>
            <div className="bg-wine-700 text-white rounded-lg py-2">
              <p className="text-xs opacity-80">Totale finale</p>
              <p className="font-display font-bold text-lg">{fmtCurrency(totale)}</p>
            </div>
          </div>
        </div>

        {/* ───── Pulsanti ───── */}
        <div className="flex justify-end gap-3 pt-4 border-t border-bark-100 sticky bottom-0 bg-white pb-1">
          <button type="button" onClick={onClose} className="btn-secondary" disabled={submitting}>Annulla</button>
          <button type="submit" className="btn-primary flex items-center gap-2" disabled={submitting}>
            {submitting && <span className="w-4 h-4 border-2 border-white/40 border-t-white rounded-full animate-spin" />}
            {isEdit ? 'Salva modifiche' : 'Crea & invia ordine'}
          </button>
        </div>
      </form>
    </ModalFullscreen>
  );
}

// ─────────────────────────────────────────────────────────────────────────
//                         MODAL DETTAGLIO ORDINE
// ─────────────────────────────────────────────────────────────────────────

function OrdineDettaglioModal({ ordine, onClose }) {
  const c = ordine.cliente_dati;
  const a = ordine.agente_dati;

  return (
    <ModalFullscreen
      onClose={onClose}
      title={`Ordine #${ordine.numero}`}
      subtitle={`Creato il ${fmtDate(ordine.data)}`}
    >
      <div className="space-y-5">
        <div className="flex items-center gap-3">
          <span className={`badge ${STATO_BADGE[ordine.stato] || 'badge-amber'}`}>
            {ordine.stato_display || ordine.stato}
          </span>
          {ordine.pacco_arrivato && (
            <span className="badge bg-olive-100 text-olive-800 border border-olive-200 inline-flex items-center gap-1">
              <PackageCheck className="w-3 h-3" /> Pacco arrivato
            </span>
          )}
          {ordine.fattura_pagata && (
            <span className="badge bg-olive-100 text-olive-800 border border-olive-200 inline-flex items-center gap-1">
              <Receipt className="w-3 h-3" /> Fattura pagata
            </span>
          )}
          {ordine.tracking_number && (
            <span className="badge bg-blue-50 text-blue-700 border border-blue-200 inline-flex items-center gap-1">
              <Truck className="w-3 h-3" /> {ordine.tracking_number}
            </span>
          )}
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <SezioneCard icon={User} title="Cliente">
            {c ? (
              <div className="text-sm space-y-1">
                {c.azienda && <div><span className="text-bark-500">Azienda:</span> <span className="font-semibold">{c.azienda}</span></div>}
                <div><span className="text-bark-500">Nome:</span> {c.nome}</div>
                {c.via && <div><span className="text-bark-500">Indirizzo:</span> {c.via}</div>}
                {c.partita_iva && <div><span className="text-bark-500">P. IVA:</span> {c.partita_iva}</div>}
                {c.telefono && <div><span className="text-bark-500">Tel:</span> {c.telefono}</div>}
                {c.email && <div><span className="text-bark-500">Email:</span> {c.email}</div>}
              </div>
            ) : '—'}
          </SezioneCard>

          <SezioneCard icon={UserCog} title="Agente">
            {a ? (
              <div className="text-sm space-y-1">
                <div className="font-semibold">{a.cognome} {a.nome}</div>
                {a.telefono && <div><span className="text-bark-500">Tel:</span> {a.telefono}</div>}
                {a.email && <div><span className="text-bark-500">Email:</span> {a.email}</div>}
              </div>
            ) : <p className="text-bark-400 text-sm">Nessun agente associato</p>}
          </SezioneCard>
        </div>

        <SezioneCard icon={Wine} title={`Bottiglie (${ordine.righe_bottiglie?.length || 0})`}>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Tipologia</th>
                  <th className="table-header">Etich.</th>
                  <th className="table-header">Caps.</th>
                  <th className="table-header text-right">Qtà</th>
                  <th className="table-header text-right">€/bott.</th>
                  <th className="table-header text-right">Subtotale</th>
                </tr>
              </thead>
              <tbody>
                {(ordine.righe_bottiglie || []).map(r => (
                  <tr key={r.id} className="border-b border-bark-50">
                    <td className="table-cell font-semibold">{r.tipologia_vino_nome}</td>
                    <td className="table-cell">{r.ha_etichetta ? '✓' : '—'}</td>
                    <td className="table-cell">{r.ha_capsula ? '✓' : '—'}</td>
                    <td className="table-cell text-right">{r.quantita}</td>
                    <td className="table-cell text-right">{fmtCurrency(r.prezzo_unitario)}</td>
                    <td className="table-cell text-right font-semibold text-wine-700">{fmtCurrency(r.subtotale)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </SezioneCard>

        {!!(ordine.righe_gadget?.length) && (
          <SezioneCard icon={Gift} title={`Gadget omaggio (${ordine.righe_gadget.length})`}>
            <ul className="text-sm space-y-1">
              {ordine.righe_gadget.map(r => (
                <li key={r.id} className="flex justify-between border-b border-bark-50 py-1">
                  <span>{r.tipo_gadget_nome}</span>
                  <span className="font-semibold">× {r.quantita}</span>
                </li>
              ))}
            </ul>
          </SezioneCard>
        )}

        {ordine.note && (
          <SezioneCard title="Note">
            <p className="text-sm whitespace-pre-line">{ordine.note}</p>
          </SezioneCard>
        )}

        <div className="bg-gradient-to-br from-bark-50 to-wine-50/50 rounded-xl p-5 border border-bark-100">
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-xs text-bark-500">Imponibile lordo</p>
              <p className="font-display font-bold text-bark-800">{fmtCurrency(ordine.imponibile_lordo)}</p>
            </div>
            <div>
              <p className="text-xs text-bark-500">Sconto ({ordine.sconto_percentuale}%)</p>
              <p className="font-display font-bold text-amber-700">– {fmtCurrency(ordine.importo_sconto)}</p>
            </div>
            <div>
              <p className="text-xs text-bark-500">IVA ({ordine.aliquota_iva}%)</p>
              <p className="font-display font-bold text-bark-800">{fmtCurrency(ordine.importo_iva)}</p>
            </div>
            <div className="bg-wine-700 text-white rounded-lg py-2">
              <p className="text-xs opacity-80">Totale</p>
              <p className="font-display font-bold text-lg">{fmtCurrency(ordine.totale)}</p>
            </div>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button onClick={onClose} className="btn-secondary">Chiudi</button>
        </div>
      </div>
    </ModalFullscreen>
  );
}

// ─────────────────────────────────────────────────────────────────────────
//                          Componenti di supporto
// ─────────────────────────────────────────────────────────────────────────

function SezioneCard({ icon: Icon, title, required, children }) {
  return (
    <div className="bg-white rounded-xl border border-bark-100 p-4">
      <h3 className="text-sm font-bold text-bark-700 mb-3 flex items-center gap-2">
        {Icon && <Icon className="w-4 h-4 text-wine-600" />}
        {title}
        {required && <span className="text-red-500">*</span>}
      </h3>
      {children}
    </div>
  );
}

/**
 * Modal a tutta larghezza (più grande di quello base in components/Modal).
 * Replica lo stile ma offre più spazio per form complessi.
 */
function ModalFullscreen({ title, subtitle, children, onClose }) {
  return (
    <div className="fixed inset-0 z-50 flex items-start sm:items-center justify-center p-2 sm:p-4">
      <div className="absolute inset-0 bg-bark-950/40 backdrop-blur-sm" onClick={onClose} />
      <div className="relative bg-[#faf8f5] rounded-2xl shadow-2xl animate-fade-in
        w-full max-w-5xl max-h-[95vh] flex flex-col">
        <div className="flex items-start justify-between px-6 py-4 border-b border-bark-100 bg-white rounded-t-2xl">
          <div>
            <h3 className="font-display text-xl font-semibold text-bark-900">{title}</h3>
            {subtitle && <p className="text-xs text-bark-500 mt-0.5">{subtitle}</p>}
          </div>
          <button onClick={onClose}
            className="p-1.5 rounded-lg hover:bg-bark-100 transition-colors">
            <XCircle className="w-5 h-5 text-bark-500" />
          </button>
        </div>
        <div className="px-6 py-5 overflow-y-auto flex-1">
          {children}
        </div>
      </div>
    </div>
  );
}
