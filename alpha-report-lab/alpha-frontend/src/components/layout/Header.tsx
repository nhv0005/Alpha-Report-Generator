"use client";

import { Settings } from "lucide-react";

export default function Header() {
  return (
    <header className="h-14 border-b border-gray-800 flex items-center justify-between px-6 bg-gray-950/40 backdrop-blur">
      <div>
        <div className="text-sm font-medium text-gray-100">Alpha Report Lab</div>
        <div className="text-xs text-gray-500">AI-Powered Investment Research</div>
      </div>
      <button className="p-2 rounded-md text-gray-400 hover:text-gray-100 hover:bg-gray-900">
        <Settings size={16} />
      </button>
    </header>
  );
}
