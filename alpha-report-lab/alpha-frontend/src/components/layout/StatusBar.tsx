"use client";

import { useEffect, useState } from "react";
import { fetchHealth } from "@/lib/api";

export default function StatusBar() {
  const [engineUp, setEngineUp] = useState<boolean | null>(null);

  useEffect(() => {
    let cancelled = false;
    async function poll() {
      try {
        await fetchHealth();
        if (!cancelled) setEngineUp(true);
      } catch {
        if (!cancelled) setEngineUp(false);
      }
    }
    poll();
    const t = setInterval(poll, 10000);
    return () => {
      cancelled = true;
      clearInterval(t);
    };
  }, []);

  const dot = (ok: boolean | null) => (
    <span
      className={
        "inline-block w-2 h-2 rounded-full " +
        (ok === null ? "bg-gray-500" : ok ? "bg-alpha-green" : "bg-alpha-red")
      }
    />
  );

  return (
    <div className="h-8 border-t border-gray-800 px-6 flex items-center text-xs text-gray-500 gap-6 bg-gray-950/60">
      <span className="flex items-center gap-2">
        {dot(true)} Frontend
      </span>
      <span className="flex items-center gap-2">
        {dot(engineUp)} Alpha Engine {engineUp === false ? "(down)" : engineUp ? "(healthy)" : "(checking...)"}
      </span>
    </div>
  );
}
