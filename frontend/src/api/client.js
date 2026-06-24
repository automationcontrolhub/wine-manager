import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '/api';

const api = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
});

// ─── Materiali CRUD ──────────────────────────────────────────────────────

const materiali = (endpoint) => ({
  list: () => api.get(`/${endpoint}/`).then(r => r.data),
  create: (data) => api.post(`/${endpoint}/`, data).then(r => r.data),
  update: (id, data) => api.patch(`/${endpoint}/${id}/`, data).then(r => r.data),
  delete: (id) => api.delete(`/${endpoint}/${id}/`),
});

export const tipoCartone = materiali('tipo-cartone');
export const tipoTappo = materiali('tipo-tappo');
export const tipoBottiglia = materiali('tipo-bottiglia');
export const tipoEtichetta = materiali('tipo-etichetta');
export const tipoCapsula = materiali('tipo-capsula');
export const tipoCestello = materiali('tipo-cestello');
export const tipoGadget = materiali('tipo-gadget');

// ─── Famiglie e Tipologie vino ───────────────────────────────────────────

export const famiglie = materiali('famiglie');
export const tipologieVino = materiali('tipologie-vino');

// ─── Lotti e Movimenti ───────────────────────────────────────────────────

export const lotti = {
  list: (params) => api.get('/lotti/', { params }).then(r => r.data),
};

export const movimenti = {
  list: (params) => api.get('/movimenti/', { params }).then(r => r.data),
};

export const operazioni = {
  list: (params) => api.get('/operazioni/', { params }).then(r => r.data),
  annulla: (id) => api.post(`/operazioni/${id}/annulla/`).then(r => r.data),
};

// ─── Operazioni ──────────────────────────────────────────────────────────

export const aggiuntaVino = (data) =>
  api.post('/aggiunta-vino/', data).then(r => r.data);

export const caricoMagazzino = (data) =>
  api.post('/carico-magazzino/', data).then(r => r.data);

export const rettificaMagazzino = (data) =>
  api.post('/rettifica-magazzino/', data).then(r => r.data);

export const rettificaSilos = (data) =>
  api.post('/rettifica-silos/', data).then(r => r.data);

export const creaSenzaEtichetta = (data) =>
  api.post('/crea-senza-etichetta/', data).then(r => r.data);

export const creaConEtichetta = (data) =>
  api.post('/crea-con-etichetta/', data).then(r => r.data);

export const associaEtichetta = (data) =>
  api.post('/associa-etichetta/', data).then(r => r.data);

export const getDashboard = () =>
  api.get('/dashboard/').then(r => r.data);

export const getBottiglieSenzaEtichetta = () =>
  api.get('/bottiglie-senza-etichetta/').then(r => r.data);

// ─── Anagrafiche (clienti / agenti) ──────────────────────────────────────

export const clienti = materiali('clienti');
export const agenti = materiali('agenti');

// ─── Bottiglie disponibili per ordine ────────────────────────────────────

export const getBottiglieDisponibili = () =>
  api.get('/bottiglie-disponibili/').then(r => r.data);


// ─── Geografia ───────────────────────────────────────────────────────────

export const geografia = {
  paesi: () => api.get('/paesi/').then(r => r.data),
  regioni: (paeseId) => api.get('/regioni/', { params: paeseId ? { paese: paeseId } : {} }).then(r => r.data),
  province: (regioneId) => api.get('/province/', { params: regioneId ? { regione: regioneId } : {} }).then(r => r.data),
  citta: (provinciaId) => api.get('/citta/', { params: provinciaId ? { provincia: provinciaId } : {} }).then(r => r.data),
};

// ─── Ordini ──────────────────────────────────────────────────────────────

export const ordini = {
  list: (params) => api.get('/ordini/', { params }).then(r => r.data),
  retrieve: (id) => api.get(`/ordini/${id}/`).then(r => r.data),
  create: (data) => api.post('/ordini/', data).then(r => r.data),
  update: (id, data) => api.patch(`/ordini/${id}/`, data).then(r => r.data),
  delete: (id) => api.delete(`/ordini/${id}/`),
  annulla: (id) => api.post(`/ordini/${id}/annulla/`).then(r => r.data),
  ripristina: (id) => api.post(`/ordini/${id}/ripristina/`).then(r => r.data),
};

// ─── Dashboard Ordini ────────────────────────────────────────────────────

export const dashboardOrdini = {
  filtri:      ()       => api.get('/dashboard-ordini/filtri/').then(r => r.data),
  commerciale: (params) => api.get('/dashboard-ordini/commerciale/', { params }).then(r => r.data),
  clienti:     (params) => api.get('/dashboard-ordini/clienti/',     { params }).then(r => r.data),
  agenti:      (params) => api.get('/dashboard-ordini/agenti/',      { params }).then(r => r.data),
  prodotti:    (params) => api.get('/dashboard-ordini/prodotti/',    { params }).then(r => r.data),
  pagamenti:   (params) => api.get('/dashboard-ordini/pagamenti/',   { params }).then(r => r.data),
};

export default api;
