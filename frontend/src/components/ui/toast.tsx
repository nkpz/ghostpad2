import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from "react";

type ToastItem = {
  id: number;
  message: string;
  durationMs?: number;
};

type ToastContextValue = {
  show: (message: string, durationMs?: number) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

export function useToast() {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return ctx;
}

export function ToastProvider({
  children,
}: Readonly<{ children: React.ReactNode }>) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);
  const idRef = useRef<number>(1);

  const remove = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const show = useCallback(
    (message: string, durationMs: number = 5000) => {
      const id = idRef.current++;
      setToasts((prev) => [...prev, { id, message, durationMs }]);
      window.setTimeout(() => remove(id), durationMs);
    },
    [remove]
  );

  const value = useMemo(() => ({ show }), [show]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div className="fixed right-4 bottom-4 z-50 flex flex-col gap-2 max-w-sm pointer-events-none">
        {toasts.map((t) => (
          <div
            key={t.id}
            className="pointer-events-auto rounded-md border bg-background text-foreground shadow-md p-3 text-sm animate-in fade-in-0 zoom-in-95"
          >
            <div className="flex items-start gap-3">
              <div className="flex-1 whitespace-pre-wrap break-words">
                {t.message}
              </div>
              <button
                className="text-muted-foreground hover:text-foreground"
                onClick={() => remove(t.id)}
                aria-label="Dismiss toast"
              >
                ×
              </button>
            </div>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}
