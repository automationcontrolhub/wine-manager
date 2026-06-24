import React, { useEffect, useState } from 'react';
import toast from 'react-hot-toast';
import {
  Plus, Trash2, Settings, Package, Hexagon, Circle, Tag, ShieldCheck,
  Grape, Edit3, Gift, Users, UserCog, Wine,
} from 'lucide-react';
import Modal from '../components/Modal';
import { useConfirm } from '../components/ConfirmDialog';
import {
  tipoCartone, tipoTappo, tipoBottiglia,
  tipoEtichetta, tipoCapsula, tipoCestello, tipoGadget,
  clienti, agenti, geografia,
} from '../api/client';
import { TipologieVinoContent } from './TipologieVino';

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
  {
    key: 'gadget', label: 'Gadget', icon: Gift, api: tipoGadget,
    campi: [{ name: 'nome', label: 'Nome', type: 'text', required: true }],
    colonne: ['nome', 'quantita'],
    colonneLabel: ['Nome', 'Scorta'],
  },
  // ── Vini (tab speciale: renderizza TipologieVinoContent) ─────────────
  {
    key: 'vino', label: 'Vini', icon: Wine, isVino: true,
  },
  // ── Anagrafiche ──────────────────────────────────────────────────────
  {
    key: 'cliente', label: 'Clienti', icon: Users, api: clienti, isAnagrafica: true,
    isClienteCustom: true,
    campi: [],
    colonne: ['azienda', 'nome', 'citta_nome', 'provincia_sigla', 'partita_iva', 'telefono'],
    colonneLabel: ['Azienda', 'Nome', 'Città', 'Prov.', 'P. IVA', 'Telefono'],
    singolare: 'cliente',
  },
  {
    key: 'agente', label: 'Agenti', icon: UserCog, api: agenti, isAnagrafica: true,
    campi: [
      { name: 'nome', label: 'Nome', type: 'text', required: true },
      { name: 'cognome', label: 'Cognome', type: 'text', required: true },
      { name: 'telefono', label: 'Telefono', type: 'tel' },
      { name: 'email', label: 'Email', type: 'email' },
      { name: 'note', label: 'Note', type: 'textarea' },
    ],
    colonne: ['cognome', 'nome', 'telefono', 'email'],
    colonneLabel: ['Cognome', 'Nome', 'Telefono', 'Email'],
    singolare: 'agente',
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

  // Carica solo le sezioni che hanno un'api (cioè non 'vino')
  const sezioniDati = SEZIONI.filter(s => s.api);

  const loadAll = async () => {
    setLoading(true);
    const responses = await Promise.all(sezioniDati.map(sez => sez.api.list().catch(() => [])));
    const results = {};
    sezioniDati.forEach((sez, i) => {
      const res = responses[i];
      results[sez.key] = Array.isArray(res) ? res : (res.results || []);
    });
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
    if (currentSection?.isClienteCustom) {
      setForm({
        azienda: item.azienda ?? '',
        nome: item.nome ?? '',
        paese: item.paese ?? '',
        regione: item.regione ?? '',
        provincia: item.provincia ?? '',
        citta: item.citta ?? '',
        cap: item.cap ?? '',
        via: item.via ?? '',
        partita_iva: item.partita_iva ?? '',
        telefono: item.telefono ?? '',
        email: item.email ?? '',
        note: item.note ?? '',
      });
    } else {
      const initialForm = {};
      currentSection.campi.forEach(c => {
        initialForm[c.name] = item[c.name] ?? '';
      });
      setForm(initialForm);
    }
    setShowModal(true);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Normalizza i campi FK vuoti a null
      const payload = { ...form };
      if (currentSection?.isClienteCustom) {
        ['paese', 'regione', 'provincia', 'citta'].forEach(k => {
          if (payload[k] === '' || payload[k] === undefined) payload[k] = null;
          else if (payload[k] != null) payload[k] = Number(payload[k]);
        });
      }
      if (editingId) {
        await currentSection.api.update(editingId, payload);
        toast.success(`${labelSingolare(currentSection)} aggiornato!`);
      } else {
        await currentSection.api.create(payload);
        toast.success(`${labelSingolare(currentSection)} creato!`);
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
    const sing = labelSingolare(currentSection);
    const nomeItem = item.nome || item.azienda || `#${item.id}`;
    const ok = await confirm({
      title: `Elimina ${sing}`,
      message: `Stai per eliminare "${nomeItem}". Questa azione non può essere annullata.\n\nNota: l'eliminazione fallirà se è in uso (es: cliente con ordini, agente associato a ordini).`,
      confirmLabel: 'Elimina',
      variant: 'danger',
    });
    if (!ok) return;
    try {
      await currentSection.api.delete(item.id);
      toast.success('Eliminato!');
      loadAll();
    } catch {
      toast.error("Impossibile eliminare: potrebbe essere in uso (ad esempio in un ordine o in una tipologia di vino).");
    }
  };

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  const items = data[activeTab] || [];

  // Raggruppamento tab in 3 categorie
  const tabsMateriali = SEZIONI.filter(s => !s.isAnagrafica && !s.isVino);
  const tabsVino = SEZIONI.filter(s => s.isVino);
  const tabsAnagrafica = SEZIONI.filter(s => s.isAnagrafica);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title flex items-center gap-3">
          <Settings className="w-8 h-8 text-bark-400" />
          Configurazione
        </h1>
        <p className="text-bark-500">Gestisci tipologie di materiali, vini, clienti e agenti</p>
      </div>

      {/* Tabs materiali */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-bark-500 mb-2">Materiali</p>
        <div className="flex gap-1 bg-bark-100 rounded-xl p-1 flex-wrap">
          {tabsMateriali.map(sez => (
            <TabButton key={sez.key} sez={sez} active={activeTab === sez.key}
              count={(data[sez.key] || []).length}
              onClick={() => setActiveTab(sez.key)} />
          ))}
        </div>
      </div>

      {/* Tabs vino */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-bark-500 mb-2">Vino</p>
        <div className="flex gap-1 bg-bark-100 rounded-xl p-1 flex-wrap">
          {tabsVino.map(sez => (
            <TabButton key={sez.key} sez={sez} active={activeTab === sez.key}
              onClick={() => setActiveTab(sez.key)} />
          ))}
        </div>
      </div>

      {/* Tabs anagrafica */}
      <div>
        <p className="text-xs font-bold uppercase tracking-wider text-bark-500 mb-2">Anagrafica</p>
        <div className="flex gap-1 bg-bark-100 rounded-xl p-1 flex-wrap">
          {tabsAnagrafica.map(sez => (
            <TabButton key={sez.key} sez={sez} active={activeTab === sez.key}
              count={(data[sez.key] || []).length}
              onClick={() => setActiveTab(sez.key)} />
          ))}
        </div>
      </div>

      {/* Contenuto sezione attiva */}
      {currentSection?.isVino ? (
        <div className="animate-fade-in">
          <TipologieVinoContent embedded={true} />
        </div>
      ) : (
        <div className="card animate-fade-in">
          <div className="flex items-center justify-between mb-4">
            <h2 className="section-title mb-0 flex items-center gap-2">
              {React.createElement(currentSection.icon, { className: 'w-5 h-5 text-wine-600' })}
              {currentSection.label}
            </h2>
            <button onClick={openCreate} className="btn-primary flex items-center gap-2">
              <Plus className="w-4 h-4" />
              {currentSection.isAnagrafica ? `Nuovo ${labelSingolare(currentSection)}` : 'Aggiungi'}
            </button>
          </div>

          {items.length === 0 ? (
            <div className="text-center py-8">
              {React.createElement(currentSection.icon, { className: 'w-12 h-12 text-bark-300 mx-auto mb-3' })}
              <p className="text-bark-500">
                {currentSection.isAnagrafica
                  ? `Nessun ${labelSingolare(currentSection)} configurato.`
                  : `Nessun tipo di ${currentSection.label.toLowerCase()} configurato.`}
              </p>
              <p className="text-bark-400 text-sm mt-1">
                Clicca "{currentSection.isAnagrafica ? `Nuovo ${labelSingolare(currentSection)}` : 'Aggiungi'}" per crearne uno.
              </p>
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
                          (col === 'nome' || col === 'azienda' || col === 'cognome') ? 'font-semibold text-bark-900' : ''
                        }`}>
                          {col === 'quantita' ? (
                            <span className={item[col] > 0 ? 'text-olive-700' : 'text-red-500'}>
                              {item[col]?.toLocaleString('it-IT')}
                            </span>
                          ) : (
                            item[col] || <span className="text-bark-300">—</span>
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
      )}

      {!currentSection?.isVino && (
        <Modal open={showModal} onClose={() => setShowModal(false)}
          wide={currentSection?.isAnagrafica}
          title={editingId
            ? `Modifica ${labelSingolare(currentSection)}`
            : currentSection?.isAnagrafica
              ? `Nuovo ${labelSingolare(currentSection)}`
              : `Nuovo tipo di ${labelSingolare(currentSection)}`}>
          {currentSection?.isClienteCustom ? (
            <ClienteForm
              form={form}
              setForm={setForm}
              editingId={editingId}
              onSubmit={handleSubmit}
              onCancel={() => setShowModal(false)}
            />
          ) : (
            <form onSubmit={handleSubmit} className="space-y-4">
              <div className={currentSection?.isAnagrafica ? 'grid grid-cols-1 sm:grid-cols-2 gap-4' : 'space-y-4'}>
                {currentSection?.campi.map(campo => (
                  <div key={campo.name} className={campo.type === 'textarea' ? 'sm:col-span-2' : ''}>
                    <label className="label">{campo.label}{campo.required && ' *'}</label>
                    {campo.type === 'textarea' ? (
                      <textarea
                        className="input-field min-h-[80px]"
                        placeholder={campo.label}
                        value={form[campo.name] ?? ''}
                        onChange={e => setForm({ ...form, [campo.name]: e.target.value })}
                      />
                    ) : (
                      <input
                        type={campo.type}
                        step={campo.step}
                        required={campo.required}
                        className="input-field"
                        placeholder={campo.label}
                        value={form[campo.name] ?? ''}
                        onChange={e => setForm({ ...form, [campo.name]: e.target.value })}
                      />
                    )}
                  </div>
                ))}
              </div>
              <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
                <button type="button" onClick={() => setShowModal(false)} className="btn-secondary">Annulla</button>
                <button type="submit" className="btn-primary">
                  {editingId ? 'Salva Modifiche' : 'Crea'}
                </button>
              </div>
            </form>
          )}
        </Modal>
      )}
    </div>
  );
}

// ─── Componente ClienteForm con select gerarchici ──────────────────────────

function ClienteForm({ form, setForm, editingId, onSubmit, onCancel }) {
  const [paesi, setPaesi] = React.useState([]);
  const [regioni, setRegioni] = React.useState([]);
  const [province, setProvince] = React.useState([]);
  const [citta, setCitta] = React.useState([]);
  const [loadingGeo, setLoadingGeo] = React.useState(true);

  React.useEffect(() => {
    geografia.paesi().then(setPaesi).catch(() => {
      toast.error('Errore caricamento paesi');
    }).finally(() => setLoadingGeo(false));
  }, []);

  React.useEffect(() => {
    if (!form.paese) {
      setRegioni([]);
      return;
    }
    geografia.regioni(form.paese).then(setRegioni).catch(() => setRegioni([]));
  }, [form.paese]);

  React.useEffect(() => {
    if (!form.regione) {
      setProvince([]);
      return;
    }
    geografia.province(form.regione).then(setProvince).catch(() => setProvince([]));
  }, [form.regione]);

  React.useEffect(() => {
    if (!form.provincia) {
      setCitta([]);
      return;
    }
    geografia.citta(form.provincia).then(setCitta).catch(() => setCitta([]));
  }, [form.provincia]);

  const cittaSelezionata = citta.find(c => c.id === Number(form.citta));
  const capDisponibili = cittaSelezionata?.cap_list || [];

  const onChangePaese = (v) => {
    setForm({ ...form, paese: v, regione: '', provincia: '', citta: '', cap: '' });
  };
  const onChangeRegione = (v) => {
    setForm({ ...form, regione: v, provincia: '', citta: '', cap: '' });
  };
  const onChangeProvincia = (v) => {
    setForm({ ...form, provincia: v, citta: '', cap: '' });
  };
  const onChangeCitta = (v) => {
    const c = citta.find(x => x.id === Number(v));
    const caps = c?.cap_list || [];
    const capDefault = caps.length === 1 ? caps[0] : '';
    setForm({ ...form, citta: v, cap: capDefault });
  };

  return (
    <form onSubmit={onSubmit} className="space-y-4">
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Azienda</label>
          <input type="text" className="input-field" placeholder="Azienda"
            value={form.azienda ?? ''}
            onChange={e => setForm({ ...form, azienda: e.target.value })} />
        </div>
        <div>
          <label className="label">Nome / Referente *</label>
          <input type="text" required className="input-field" placeholder="Nome"
            value={form.nome ?? ''}
            onChange={e => setForm({ ...form, nome: e.target.value })} />
        </div>
      </div>

      <div className="bg-bark-50/50 p-4 rounded-lg space-y-3 border border-bark-100">
        <p className="text-xs font-bold uppercase tracking-wider text-bark-500">Indirizzo</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          <div>
            <label className="label">Paese</label>
            <select className="select-field" value={form.paese ?? ''}
              onChange={e => onChangePaese(e.target.value)}
              disabled={loadingGeo}>
              <option value="">— Seleziona paese —</option>
              {paesi.map(p => (
                <option key={p.id} value={p.id}>{p.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Regione</label>
            <select className="select-field" value={form.regione ?? ''}
              onChange={e => onChangeRegione(e.target.value)}
              disabled={!form.paese || regioni.length === 0}>
              <option value="">— Seleziona regione —</option>
              {regioni.map(r => (
                <option key={r.id} value={r.id}>{r.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Provincia</label>
            <select className="select-field" value={form.provincia ?? ''}
              onChange={e => onChangeProvincia(e.target.value)}
              disabled={!form.regione || province.length === 0}>
              <option value="">— Seleziona provincia —</option>
              {province.map(p => (
                <option key={p.id} value={p.id}>
                  {p.nome}{p.sigla ? ` (${p.sigla})` : ''}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">Città</label>
            <select className="select-field" value={form.citta ?? ''}
              onChange={e => onChangeCitta(e.target.value)}
              disabled={!form.provincia || citta.length === 0}>
              <option value="">— Seleziona città —</option>
              {citta.map(c => (
                <option key={c.id} value={c.id}>{c.nome}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="label">CAP</label>
            {capDisponibili.length > 1 ? (
              <select className="select-field" value={form.cap ?? ''}
                onChange={e => setForm({ ...form, cap: e.target.value })}>
                <option value="">— Seleziona CAP —</option>
                {capDisponibili.map(cap => (
                  <option key={cap} value={cap}>{cap}</option>
                ))}
              </select>
            ) : (
              <input type="text" className="input-field"
                placeholder={capDisponibili[0] || 'CAP'}
                value={form.cap ?? ''}
                onChange={e => setForm({ ...form, cap: e.target.value })} />
            )}
          </div>

          <div>
            <label className="label">Via, numero civico</label>
            <input type="text" className="input-field" placeholder="Via Roma, 12"
              value={form.via ?? ''}
              onChange={e => setForm({ ...form, via: e.target.value })} />
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        <div>
          <label className="label">Partita IVA</label>
          <input type="text" className="input-field" placeholder="Partita IVA"
            value={form.partita_iva ?? ''}
            onChange={e => setForm({ ...form, partita_iva: e.target.value })} />
        </div>
        <div>
          <label className="label">Telefono</label>
          <input type="tel" className="input-field" placeholder="Telefono"
            value={form.telefono ?? ''}
            onChange={e => setForm({ ...form, telefono: e.target.value })} />
        </div>
        <div className="sm:col-span-2">
          <label className="label">Email</label>
          <input type="email" className="input-field" placeholder="Email"
            value={form.email ?? ''}
            onChange={e => setForm({ ...form, email: e.target.value })} />
        </div>
        <div className="sm:col-span-2">
          <label className="label">Note</label>
          <textarea className="input-field min-h-[80px]" placeholder="Note"
            value={form.note ?? ''}
            onChange={e => setForm({ ...form, note: e.target.value })} />
        </div>
      </div>

      <div className="flex justify-end gap-3 pt-4 border-t border-bark-100">
        <button type="button" onClick={onCancel} className="btn-secondary">Annulla</button>
        <button type="submit" className="btn-primary">
          {editingId ? 'Salva Modifiche' : 'Crea'}
        </button>
      </div>
    </form>
  );
}

// ─── Helpers ───────────────────────────────────────────────────────────────

function labelSingolare(sez) {
  if (!sez) return '';
  if (sez.singolare) return sez.singolare;
  return sez.label.toLowerCase().replace(/i$/, 'o').replace(/e$/, 'a');
}

function TabButton({ sez, active, count, onClick }) {
  const Icon = sez.icon;
  return (
    <button
      onClick={onClick}
      className={`flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-semibold transition-all duration-200
        ${active
          ? 'bg-white text-bark-900 shadow-sm'
          : 'text-bark-500 hover:text-bark-700'
        }`}
    >
      <Icon className="w-4 h-4" />
      {sez.label}
      {count !== undefined && (
        <span className={`text-xs px-1.5 py-0.5 rounded-full ${
          active ? 'bg-bark-100 text-bark-600' : 'bg-bark-200/50 text-bark-400'
        }`}>
          {count}
        </span>
      )}
    </button>
  );
}
