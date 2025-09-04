import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { useWebSocketContext } from "@/context/WebSocketContext";
import { DataSource } from "@/types";

interface ListDisplayProps {
  id: string;
  data_source: DataSource;
  props?: {
    height?: string;
    show_clear?: boolean;
    show_delete_per_item?: boolean;
    placeholder?: string;
  };
  onAction?: (action: any) => Promise<void>;
}

export function ListDisplay({
  data_source,
  props,
  onAction,
}: Readonly<ListDisplayProps>) {
  const [items, setItems] = useState<string[]>([]);
  const [totalCount, setTotalCount] = useState(0);
  const [loading, setLoading] = useState(true);
  const { isConnected, subscribe } = useWebSocketContext();

  const loadItems = async () => {
    if (data_source.type !== "kv_store" || !data_source.key) return;

    try {
      const fetchWindow = data_source.fetch_window || 50;
      const [lenRes, listRes] = await Promise.all([
        fetch(`/api/kv/list/len?key=${encodeURIComponent(data_source.key)}`),
        fetch(
          `/api/kv/list?key=${encodeURIComponent(
            data_source.key
          )}&start=${-fetchWindow}&end=-1`
        ),
      ]);

      const lenData = await lenRes.json();
      const listData = await listRes.json();

      setItems(listData.items || []);
      setTotalCount(lenData.len || 0);
    } catch (error) {
      console.error("Failed to load list items:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, [data_source.key]);

  // Subscribe to KV updates via WebSocket
  useEffect(() => {
    if (data_source.type !== "kv_store" || !data_source.key) return;

    const unsubscribe = subscribe([data_source.key], (message) => {
      if (message.type === "kv_update" && message.key === data_source.key) {
        const newItems = Array.isArray(message.value) ? message.value : [];
        const count = message.len ?? newItems.length;
        const fetchWindow = data_source.fetch_window || 50;

        setItems(newItems.slice(-fetchWindow));
        setTotalCount(count);
      }
    });

    return unsubscribe;
  }, [data_source.key, subscribe]);

  // Fallback polling if WebSocket not connected
  useEffect(() => {
    if (isConnected || data_source.type !== "kv_store") return;

    const interval = setInterval(loadItems, 5000);
    return () => clearInterval(interval);
  }, [isConnected, data_source.type]);

  const handleClearAll = async () => {
    if (!onAction) return;

    try {
      await fetch("/api/kv/list/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: data_source.key }),
      });
      await loadItems();
    } catch (error) {
      console.error("Failed to clear items:", error);
    }
  };

  const handleDeleteItem = async (index: number) => {
    if (!onAction) return;

    try {
      await fetch("/api/kv/list/remove-item", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key: data_source.key, index }),
      });
      await loadItems();
    } catch (error) {
      console.error("Failed to delete item:", error);
    }
  };

  if (loading) {
    return <div className="text-sm text-muted-foreground">Loading...</div>;
  }

  return (
    <div
      className="max-h-80 overflow-y-auto rounded border p-2 bg-muted/30 text-sm"
      style={{ height: props?.height }}
    >
      <div className="flex items-center justify-between mb-2">
        <div className="text-xs text-muted-foreground">Total: {totalCount}</div>
        {props?.show_clear && (
          <Button variant="outline" size="sm" onClick={handleClearAll}>
            Clear all
          </Button>
        )}
      </div>

      {items.length === 0 ? (
        <div className="text-muted-foreground">
          {props?.placeholder || "No items."}
        </div>
      ) : (
        items.map((item, idx) => (
          <div
            key={idx}
            className="py-0.5 whitespace-pre-wrap break-words flex items-start gap-2 group"
          >
            <div className="flex-1">{item}</div>
            {props?.show_delete_per_item && (
              <Button
                variant="ghost"
                size="sm"
                className="opacity-60 hover:opacity-100"
                onClick={() => handleDeleteItem(idx)}
              >
                Delete
              </Button>
            )}
          </div>
        ))
      )}
    </div>
  );
}
