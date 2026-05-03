"use client";

import * as React from "react";
import { Moon, Sun } from "lucide-react";
import { useTheme } from "next-themes";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = React.useState(false);

  // Evitar problemas de hidratación en SSR
  React.useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted) {
    return (
      <button className="flex items-center gap-3 px-4 py-2 w-full text-left rounded-md text-sm font-medium text-muted-foreground opacity-50 cursor-default">
        <div className="w-4 h-4 bg-muted-foreground/20 rounded-full" />
        <span>Cargando tema...</span>
      </button>
    );
  }

  const isDark = theme === "dark";

  return (
    <button
      onClick={() => setTheme(isDark ? "light" : "dark")}
      className="flex items-center gap-3 px-4 py-2 w-full text-left rounded-md text-sm font-medium text-muted-foreground hover:bg-muted hover:text-foreground transition-colors group"
      aria-label="Toggle theme"
    >
      <div className="relative w-4 h-4 flex items-center justify-center">
        <Sun className={`absolute h-4 w-4 transition-all duration-300 ${isDark ? 'scale-0 opacity-0 -rotate-90' : 'scale-100 opacity-100 rotate-0'}`} />
        <Moon className={`absolute h-4 w-4 transition-all duration-300 ${isDark ? 'scale-100 opacity-100 rotate-0' : 'scale-0 opacity-0 rotate-90'}`} />
      </div>
      <span>{isDark ? 'Modo Claro' : 'Modo Oscuro'}</span>
    </button>
  );
}
