import { useEffect, useState, useRef } from "react";
import { useWebSocketContext } from "@/context/WebSocketContext";

interface HtmlRendererProps {
  id: string;
  data_source: {
    type: string;
    key?: string;
    value?: string;
  };
  props?: Record<string, any>;
}

export function HtmlRenderer({
  id,
  data_source,
  props,
}: Readonly<HtmlRendererProps>) {
  const [htmlContent, setHtmlContent] = useState<string>("");
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isConnected, subscribe } = useWebSocketContext();
  const previousContentRef = useRef<string>("");

  // Create a ref for the iframe
  const iframeRef = useRef<HTMLIFrameElement>(null);

  // Update iframe content when htmlContent changes (only if using iframe)
  useEffect(() => {
    if (props?.use_iframe && iframeRef.current && htmlContent) {
      const iframe = iframeRef.current;

      // Use srcdoc instead of document.write for better compatibility
      iframe.srcdoc = htmlContent;
    }
  }, [htmlContent, props?.use_iframe]);

  // Load initial content from KV store
  const loadContent = async () => {
    try {
      // Only show loading if we have no existing content
      if (!htmlContent) {
        setIsLoading(true);
      }
      setError(null);

      if (typeof data_source.key == "undefined") {
        throw new Error("Invalid key");
      }

      const response = await fetch(
        `/api/kv/get?key=${encodeURIComponent(data_source.key)}`
      );
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      const newContent = data.value || "";

      // Only update if content has actually changed
      if (newContent !== previousContentRef.current) {
        previousContentRef.current = newContent;
        setHtmlContent(newContent);
      }
    } catch (err) {
      console.error("Failed to load HTML content:", err);
      // Only show error if we have no existing content to fall back to
      if (!htmlContent) {
        setError(err instanceof Error ? err.message : "Failed to load content");
      }
    } finally {
      setIsLoading(false);
    }
  };

  // Initial load
  useEffect(() => {
    if (data_source.type === "kv_store" && data_source.key) {
      loadContent();
    } else if (data_source.type === "value" && data_source.value) {
      setHtmlContent(data_source.value);
      setIsLoading(false);
    }
  }, [data_source.key, data_source.type, data_source.value]);

  // WebSocket subscription for real-time updates
  useEffect(() => {
    if (data_source.type !== "kv_store" || !data_source.key) return;

    const unsubscribe = subscribe([data_source.key], (message) => {
      if (message.type === "kv_update" && message.key === data_source.key) {
        const newContent = message.value || "";

        // Only update if content has actually changed
        if (newContent !== previousContentRef.current) {
          previousContentRef.current = newContent;
          setHtmlContent(newContent);
        }
      }
    });

    return unsubscribe;
  }, [data_source.key, data_source.type, subscribe]);

  // Fallback polling if WebSocket not connected
  useEffect(() => {
    if (isConnected || data_source.type !== "kv_store") return;

    const interval = setInterval(loadContent, 5000); // Poll every 5 seconds
    return () => clearInterval(interval);
  }, [isConnected, data_source.type]);

  // Always prioritize showing content if we have it
  if (htmlContent) {
    // Use iframe if specified in props, otherwise direct HTML
    if (props?.use_iframe) {
      return (
        <div className="w-full" style={props?.style}>
          <iframe
            ref={iframeRef}
            className="w-full border border-gray-200 rounded bg-white"
            style={{
              minHeight: "400px",
              height: "500px",
              maxHeight: "80vh",
            }}
            title={`html-content-${id}`}
            sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-popups-to-escape-sandbox"
            loading="lazy"
            referrerPolicy="strict-origin-when-cross-origin"
          />
        </div>
      );
    } else {
      // Direct HTML rendering
      return (
        <div
          className="ui-html-component"
          style={props?.style}
          dangerouslySetInnerHTML={{ __html: htmlContent }}
        />
      );
    }
  }

  // Only show loading/error states when we have no content to display
  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="text-sm text-muted-foreground">Loading content...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center p-4">
        <div className="text-sm text-red-500">Error: {error}</div>
      </div>
    );
  }

  // No content and not loading/error
  return (
    <div className="flex items-center justify-center p-4">
      <div className="text-sm text-muted-foreground">No content available</div>
    </div>
  );
}
