import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Trash2 } from "lucide-react";
import { DataSource } from "@/types";

interface LibraryItem {
  id: number;
  name: string;
  content: string;
  created_at: string;
  updated_at: string;
}

interface LibraryLoaderProps {
  id: string;
  data_source: DataSource;
  props?: {
    height?: string;
    placeholder?: string;
  };
  onAction?: (action: any) => Promise<void>;
}

function renderLibraryContent(
  loading: boolean,
  items: LibraryItem[],
  props: LibraryLoaderProps["props"],
  handleLoad: (item: LibraryItem) => Promise<void>,
  handleDelete: (item: LibraryItem) => Promise<void>
) {
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        Loading library items...
      </div>
    );
  }

  if (items.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-muted-foreground">
        {props?.placeholder || "No library items found"}
      </div>
    );
  }

  return (
    <div className="p-2 space-y-2">
      {items.map((item) => (
        <div
          key={item.id}
          className="flex items-center justify-between p-2 bg-background rounded border"
        >
          <div className="flex-1 min-w-0">
            <div className="font-medium truncate">{item.name}</div>
            <div className="text-xs text-muted-foreground truncate">
              {item.content.substring(0, 100)}
              {item.content.length > 100 ? "..." : ""}
            </div>
          </div>
          <div className="flex items-center gap-2 ml-2">
            <Button size="sm" variant="ghost" onClick={() => handleLoad(item)}>
              Load
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => handleDelete(item)}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
          </div>
        </div>
      ))}
    </div>
  );
}

export function LibraryLoader({
  data_source,
  props,
  onAction,
}: Readonly<LibraryLoaderProps>) {
  const [items, setItems] = useState<LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);

  const loadItems = async () => {
    if (data_source.type !== "library" || !data_source.library_type) return;

    try {
      setLoading(true);
      const response = await fetch(
        `/api/library?type=${encodeURIComponent(data_source.library_type)}`
      );
      const data = await response.json();
      setItems(data.snippets || []);
    } catch (error) {
      console.error("Failed to load library items:", error);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadItems();
  }, [data_source.library_type]);

  const handleLoad = async (item: LibraryItem) => {
    if (onAction) {
      await onAction({
        type: "library_load",
        item_id: item.id,
        content: item.content,
        name: item.name,
        target_component_id: data_source.target_component_id,
      });
    }
  };

  const handleDelete = async (item: LibraryItem) => {
    try {
      const response = await fetch(`/api/library/${item.id}`, {
        method: "DELETE",
      });

      if (response.ok) {
        await loadItems();
      }
    } catch (error) {
      console.error("Failed to delete library item:", error);
    }
  };

  const containerHeight = props?.height || "300px";

  return (
    <div
      className="border rounded-md overflow-auto bg-muted/30"
      style={{ height: containerHeight }}
    >
      {renderLibraryContent(loading, items, props, handleLoad, handleDelete)}
    </div>
  );
}
