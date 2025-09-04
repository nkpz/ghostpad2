import { useCallback, useEffect, useState } from "react";
import { ToolFeature } from "@/types";

export function useToolFeatures() {
  const [features, setFeatures] = useState<ToolFeature[]>([]);

  const loadFeatures = useCallback(async () => {
    try {
      const res = await fetch("/api/tools/features");
      if (!res.ok) return;
      const data = await res.json();
      setFeatures(data.features || []);
    } catch (e) {
      console.error("Failed to load tool features", e);
    }
  }, []);

  // Reload features when tools are toggled
  useEffect(() => {
    loadFeatures();
    const handler = () => loadFeatures();
    window.addEventListener("toolsUpdated", handler);
    return () => window.removeEventListener("toolsUpdated", handler);
  }, [loadFeatures]);

  return {
    state: {
      features,
    },
    actions: {
      loadFeatures,
    },
  };
}
