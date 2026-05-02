import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { Toaster } from 'react-hot-toast';
import {
  LayoutDashboard, Wine, Warehouse, Package, Settings, GlassWater,
  ChevronLeft, ChevronRight
} from 'lucide-react';
import { ConfirmProvider } from './components/ConfirmDialog';
import Dashboard from './pages/Dashboard';
import TipologieVino from './pages/TipologieVino';
import Magazzino from './pages/Magazzino';
import Imbottigliamento from './pages/Imbottigliamento';
import Configurazione from './pages/Configurazione';

const navItems = [
  { to: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
  { to: '/tipologie', icon: Wine, label: 'Tipologie Vino' },
  { to: '/magazzino', icon: Warehouse, label: 'Magazzino' },
  { to: '/imbottigliamento', icon: Package, label: 'Imbottigliamento' },
  { to: '/configurazione', icon: Settings, label: 'Configurazione' },
];

function Sidebar({ collapsed, setCollapsed }) {
  return (
    <aside className={`fixed left-0 top-0 h-full bg-bark-950 text-bark-100 z-30 
      transition-all duration-300 flex flex-col ${collapsed ? 'w-[72px]' : 'w-64'}`}>
      
      {/* Logo */}
      <div className="flex items-center gap-3 px-5 h-16 border-b border-bark-800/50">
        <GlassWater className="w-7 h-7 text-wine-400 shrink-0" />
        {!collapsed && (
          <span className="font-display text-lg font-bold text-white tracking-tight">
            VinoManager
          </span>
        )}
      </div>

      {/* Nav */}
      <nav className="flex-1 py-4 space-y-1 px-3">
        {navItems.map(({ to, icon: Icon, label }) => (
          <NavLink
            key={to}
            to={to}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all duration-200
               ${isActive
                 ? 'bg-wine-700/30 text-wine-300 font-semibold'
                 : 'text-bark-400 hover:bg-bark-800/60 hover:text-bark-200'
               } ${collapsed ? 'justify-center' : ''}`
            }
            title={label}
          >
            <Icon className="w-5 h-5 shrink-0" />
            {!collapsed && <span className="text-sm">{label}</span>}
          </NavLink>
        ))}
      </nav>

      {/* Collapse toggle */}
      <button
        onClick={() => setCollapsed(!collapsed)}
        className="flex items-center justify-center h-12 border-t border-bark-800/50
                   text-bark-500 hover:text-bark-300 transition-colors"
      >
        {collapsed ? <ChevronRight className="w-5 h-5" /> : <ChevronLeft className="w-5 h-5" />}
      </button>
    </aside>
  );
}

export default function App() {
  const [collapsed, setCollapsed] = React.useState(false);

  return (
    <BrowserRouter>
      <ConfirmProvider>
        <Toaster
          position="top-right"
          toastOptions={{
            duration: 3000,
            style: {
              fontFamily: '"Source Sans 3", sans-serif',
              borderRadius: '10px',
              background: '#2f2019',
              color: '#faf8f5',
            },
          }}
        />
        <div className="flex min-h-screen bg-[#faf8f5]">
          <Sidebar collapsed={collapsed} setCollapsed={setCollapsed} />
          <main className={`flex-1 transition-all duration-300 ${collapsed ? 'ml-[72px]' : 'ml-64'}`}>
            <div className="p-8 max-w-7xl mx-auto">
              <Routes>
                <Route path="/" element={<Navigate to="/dashboard" replace />} />
                <Route path="/dashboard" element={<Dashboard />} />
                <Route path="/tipologie" element={<TipologieVino />} />
                <Route path="/magazzino" element={<Magazzino />} />
                <Route path="/imbottigliamento" element={<Imbottigliamento />} />
                <Route path="/configurazione" element={<Configurazione />} />
              </Routes>
            </div>
          </main>
        </div>
      </ConfirmProvider>
    </BrowserRouter>
  );
}
