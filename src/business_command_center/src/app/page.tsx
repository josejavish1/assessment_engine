import React from 'react';

export default function Home() {
  return (
    <div className="flex h-screen bg-gray-100">
      {/* Sidebar */}
      <aside className="w-64 bg-slate-900 text-white flex flex-col">
        <div className="h-16 flex items-center justify-center border-b border-slate-800">
          <h1 className="text-xl font-bold tracking-tight">Assessment Platform</h1>
        </div>
        <nav className="flex-1 px-4 py-6 space-y-2">
          <a href="#" className="block px-4 py-2 rounded bg-slate-800 text-sm font-medium">Dashboard</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Assessments</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Blueprints</a>
          <a href="#" className="block px-4 py-2 rounded text-slate-300 hover:bg-slate-800 hover:text-white text-sm font-medium">Settings</a>
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 flex flex-col overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center px-8 justify-between shadow-sm">
          <h2 className="text-2xl font-semibold text-gray-800">Assessment Engine Command Center</h2>
          
          {/* Status Indicator */}
          <div className="flex items-center space-x-2">
            <span className="relative flex h-3 w-3">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-amber-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-3 w-3 bg-amber-500"></span>
            </span>
            <span className="text-sm font-medium text-amber-700">Conectando al servidor MCP...</span>
          </div>
        </header>

        {/* Workspace */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 h-full flex flex-col items-center justify-center text-center">
            <svg className="w-16 h-16 text-gray-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 002-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10"></path>
            </svg>
            <h3 className="text-lg font-medium text-gray-900 mb-2">Workspace Inactivo</h3>
            <p className="text-gray-500 max-w-md">
              El entorno visual está preparado. Esperando la conexión con el protocolo MCP para renderizar los datos del Assessment Engine.
            </p>
          </div>
        </div>
      </main>
    </div>
  );
}
