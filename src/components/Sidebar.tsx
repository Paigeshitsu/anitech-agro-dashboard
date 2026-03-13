import React, { useState } from 'react';
import { Menu, X, LayoutDashboard, BarChart3, Package, Calendar } from 'lucide-react';
import { AGRO_THEME } from '../utils/formatters';

const Sidebar = () => {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      {/* Mobile toggle */}
      <button
        className="md:hidden fixed top-4 left-4 z-50 p-2 bg-[var(--agro-accent-dark)] text-white rounded-lg shadow-lg hover:bg-[var(--agro-primary-dark)] transition-all"
        onClick={() => setIsOpen(true)}
      >
        <Menu className="h-6 w-6" />
      </button>

      {/* Overlay */}
      {isOpen && (
        <div 
          className="md:hidden fixed inset-0 bg-black bg-opacity-50 z-40"
          onClick={() => setIsOpen(false)}
        />
      )}

      {/* Drawer / Fixed Sidebar */}
      <aside className={`agro-sidebar ${
        isOpen ? 'translate-x-0' : '-translate-x-full'
      } md:translate-x-0 fixed md:static md:inset-y-0 left-0 z-50 w-64 shadow-2xl transform transition-transform duration-300 ease-in-out overflow-y-auto h-screen`}>
        <div className="flex items-center justify-between p-6 border-b border-white/20 bg-[var(--agro-primary)]/90 backdrop-blur-sm">
          <h1 className="text-2xl font-bold bg-gradient-to-r from-white to-gray-200 bg-clip-text text-transparent">
            Anitech Agro
          </h1>
          <button
            className="p-2 rounded-xl hover:bg-white/20 transition-all md:hidden"
            onClick={() => setIsOpen(false)}
          >
            <X className="h-6 w-6" />
          </button>
        </div>
        <nav className="mt-2 px-3 py-2">
          <a href="/dashboard" className="flex items-center p-4 rounded-xl mx-1 hover:bg-white/20 text-white/90 hover:text-white font-medium transition-all group">
            <LayoutDashboard className="h-5 w-5 mr-4 group-hover:scale-110" />
            Dashboard
          </a>
          <a href="/market" className="flex items-center p-4 mt-2 rounded-xl mx-1 hover:bg-white/20 text-white/90 hover:text-white transition-all group">
            <BarChart3 className="h-5 w-5 mr-4 group-hover:scale-110" />
            Market Prices
          </a>
          <a href="/crops" className="flex items-center p-4 mt-2 rounded-xl mx-1 hover:bg-white/20 text-white/90 hover:text-white transition-all group">
            <Package className="h-5 w-5 mr-4 group-hover:scale-110" />
            Crops
          </a>
          <a href="/schedule" className="flex items-center p-4 mt-2 rounded-xl mx-1 hover:bg-white/20 text-white/90 hover:text-white transition-all group">
            <Calendar className="h-5 w-5 mr-4 group-hover:scale-110" />
            Schedule
          </a>
        </nav>
      </aside>
    </>
  );
};

export default Sidebar;

