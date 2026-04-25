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

// ─── Operazioni ──────────────────────────────────────────────────────────

export const aggiuntaVino = (data) =>
  api.post('/aggiunta-vino/', data).then(r => r.data);

export const caricoMagazzino = (data) =>
  api.post('/carico-magazzino/', data).then(r => r.data);

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

export default api;
