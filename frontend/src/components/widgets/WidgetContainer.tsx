import { useEffect, useState } from "react";
import { WidgetGrid } from "./WidgetGrid";
import { TextWidget } from "./TextWidget";
import { PercentWidget } from "./PercentWidget";
import { useWebSocketContext } from "../../context/WebSocketContext";

interface WidgetConfig {
  id: string;
  type: "text" | "percent";
  label: string;
  kv_key: string;
  max_value_key?: string;
  refresh_interval?: number;
  format_options?: {
    text?: {
      max_length?: number;
      truncate?: boolean;
      prefix?: string;
      suffix?: string;
      color?: string;
    };
    percent?: {
      show_value?: boolean;
      color_scheme?: "default" | "health" | "custom";
    };
  };
}

interface WidgetFeature {
  id: string;
  label: string;
  kv_key: string;
  type: "widget";
  widget_config: WidgetConfig;
  source_tool_id?: string;
}

export function WidgetContainer() {
  const [widgets, setWidgets] = useState<WidgetFeature[]>([]);
  const [widgetValues, setWidgetValues] = useState<Record<string, any>>({});
  const [maxValues, setMaxValues] = useState<Record<string, any>>({});
  const [loading, setLoading] = useState(true);

  // Load widget features from the API
  const loadWidgetFeatures = async () => {
    try {
      const res = await fetch("/api/tools/features");
      if (!res.ok) return;

      const data = await res.json();

      const widgetFeatures =
        data.features?.filter((f: any) => f.type === "widget") || [];

      setWidgets(widgetFeatures);

      // Load initial values for all widgets
      await Promise.all(
        widgetFeatures.map(async (widget: WidgetFeature) => {
          try {
            // Load KV store value
            const valueRes = await fetch(
              `/api/kv/get?key=${encodeURIComponent(widget.kv_key)}`
            );
            if (valueRes.ok) {
              const valueData = await valueRes.json();
              setWidgetValues((prev) => ({
                ...prev,
                [widget.kv_key]: valueData.value,
              }));
            } else {
              console.error(
                `Failed to get value for widget ${widget.id}:`,
                valueRes.status
              );
            }

            // Load max value if specified
            if (widget.widget_config.max_value_key) {
              const maxValueRes = await fetch(
                `/api/kv/get?key=${encodeURIComponent(
                  widget.widget_config.max_value_key
                )}`
              );
              if (maxValueRes.ok) {
                const maxValueData = await maxValueRes.json();
                setMaxValues((prev) => ({
                  ...prev,
                  [widget.widget_config.max_value_key!]: maxValueData.value,
                }));
              } else {
                console.error(
                  `Failed to get max value for widget ${widget.id}:`,
                  maxValueRes.status
                );
              }
            }
          } catch (e) {
            console.error(`Failed to load value for widget ${widget.id}:`, e);
          }
        })
      );
    } catch (e) {
      console.error("Failed to load widget features:", e);
    } finally {
      setLoading(false);
    }
  };

  // Set up WebSocket for real-time updates
  const { subscribe } = useWebSocketContext();

  // Subscribe to ALL KV changes (no specific topics needed)
  useEffect(() => {
    const unsubscribe = subscribe([], (message) => {
      // Empty array = subscribe to all
      if (message.type === "kv_update") {
        // Use the value directly from the WebSocket message
        const value = message.value;

        // Always update both widget values and max values - let React handle the re-renders
        // This is simpler and avoids stale closure issues
        setWidgetValues((prev) => ({
          ...prev,
          [message.key]: value,
        }));

        setMaxValues((prev) => ({
          ...prev,
          [message.key]: value,
        }));
      } else if (message.type === "features_changed") {
        loadWidgetFeatures();
      }
    });

    return () => {
      unsubscribe();
    };
  }, [subscribe]); // Only depend on subscribe function, not widgets

  // Load features when component mounts
  useEffect(() => {
    loadWidgetFeatures();

    // Listen for tool updates
    const handleToolsUpdated = () => loadWidgetFeatures();
    window.addEventListener("toolsUpdated", handleToolsUpdated);

    return () => {
      window.removeEventListener("toolsUpdated", handleToolsUpdated);
    };
  }, []);

  if (loading) {
    return (
      <div className="px-6 py-3">
        <div className="animate-pulse">
          <div className="h-20 bg-muted rounded-md"></div>
        </div>
      </div>
    );
  }

  if (widgets.length === 0) {
    return null; // Don't render anything if no widgets
  }

  const saveWidgetValue = async (key: string, value: any) => {
    try {
      await fetch("/api/kv/set", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ key, value }),
      });

      // update local state immediately for optimistic UI
      setWidgetValues((prev) => ({ ...prev, [key]: value }));
    } catch (e) {
      console.error(`Failed to save widget value for ${key}:`, e);
    }
  };

  const renderWidget = (widget: WidgetFeature) => {
    const value = widgetValues[widget.kv_key];
    const maxValue = widget.widget_config.max_value_key
      ? maxValues[widget.widget_config.max_value_key]
      : undefined;
    const config = widget.widget_config;

    switch (config.type) {
      case "text":
        return (
          <TextWidget
            key={widget.id}
            label={widget.label}
            value={value || ""}
            kv_key={widget.kv_key}
            onValueChange={(v: string) => saveWidgetValue(widget.kv_key, v)}
            formatOptions={{
              maxLength: config.format_options?.text?.max_length,
              truncate: config.format_options?.text?.truncate,
              prefix: config.format_options?.text?.prefix,
              suffix: config.format_options?.text?.suffix,
              color: config.format_options?.text?.color,
            }}
          />
        );

      case "percent":
        return (
          <PercentWidget
            key={widget.id}
            label={widget.label}
            value={value || 0}
            max_value={maxValue}
            kv_key={widget.kv_key}
            onValueChange={(v: number) => saveWidgetValue(widget.kv_key, v)}
            formatOptions={{
              showValue: config.format_options?.percent?.show_value,
              colorScheme: config.format_options?.percent?.color_scheme,
            }}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="px-6 py-3 border-b bg-muted/30">
      <WidgetGrid>{widgets.map(renderWidget)}</WidgetGrid>
    </div>
  );
}
