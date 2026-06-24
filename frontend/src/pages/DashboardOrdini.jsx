import React, { useEffect, useMemo, useState } from 'react';
import toast from 'react-hot-toast';
import {
  BarChart3, Receipt, Users, UserCog, Wine as WineIcon, CreditCard,
  TrendingUp, ShoppingCart, Package, CheckCircle2, XCircle,
  Calendar, Filter as FilterIcon, RefreshCcw, Trophy, Medal, Award,
} from 'lucide-react';
import {
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip,
  ResponsiveContainer, PieChart, Pie, Cell, Legend,
} from 'recharts';
import { dashboardOrdini } from '../api/client';

/* ─── Utilities ──────────────────────────────────────────────────────── */

const fmtEUR = (v) =>
  Number(v ?? 0).toLocaleString('it-IT', {
    style: 'currency', currency: 'EUR', maximumFractionDigits: 2,
  });

const fmtInt = (v) => Number(v ?? 0).toLocaleString('it-IT');

const fmtDate = (iso) => {
  if (!iso) return '—';
  try {
    return new Date(iso).toLocaleDateString('it-IT', {
      day: '2-digit', month: '2-digit', year: 'numeric',
    });
  } catch { return '—'; }
};

/* Colori coerenti con il design system Tailwind */
const COLORS = {
  wine: '#ab2049', wineLight: '#df4d6f',
  olive: '#566124', oliveLight: '#90a039',
  bark: '#583f31', barkLight: '#ac855a',
  amber: '#d97706', amberLight: '#f59e0b',
};

/* Tronca un nome lungo aggiungendo ellipsis */
const truncate = (s, max = 22) => {
  if (!s) return '';
  return s.length > max ? `${s.slice(0, max - 1)}…` : s;
};

/* Tronca un nome ma più aggressivamente (per assi piccoli) */
const truncateShort = (s, max = 18) => truncate(s, max);

/* Custom label per Pie chart: posiziona dentro la fetta se grande,
   fuori con linea se piccola. Riduce il rischio di tagli sui bordi. */
function PieLabelLine({ cx, cy, midAngle, innerRadius, outerRadius, percent, name, value, showValue = false }) {
  if (percent < 0.04) return null; // fette minuscole: nascondi label
  const RADIAN = Math.PI / 180;
  // Posizione DENTRO la fetta
  const radius = innerRadius + (outerRadius - innerRadius) * 0.5;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  const pct = (percent * 100).toFixed(0);
  return (
    <text
      x={x} y={y}
      fill="#fff"
      textAnchor="middle"
      dominantBaseline="central"
      style={{ fontSize: 13, fontWeight: 700 }}
    >
      {pct}%
    </text>
  );
}

/* ─── Filtri globali ─────────────────────────────────────────────────── */

const PERIODI = [
  { value: '', label: 'Tutto' },
  { value: 'oggi', label: 'Oggi' },
  { value: 'settimana', label: 'Settimana' },
  { value: 'mese', label: 'Mese' },
  { value: 'trimestre', label: 'Trimestre' },
  { value: 'semestre', label: 'Semestre' },
  { value: 'anno', label: 'Anno' },
  { value: 'personalizzato', label: 'Personalizzato' },
];

