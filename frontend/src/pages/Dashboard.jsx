import React, { useEffect, useState } from 'react';
import { getDashboard } from '../api/client';
import {
  Wine, Package, Tag, Circle, Hexagon, ShieldCheck,
  Grape, ArrowUpCircle, ArrowDownCircle, TrendingUp
} from 'lucide-react';

function StatCard({ icon: Icon, label, value, sub, color }) {
  return (
    <div className="card flex items-start gap-4 animate-fade-in">
      <div className={`p-3 rounded-xl ${color}`}>
        <Icon className="w-6 h-6" />
      </div>
      <div>
        <p className="text-sm text-bark-500 font-medium">{label}</p>
        <p className="text-2xl font-display font-bold text-bark-900">{value}</p>
        {sub && <p className="text-xs text-bark-400 mt-0.5">{sub}</p>}
      </div>
    </div>
  );
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getDashboard().then(setData).finally(() => setLoading(false));
  }, []);

  if (loading) return (
    <div className="flex items-center justify-center h-64">
      <div className="w-8 h-8 border-3 border-wine-300 border-t-wine-700 rounded-full animate-spin" />
    </div>
  );

  if (!data) return <p className="text-bark-500">Errore nel caricamento.</p>;

  const { magazzino, silos, bottiglie, ultimi_movimenti } = data;

  const totaleLitri = silos.reduce((s, v) => s + parseFloat(v.quantita_litri), 0);

  return (
    <div className="space-y-8">
      <div>
        <h1 className="page-title">Dashboard</h1>
        <p className="text-bark-500">Panoramica della cantina</p>
      </div>

      {/* Stats top */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          icon={Grape}
          label="Vino totale nei silos"
          value={`${totaleLitri.toLocaleString('it-IT')} L`}
          sub={`${silos.length} tipologie`}
          color="bg-wine-100 text-wine-700"
        />
        <StatCard
          icon={Package}
          label="Bottiglie complete"
          value={bottiglie.complete.toLocaleString('it-IT')}
          color="bg-olive-100 text-olive-700"
        />
        <StatCard
          icon={Tag}
          label="In attesa etichetta"
          value={bottiglie.senza_etichetta.toLocaleString('it-IT')}
          color="bg-amber-100 text-amber-700"
        />
        <StatCard
          icon={TrendingUp}
          label="Movimenti recenti"
          value={ultimi_movimenti.length}
          color="bg-bark-100 text-bark-700"
        />
      </div>

      {/* Silos */}
      <div className="card">
        <h2 className="section-title flex items-center gap-2">
          <Wine className="w-5 h-5 text-wine-600" /> Silos Vino
        </h2>
        {silos.length === 0 ? (
          <p className="text-bark-400 text-sm">Nessuna tipologia di vino creata.</p>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
            {silos.map(v => (
              <div key={v.id} className="flex items-center justify-between p-4 rounded-xl bg-bark-50 border border-bark-100">
                <div>
                  <p className="font-semibold text-bark-900">{v.nome}</p>
                  <p className="text-xs text-bark-500">{v.famiglia__nome}</p>
                </div>
                <span className="text-lg font-display font-bold text-wine-700">
                  {parseFloat(v.quantita_litri).toLocaleString('it-IT')} L
                </span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Magazzino riepilogo */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {[
          { key: 'bottiglie', label: 'Bottiglie', icon: Circle },
          { key: 'tappi', label: 'Tappi', icon: Hexagon },
          { key: 'etichette', label: 'Etichette', icon: Tag },
          { key: 'capsule', label: 'Capsule', icon: ShieldCheck },
          { key: 'cartoni', label: 'Cartoni', icon: Package },
          { key: 'cestelli', label: 'Cestelli', icon: Grape },
        ].map(({ key, label, icon: Icon }) => (
          <div key={key} className="card">
            <h3 className="flex items-center gap-2 text-sm font-bold text-bark-600 uppercase tracking-wider mb-3">
              <Icon className="w-4 h-4" /> {label}
            </h3>
            {magazzino[key].length === 0 ? (
              <p className="text-bark-400 text-sm">Nessun tipo configurato.</p>
            ) : (
              <div className="space-y-2">
                {magazzino[key].map(item => (
                  <div key={item.id} className="flex justify-between items-center py-1.5 px-3 rounded-lg hover:bg-bark-50">
                    <span className="text-sm text-bark-800">{item.nome}</span>
                    <span className="font-semibold text-bark-900">{item.quantita.toLocaleString('it-IT')}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* Ultimi movimenti */}
      <div className="card">
        <h2 className="section-title">Ultimi movimenti</h2>
        {ultimi_movimenti.length === 0 ? (
          <p className="text-bark-400 text-sm">Nessun movimento registrato.</p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-bark-100">
                  <th className="table-header">Tipo</th>
                  <th className="table-header">Categoria</th>
                  <th className="table-header">Qtà</th>
                  <th className="table-header">Descrizione</th>
                  <th className="table-header">Data</th>
                </tr>
              </thead>
              <tbody>
                {ultimi_movimenti.map(m => (
                  <tr key={m.id} className="border-b border-bark-50 hover:bg-bark-50/50">
                    <td className="table-cell">
                      {m.tipo === 'CARICO' ? (
                        <span className="badge-olive flex items-center gap-1 w-fit">
                          <ArrowUpCircle className="w-3 h-3" /> Carico
                        </span>
                      ) : m.tipo === 'AGGIUNTA_VINO' ? (
                        <span className="badge-wine flex items-center gap-1 w-fit">
                          <ArrowUpCircle className="w-3 h-3" /> Aggiunta
                        </span>
                      ) : (
                        <span className="badge-amber flex items-center gap-1 w-fit">
                          <ArrowDownCircle className="w-3 h-3" /> Scarico
                        </span>
                      )}
                    </td>
                    <td className="table-cell">{m.categoria}</td>
                    <td className="table-cell font-semibold">{parseFloat(m.quantita).toLocaleString('it-IT')}</td>
                    <td className="table-cell text-bark-600">{m.descrizione}</td>
                    <td className="table-cell text-bark-500 text-xs">
                      {new Date(m.data).toLocaleString('it-IT')}
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
