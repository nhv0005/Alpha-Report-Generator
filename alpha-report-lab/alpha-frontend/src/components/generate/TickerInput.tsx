"use client";

import { useState } from "react";

const POPULAR = ["AAPL", "MSFT", "NVDA", "GOOGL", "AMZN", "META", "TSLA", "JPM", "V", "JNJ"];

export default function TickerInput({
  value,
  onChange,
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  const [focused, setFocused] = useState(false);
  const filtered = POPULAR.filter((t) =>
    value ? t.startsWith(value.toUpperCase()) : true
  ).slice(0, 6);

  return (
    <div className="relative">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value.toUpperCase().slice(0, 5).replace(/[^A-Z]/g, ""))}
        onFocus={() => setFocused(true)}
        onBlur={() => setTimeout(() => setFocused(false), 150)}
        placeholder="e.g. NVDA"
        className="w-full px-4 py-2 bg-gray-900 border border-gray-700 rounded-lg font-mono uppercase text-lg focus:outline-none focus:ring-2 focus:ring-alpha-blue/40"
      />
      {focused && filtered.length > 0 && (
        <div className="absolute z-10 top-full left-0 right-0 mt-1 bg-gray-900 border border-gray-700 rounded-lg shadow-lg max-h-48 overflow-y-auto">
          {filtered.map((t) => (
            <button
              key={t}
              type="button"
              onMouseDown={() => onChange(t)}
              className="block w-full text-left px-3 py-2 font-mono hover:bg-gray-800"
            >
              {t}
            </button>
          ))}
        </div>
      )}
    </div>
  );
}