function FiltriGlobali({ filtri, setFiltri, opzioni }) {
  const update = (k, v) => setFiltri(prev => ({ ...prev, [k]: v }));

  // Cascata geografica
  const regioniDisp = useMemo(() => {
    if (!filtri.paese_id) return opzioni.regioni || [];
    return (opzioni.regioni || []).filter(r => String(r.paese_id) === String(filtri.paese_id));
  }, [filtri.paese_id, opzioni.regioni]);

  const provinceDisp = useMemo(() => {
    if (!filtri.regione_id) return opzioni.province || [];
    return (opzioni.province || []).filter(p => String(p.regione_id) === String(filtri.regione_id));
  }, [filtri.regione_id, opzioni.province]);

  const tipologieDisp = useMemo(() => {
    if (!filtri.famiglia_id) return opzioni.tipologie_vino || [];
    return (opzioni.tipologie_vino || []).filter(
      t => String(t.famiglia_id) === String(filtri.famiglia_id)
    );
  }, [filtri.famiglia_id, opzioni.tipologie_vino]);

  const reset = () => setFiltri({
    periodo: '', date_from: '', date_to: '',
    cliente_id: '', agente_id: '',
    paese_id: '', regione_id: '', provincia_id: '',
    famiglia_id: '', tipologia_id: '',
  });

  const someActive = Object.entries(filtri).some(
    ([k, v]) => v !== '' && v !== null && v !== undefined
  );

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="flex items-center gap-2 text-sm font-bold text-bark-700 uppercase tracking-wider">
          <FilterIcon className="w-4 h-4" /> Filtri globali
        </h3>
        {someActive && (
          <button
            onClick={reset}
            className="flex items-center gap-1.5 text-xs font-semibold text-wine-700 hover:text-wine-900"
            title="Reimposta tutti i filtri"
          >
            <RefreshCcw className="w-3.5 h-3.5" /> Reimposta
          </button>
        )}
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Periodo */}
        <div>
          <label className="label flex items-center gap-1.5">
            <Calendar className="w-3.5 h-3.5" /> Periodo
          </label>
          <select
            className="select-field"
            value={filtri.periodo}
            onChange={(e) => update('periodo', e.target.value)}
          >
            {PERIODI.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
          </select>
        </div>

        {filtri.periodo === 'personalizzato' && (
          <>
            <div>
              <label className="label">Da</label>
              <input
                type="date"
                className="input-field"
                value={filtri.date_from}
                onChange={(e) => update('date_from', e.target.value)}
              />
            </div>
            <div>
              <label className="label">A</label>
              <input
                type="date"
                className="input-field"
                value={filtri.date_to}
                onChange={(e) => update('date_to', e.target.value)}
              />
            </div>
          </>
        )}

        {/* Cliente */}
        <div>
          <label className="label">Cliente</label>
          <select
            className="select-field"
            value={filtri.cliente_id}
            onChange={(e) => update('cliente_id', e.target.value)}
          >
            <option value="">Tutti</option>
            {(opzioni.clienti || []).map(c => (
              <option key={c.id} value={c.id}>
                {c.azienda || c.nome}{c.azienda && c.nome ? ` — ${c.nome}` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Agente */}
        <div>
          <label className="label">Agente</label>
          <select
            className="select-field"
            value={filtri.agente_id}
            onChange={(e) => update('agente_id', e.target.value)}
          >
            <option value="">Tutti</option>
            {(opzioni.agenti || []).map(a => (
              <option key={a.id} value={a.id}>{a.cognome} {a.nome}</option>
            ))}
          </select>
        </div>

        {/* Paese */}
        <div>
          <label className="label">Paese</label>
          <select
            className="select-field"
            value={filtri.paese_id}
            onChange={(e) => {
              update('paese_id', e.target.value);
              update('regione_id', '');
              update('provincia_id', '');
            }}
          >
            <option value="">Tutti</option>
            {(opzioni.paesi || []).map(p => (
              <option key={p.id} value={p.id}>{p.nome}</option>
            ))}
          </select>
        </div>

        {/* Regione */}
        <div>
          <label className="label">Regione</label>
          <select
            className="select-field"
            value={filtri.regione_id}
            onChange={(e) => {
              update('regione_id', e.target.value);
              update('provincia_id', '');
            }}
          >
            <option value="">Tutte</option>
            {regioniDisp.map(r => (
              <option key={r.id} value={r.id}>{r.nome}</option>
            ))}
          </select>
        </div>

        {/* Provincia */}
        <div>
          <label className="label">Provincia</label>
          <select
            className="select-field"
            value={filtri.provincia_id}
            onChange={(e) => update('provincia_id', e.target.value)}
          >
            <option value="">Tutte</option>
            {provinceDisp.map(p => (
              <option key={p.id} value={p.id}>
                {p.nome}{p.sigla ? ` (${p.sigla})` : ''}
              </option>
            ))}
          </select>
        </div>

        {/* Famiglia vino */}
        <div>
          <label className="label">Famiglia vino</label>
          <select
            className="select-field"
            value={filtri.famiglia_id}
            onChange={(e) => {
              update('famiglia_id', e.target.value);
              update('tipologia_id', '');
            }}
          >
            <option value="">Tutte</option>
            {(opzioni.famiglie_vino || []).map(f => (
              <option key={f.id} value={f.id}>{f.nome}</option>
            ))}
          </select>
        </div>

        {/* Tipologia vino */}
        <div>
          <label className="label">Tipologia vino</label>
          <select
            className="select-field"
            value={filtri.tipologia_id}
            onChange={(e) => update('tipologia_id', e.target.value)}
          >
            <option value="">Tutte</option>
            {tipologieDisp.map(t => (
              <option key={t.id} value={t.id}>
                {t.famiglia__nome ? `${t.famiglia__nome} — ` : ''}{t.nome}
              </option>
            ))}
          </select>
        </div>
      </div>
    </div>
  );
}

/* ─── Card riusabili ─────────────────────────────────────────────────── */

function StatCard({ icon: Icon, label, value, sub, color = 'bg-wine-100 text-wine-700' }) {
  return (
    <div className="card flex items-start gap-4 animate-fade-in">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div className="min-w-0">
        <p className="text-sm text-bark-500 font-medium">{label}</p>
        <p className="text-2xl font-display font-bold text-bark-900 break-all">{value}</p>
        {sub && <p className="text-xs text-bark-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center h-40">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );
}

function EmptyState({ msg = 'Nessun dato per i filtri selezionati.' }) {
  return <p className="text-bark-400 text-sm italic py-6 text-center">{msg}</p>;
}

/* ─── Hook generico per fetch con filtri ─────────────────────────────── */

function buildParams(filtri) {
  const p = {};
  for (const [k, v] of Object.entries(filtri)) {
    if (v !== '' && v !== null && v !== undefined) p[k] = v;
  }
  // se periodo non è personalizzato, ignoriamo date_from/date_to
  if (p.periodo !== 'personalizzato') {
    delete p.date_from;
    delete p.date_to;
  }
  return p;
}

function useDashboardFetch(fetcher, filtri) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const params = useMemo(() => buildParams(filtri), [filtri]);
  const paramsKey = useMemo(() => JSON.stringify(params), [params]);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setError(null);
    fetcher(params)
      .then(d => { if (!cancelled) setData(d); })
      .catch(e => {
        if (!cancelled) {
          setError(e);
          toast.error('Errore nel caricamento della dashboard');
        }
      })
      .finally(() => { if (!cancelled) setLoading(false); });
    return () => { cancelled = true; };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [paramsKey]);

  return { data, loading, error };
}

/* ─── Dashboard 1: Commerciale Generale ──────────────────────────────── */

function TabCommerciale({ filtri }) {
  const { data, loading } = useDashboardFetch(dashboardOrdini.commerciale, filtri);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  const { kpi_fissi: K, periodo, trend_anno } = data;

  const pieData = [
    { name: 'Pagati', value: periodo.n_pagati },
    { name: 'Non pagati', value: periodo.n_non_pagati },
  ];

  return (
    <div className="space-y-6">
      {/* KPI Mese / Anno */}
      <div>
        <h3 className="text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
          Mese corrente
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            icon={Receipt} label="Fatturato mese"
            value={fmtEUR(K.fatturato_mese)}
            color="bg-wine-100 text-wine-700"
          />
          <StatCard
            icon={ShoppingCart} label="Ordini mese"
            value={fmtInt(K.n_ordini_mese)}
            color="bg-olive-100 text-olive-700"
          />
          <StatCard
            icon={Package} label="Bottiglie mese"
            value={fmtInt(K.bottiglie_mese)}
            color="bg-bark-100 text-bark-700"
          />
        </div>
      </div>

      <div>
        <h3 className="text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
          Anno corrente
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <StatCard
            icon={Receipt} label="Fatturato anno"
            value={fmtEUR(K.fatturato_anno)}
            color="bg-wine-100 text-wine-700"
          />
          <StatCard
            icon={ShoppingCart} label="Ordini anno"
            value={fmtInt(K.n_ordini_anno)}
            color="bg-olive-100 text-olive-700"
          />
          <StatCard
            icon={Package} label="Bottiglie anno"
            value={fmtInt(K.bottiglie_anno)}
            color="bg-bark-100 text-bark-700"
          />
        </div>
      </div>

      {/* KPI periodo + percentuali pagati */}
      <div>
        <h3 className="text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
          Pagamenti — periodo selezionato
        </h3>
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <StatCard
            icon={CheckCircle2} label="% pagati"
            value={`${periodo.perc_pagati}%`}
            sub={`${fmtInt(periodo.n_pagati)} ordini`}
            color="bg-olive-100 text-olive-700"
          />
          <StatCard
            icon={XCircle} label="% non pagati"
            value={`${periodo.perc_non_pagati}%`}
            sub={`${fmtInt(periodo.n_non_pagati)} ordini`}
            color="bg-amber-100 text-amber-700"
          />
          <StatCard
            icon={Receipt} label="Fatturato periodo"
            value={fmtEUR(periodo.fatturato)}
            sub={`${fmtInt(periodo.n_ordini)} ordini`}
            color="bg-wine-100 text-wine-700"
          />
          <StatCard
            icon={Package} label="Bottiglie periodo"
            value={fmtInt(periodo.bottiglie)}
            color="bg-bark-100 text-bark-700"
          />
        </div>
      </div>

      {/* Grafici */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-2">
          <h3 className="section-title flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-wine-600" />
            Trend fatturato mensile — Anno corrente
          </h3>
          {trend_anno && trend_anno.length > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={trend_anno} margin={{ top: 10, right: 20, left: 10, bottom: 10 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee9dc" />
                  <XAxis
                    dataKey="label"
                    tick={{ fontSize: 12, fill: '#583f31' }}
                    interval={0}
                  />
                  <YAxis
                    tick={{ fontSize: 12, fill: '#583f31' }}
                    tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
                    width={60}
                  />
                  <Tooltip
                    formatter={(v) => fmtEUR(v)}
                    contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                  />
                  <Bar dataKey="fatturato" fill={COLORS.wine} radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState />}
        </div>

        <div className="card">
          <h3 className="section-title">Ordini per stato pagamento</h3>
          {periodo.n_ordini > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <Pie
                    data={pieData} cx="50%" cy="45%"
                    outerRadius={70} innerRadius={40}
                    dataKey="value"
                    labelLine={false}
                    label={PieLabelLine}
                  >
                    <Cell fill={COLORS.olive} />
                    <Cell fill={COLORS.amberLight} />
                  </Pie>
                  <Tooltip
                    formatter={(v, name) => [`${v} ordini`, name]}
                    contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                    formatter={(value, entry) => (
                      <span style={{ color: '#583f31', fontSize: 13 }}>
                        {value}: <strong>{entry.payload.value}</strong>
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState />}
        </div>
      </div>
    </div>
  );
}

/* ─── Dashboard 2: Clienti ───────────────────────────────────────────── */

function TabClienti({ filtri }) {
  const { data, loading } = useDashboardFetch(dashboardOrdini.clienti, filtri);
  const [sortKey, setSortKey] = useState('fatturato');
  const [sortDir, setSortDir] = useState('desc');

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  const totals = data.totali;
  const clienti = [...(data.clienti || [])].sort((a, b) => {
    const av = a[sortKey] ?? 0;
    const bv = b[sortKey] ?? 0;
    if (av < bv) return sortDir === 'asc' ? -1 : 1;
    if (av > bv) return sortDir === 'asc' ? 1 : -1;
    return 0;
  });

  const setSort = (key) => {
    if (sortKey === key) setSortDir(d => d === 'asc' ? 'desc' : 'asc');
    else { setSortKey(key); setSortDir('desc'); }
  };

  const topClienti = [...(data.clienti || [])]
    .sort((a, b) => b.fatturato - a.fatturato)
    .slice(0, 10)
    .map(c => ({
      name: (c.azienda || c.cliente).slice(0, 18),
      fatturato: c.fatturato,
    }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        <StatCard
          icon={Users} label="Clienti attivi"
          value={fmtInt(totals.n_clienti)}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={Receipt} label="Fatturato"
          value={fmtEUR(totals.fatturato)}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={ShoppingCart} label="Ordini"
          value={fmtInt(totals.n_ordini)}
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={Package} label="Bottiglie"
          value={fmtInt(totals.bottiglie)}
          color="bg-bark-100 text-bark-700"
        />
        <StatCard
          icon={TrendingUp} label="Valore medio ordine"
          value={fmtEUR(totals.valore_medio_ordine)}
          color="bg-amber-100 text-amber-700"
        />
      </div>

      {topClienti.length > 0 && (
        <div className="card">
          <h3 className="section-title">Top 10 clienti per fatturato</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={topClienti.map(c => ({ ...c, name: truncate(c.name, 26) }))}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#eee9dc" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: '#583f31' }}
                  tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
                />
                <YAxis
                  type="category" dataKey="name" width={180}
                  tick={{ fontSize: 12, fill: '#583f31' }}
                  interval={0}
                />
                <Tooltip
                  formatter={(v) => fmtEUR(v)}
                  contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                />
                <Bar dataKey="fatturato" fill={COLORS.wine} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="section-title">Dettaglio clienti</h3>
        {clienti.length === 0 ? <EmptyState /> : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header cursor-pointer hover:bg-bark-100" onClick={() => setSort('cliente')}>Cliente</th>
                  <th className="table-header">Provincia</th>
                  <th className="table-header text-right cursor-pointer hover:bg-bark-100" onClick={() => setSort('fatturato')}>Fatturato</th>
                  <th className="table-header text-right cursor-pointer hover:bg-bark-100" onClick={() => setSort('numero_ordini')}>Ordini</th>
                  <th className="table-header text-right cursor-pointer hover:bg-bark-100" onClick={() => setSort('bottiglie')}>Bottiglie</th>
                  <th className="table-header text-right cursor-pointer hover:bg-bark-100" onClick={() => setSort('valore_medio_ordine')}>Val. medio</th>
                  <th className="table-header text-right cursor-pointer hover:bg-bark-100" onClick={() => setSort('ultimo_ordine')}>Ultimo ordine</th>
                </tr>
              </thead>
              <tbody>
                {clienti.map(c => (
                  <tr key={c.cliente_id} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell">
                      <div className="font-semibold">{c.azienda || c.cliente}</div>
                      {c.azienda && c.cliente && <div className="text-xs text-bark-500">{c.cliente}</div>}
                    </td>
                    <td className="table-cell text-bark-600 text-sm">
                      {c.provincia || c.regione || c.paese || '—'}
                    </td>
                    <td className="table-cell text-right font-display font-bold text-wine-700">
                      {fmtEUR(c.fatturato)}
                    </td>
                    <td className="table-cell text-right">{fmtInt(c.numero_ordini)}</td>
                    <td className="table-cell text-right">{fmtInt(c.bottiglie)}</td>
                    <td className="table-cell text-right">{fmtEUR(c.valore_medio_ordine)}</td>
                    <td className="table-cell text-right text-bark-500 text-xs">
                      {fmtDate(c.ultimo_ordine)}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard 3: Agenti ────────────────────────────────────────────── */

function PodiumCard({ icon: Icon, title, item, valueFmt, colorClass }) {
  if (!item) {
    return (
      <div className="card">
        <h4 className="flex items-center gap-2 text-sm font-bold text-bark-600 uppercase tracking-wider mb-2">
          <Icon className="w-4 h-4" /> {title}
        </h4>
        <EmptyState msg="Nessun dato." />
      </div>
    );
  }
  return (
    <div className="card">
      <h4 className="flex items-center gap-2 text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
        <Icon className={`w-4 h-4 ${colorClass}`} /> {title}
      </h4>
      <p className="font-display text-xl font-bold text-bark-900">{item.agente}</p>
      <p className={`mt-1 text-2xl font-display font-bold ${colorClass}`}>
        {valueFmt(item)}
      </p>
    </div>
  );
}

function TabAgenti({ filtri }) {
  const { data, loading } = useDashboardFetch(dashboardOrdini.agenti, filtri);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  const totals = data.totali;
  const top = [...(data.classifica_fatturato || [])]
    .slice(0, 10)
    .map(a => ({ name: a.agente.slice(0, 18), fatturato: a.fatturato, bottiglie: a.bottiglie }));

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={UserCog} label="Agenti attivi"
          value={fmtInt(totals.n_agenti)}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={Receipt} label="Fatturato totale"
          value={fmtEUR(totals.fatturato)}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={ShoppingCart} label="Ordini"
          value={fmtInt(totals.n_ordini)}
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={Package} label="Bottiglie"
          value={fmtInt(totals.bottiglie)}
          color="bg-bark-100 text-bark-700"
        />
      </div>

      {/* Classifiche / Podio */}
      <div>
        <h3 className="text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">Migliori agenti</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <PodiumCard
            icon={Trophy} title="Per fatturato"
            item={data.miglior_agente_fatturato}
            valueFmt={(a) => fmtEUR(a.fatturato)}
            colorClass="text-wine-700"
          />
          <PodiumCard
            icon={Medal} title="Per bottiglie"
            item={data.miglior_agente_bottiglie}
            valueFmt={(a) => `${fmtInt(a.bottiglie)} bott.`}
            colorClass="text-olive-700"
          />
          <PodiumCard
            icon={Award} title="Per numero ordini"
            item={data.miglior_agente_ordini}
            valueFmt={(a) => `${fmtInt(a.numero_ordini)} ordini`}
            colorClass="text-amber-700"
          />
        </div>
      </div>

      {top.length > 0 && (
        <div className="card">
          <h3 className="section-title">Classifica fatturato — Top 10</h3>
          <div className="h-80">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={top.map(t => ({ ...t, name: truncate(t.name, 24) }))}
                layout="vertical"
                margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#eee9dc" />
                <XAxis
                  type="number"
                  tick={{ fontSize: 12, fill: '#583f31' }}
                  tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
                />
                <YAxis
                  type="category" dataKey="name" width={170}
                  tick={{ fontSize: 12, fill: '#583f31' }}
                  interval={0}
                />
                <Tooltip
                  formatter={(v) => fmtEUR(v)}
                  contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                />
                <Bar dataKey="fatturato" fill={COLORS.wine} radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}

      <div className="card">
        <h3 className="section-title">Tutti gli agenti</h3>
        {(data.agenti || []).length === 0 ? <EmptyState /> : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Agente</th>
                  <th className="table-header text-right">Fatturato</th>
                  <th className="table-header text-right">Bottiglie</th>
                  <th className="table-header text-right">Ordini</th>
                </tr>
              </thead>
              <tbody>
                {data.agenti.map((a, i) => (
                  <tr key={a.agente_id ?? `na-${i}`} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell font-semibold">{a.agente}</td>
                    <td className="table-cell text-right font-display font-bold text-wine-700">
                      {fmtEUR(a.fatturato)}
                    </td>
                    <td className="table-cell text-right">{fmtInt(a.bottiglie)}</td>
                    <td className="table-cell text-right">{fmtInt(a.numero_ordini)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard 4: Prodotti / Vini ───────────────────────────────────── */

function TabProdotti({ filtri, etichettato, setEtichettato }) {
  // arricchiamo i filtri con etichettato (specifico di D4)
  const fullFiltri = useMemo(() => ({
    ...filtri,
    ...(etichettato !== '' ? { etichettato } : {}),
  }), [filtri, etichettato]);

  const { data, loading } = useDashboardFetch(dashboardOrdini.prodotti, fullFiltri);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  const totals = data.totali;
  const topProdotti = (data.prodotti || []).slice(0, 10).map(p => ({
    name: p.tipologia.slice(0, 22), fatturato: p.fatturato, bottiglie: p.bottiglie,
  }));

  return (
    <div className="space-y-6">
      {/* Filtro specifico D4 — etichettato/non etichettato */}
      <div className="card">
        <h3 className="flex items-center gap-2 text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
          <FilterIcon className="w-4 h-4" /> Filtro etichetta
        </h3>
        <div className="flex gap-2">
          {[
            { v: '', label: 'Tutto' },
            { v: 'true', label: 'Etichettato' },
            { v: 'false', label: 'Non etichettato' },
          ].map(opt => (
            <button
              key={opt.v}
              onClick={() => setEtichettato(opt.v)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold transition-all ${
                etichettato === opt.v
                  ? 'bg-wine-700 text-white'
                  : 'bg-bark-100 text-bark-700 hover:bg-bark-200'
              }`}
            >
              {opt.label}
            </button>
          ))}
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <StatCard
          icon={WineIcon} label="Tipologie vendute"
          value={fmtInt(totals.n_tipologie)}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={WineIcon} label="Famiglie"
          value={fmtInt(totals.n_famiglie)}
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={Package} label="Bottiglie vendute"
          value={fmtInt(totals.bottiglie)}
          color="bg-bark-100 text-bark-700"
        />
        <StatCard
          icon={Receipt} label="Fatturato generato"
          value={fmtEUR(totals.fatturato)}
          color="bg-wine-100 text-wine-700"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {topProdotti.length > 0 && (
          <div className="card">
            <h3 className="section-title">Top 10 prodotti per fatturato</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={topProdotti.map(p => ({ ...p, name: truncate(p.name, 22) }))}
                  layout="vertical"
                  margin={{ top: 10, right: 30, left: 10, bottom: 10 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#eee9dc" />
                  <XAxis
                    type="number"
                    tick={{ fontSize: 12, fill: '#583f31' }}
                    tickFormatter={(v) => v >= 1000 ? `${(v/1000).toFixed(0)}k` : v}
                  />
                  <YAxis
                    type="category" dataKey="name" width={170}
                    tick={{ fontSize: 11, fill: '#583f31' }}
                    interval={0}
                  />
                  <Tooltip
                    formatter={(v) => fmtEUR(v)}
                    contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                  />
                  <Bar dataKey="fatturato" fill={COLORS.wine} radius={[0, 6, 6, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {(data.famiglie || []).length > 0 && (
          <div className="card">
            <h3 className="section-title">Fatturato per famiglia</h3>
            <div className="h-80">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <Pie
                    data={data.famiglie} cx="50%" cy="45%"
                    outerRadius={85} innerRadius={45}
                    dataKey="fatturato" nameKey="famiglia"
                    labelLine={false}
                    label={PieLabelLine}
                  >
                    {data.famiglie.map((_, i) => {
                      const palette = [
                        COLORS.wine, COLORS.olive, COLORS.barkLight,
                        COLORS.amberLight, COLORS.wineLight, COLORS.oliveLight, COLORS.bark,
                      ];
                      return <Cell key={i} fill={palette[i % palette.length]} />;
                    })}
                  </Pie>
                  <Tooltip
                    formatter={(v) => fmtEUR(v)}
                    contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={50}
                    iconType="circle"
                    wrapperStyle={{ fontSize: 12 }}
                    formatter={(value) => (
                      <span style={{ color: '#583f31', fontSize: 12 }}>
                        {truncate(value, 20)}
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>

      <div className="card">
        <h3 className="section-title">Dettaglio per tipologia</h3>
        {(data.prodotti || []).length === 0 ? <EmptyState /> : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Famiglia</th>
                  <th className="table-header">Tipologia</th>
                  <th className="table-header text-right">Bottiglie</th>
                  <th className="table-header text-right">Fatturato</th>
                  <th className="table-header text-right">N. ordini</th>
                </tr>
              </thead>
              <tbody>
                {data.prodotti.map(p => (
                  <tr key={p.tipologia_id} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell text-sm text-bark-600">{p.famiglia}</td>
                    <td className="table-cell font-semibold">{p.tipologia}</td>
                    <td className="table-cell text-right">{fmtInt(p.bottiglie)}</td>
                    <td className="table-cell text-right font-display font-bold text-wine-700">
                      {fmtEUR(p.fatturato)}
                    </td>
                    <td className="table-cell text-right">{fmtInt(p.n_ordini)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

/* ─── Dashboard 5: Pagamenti ─────────────────────────────────────────── */

function TabPagamenti({ filtri }) {
  const { data, loading } = useDashboardFetch(dashboardOrdini.pagamenti, filtri);

  if (loading) return <LoadingSpinner />;
  if (!data) return <EmptyState />;

  const totale = (data.totale_incassato || 0) + (data.totale_da_incassare || 0);
  const pieData = [
    { name: 'Incassato', value: data.totale_incassato },
    { name: 'Da incassare', value: data.totale_da_incassare },
  ];

  return (
    <div className="space-y-6">
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={CheckCircle2} label="Ordini pagati"
          value={fmtInt(data.n_pagati)}
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={XCircle} label="Ordini non pagati"
          value={fmtInt(data.n_non_pagati)}
          color="bg-amber-100 text-amber-700"
        />
        <StatCard
          icon={CreditCard} label="Totale incassato"
          value={fmtEUR(data.totale_incassato)}
          sub="IVA inclusa"
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={CreditCard} label="Totale da incassare"
          value={fmtEUR(data.totale_da_incassare)}
          sub="IVA inclusa"
          color="bg-wine-100 text-wine-700"
        />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card lg:col-span-1">
          <h3 className="section-title">Incassi vs da incassare</h3>
          {totale > 0 ? (
            <div className="h-72">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart margin={{ top: 5, right: 5, left: 5, bottom: 5 }}>
                  <Pie
                    data={pieData} cx="50%" cy="45%"
                    outerRadius={70} innerRadius={40}
                    dataKey="value"
                    labelLine={false}
                    label={PieLabelLine}
                  >
                    <Cell fill={COLORS.olive} />
                    <Cell fill={COLORS.amberLight} />
                  </Pie>
                  <Tooltip
                    formatter={(v) => fmtEUR(v)}
                    contentStyle={{ borderRadius: 8, border: '1px solid #ded3bb' }}
                  />
                  <Legend
                    verticalAlign="bottom"
                    height={36}
                    iconType="circle"
                    formatter={(value, entry) => (
                      <span style={{ color: '#583f31', fontSize: 13 }}>
                        {value}: <strong>{fmtEUR(entry.payload.value)}</strong>
                      </span>
                    )}
                  />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : <EmptyState />}
        </div>

        <div className="card lg:col-span-2">
          <h3 className="section-title">Ordini da incassare</h3>
          {(data.ordini_da_incassare || []).length === 0 ? (
            <EmptyState msg="Nessun ordine non pagato nel periodo." />
          ) : (
            <div className="overflow-x-auto max-h-96 overflow-y-auto">
              <table className="w-full">
                <thead className="sticky top-0 bg-white">
                  <tr className="border-b border-bark-100">
                    <th className="table-header">#</th>
                    <th className="table-header">Data</th>
                    <th className="table-header">Cliente</th>
                    <th className="table-header text-right">Totale</th>
                  </tr>
                </thead>
                <tbody>
                  {data.ordini_da_incassare.map(o => (
                    <tr key={o.ordine_id} className="border-b border-bark-50 hover:bg-bark-50/50">
                      <td className="table-cell font-semibold">#{o.numero}</td>
                      <td className="table-cell text-xs text-bark-500">{fmtDate(o.data)}</td>
                      <td className="table-cell">{o.cliente}</td>
                      <td className="table-cell text-right font-display font-bold text-wine-700">
                        {fmtEUR(o.totale)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

/* ─── Pagina principale con tab system ───────────────────────────────── */

const TABS = [
  { id: 'commerciale', label: 'Commerciale Generale', icon: BarChart3 },
  { id: 'clienti',     label: 'Clienti',              icon: Users },
  { id: 'agenti',      label: 'Agenti',               icon: UserCog },
  { id: 'prodotti',    label: 'Prodotti / Vini',      icon: WineIcon },
  { id: 'pagamenti',   label: 'Pagamenti',            icon: CreditCard },
];

export default function DashboardOrdini() {
  const [tab, setTab] = useState('commerciale');
  const [opzioni, setOpzioni] = useState({});
  const [opzioniLoading, setOpzioniLoading] = useState(true);

  const [filtri, setFiltri] = useState({
    periodo: '', date_from: '', date_to: '',
    cliente_id: '', agente_id: '',
    paese_id: '', regione_id: '', provincia_id: '',
    famiglia_id: '', tipologia_id: '',
  });

  // filtro specifico D4 (etichettato) — non condiviso con gli altri tab
  const [etichettato, setEtichettato] = useState('');

  useEffect(() => {
    dashboardOrdini.filtri()
      .then(setOpzioni)
      .catch(() => toast.error('Errore nel caricamento delle opzioni di filtro'))
      .finally(() => setOpzioniLoading(false));
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="page-title">Dashboard Ordini</h1>
        <p className="text-bark-500">
          Analisi commerciale basata sui dati registrati negli ordini
        </p>
      </div>

      {/* Filtri globali */}
      {opzioniLoading ? (
        <div className="card"><LoadingSpinner /></div>
      ) : (
        <FiltriGlobali filtri={filtri} setFiltri={setFiltri} opzioni={opzioni} />
      )}

      {/* Tab bar */}
      <div className="border-b border-bark-200 overflow-x-auto">
        <div className="flex gap-1 min-w-fit">
          {TABS.map(({ id, label, icon: Icon }) => (
            <button
              key={id}
              onClick={() => setTab(id)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-semibold whitespace-nowrap
                          transition-all border-b-2 -mb-px
                          ${tab === id
                            ? 'text-wine-700 border-wine-700'
                            : 'text-bark-500 border-transparent hover:text-bark-800 hover:border-bark-300'
                          }`}
            >
              <Icon className="w-4 h-4" /> {label}
            </button>
          ))}
        </div>
      </div>

      {/* Tab content */}
      <div className="animate-fade-in">
        {tab === 'commerciale' && <TabCommerciale filtri={filtri} />}
        {tab === 'clienti'     && <TabClienti     filtri={filtri} />}
        {tab === 'agenti'      && <TabAgenti      filtri={filtri} />}
        {tab === 'prodotti'    && (
          <TabProdotti
            filtri={filtri}
            etichettato={etichettato}
            setEtichettato={setEtichettato}
          />
        )}
        {tab === 'pagamenti'   && <TabPagamenti   filtri={filtri} />}
      </div>
    </div>
  );
}
