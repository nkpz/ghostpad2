import React, {
  createContext,
  useContext,
  useEffect,
  useRef,
  useState,
  useCallback,
  useMemo,
} from "react";

// Global WebSocket manager to handle connection across component remounts
class WebSocketManager {
  private static instance: WebSocketManager;
  private ws: WebSocket | null = null;
  private url: string | null = null;
  private isConnecting = false;
  private reconnectAttempts = 0;
  private reconnectTimeout: NodeJS.Timeout | null = null;
  private readonly subscribers = new Map<string, Set<(message: any) => void>>();
  private readonly stateChangeCallbacks = new Set<
    (isConnected: boolean, isConnecting: boolean) => void
  >();
  private readonly maxReconnectAttempts = 5;
  private readonly reconnectInterval = 3000;

  static getInstance(): WebSocketManager {
    if (!WebSocketManager.instance) {
      WebSocketManager.instance = new WebSocketManager();
    }
    return WebSocketManager.instance;
  }

  connect(url: string) {
    if (
      this.url === url &&
      (this.isConnecting || (this.ws && this.ws.readyState === WebSocket.OPEN))
    ) {
      return;
    }

    if (this.ws && this.ws.readyState !== WebSocket.CLOSED) {
      this.ws.close();
    }

    this.url = url;
    this.isConnecting = true;
    this.notifyStateChange();

    try {
      this.ws = new WebSocket(url);

      this.ws.onopen = () => {
        this.isConnecting = false;
        this.reconnectAttempts = 0;
        this.notifyStateChange();

        // Subscribe to ALL KV changes
        this.ws!.send(
          JSON.stringify({
            type: "subscribe",
            topics: [],
          })
        );
      };

      this.ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);

          // Broadcast to all relevant subscribers
          if (message.type === "kv_update" && message.key) {
            const specificSubscribers = this.subscribers.get(message.key);
            if (specificSubscribers) {
              specificSubscribers.forEach((callback) => callback(message));
            }

            const wildcardSubscribers = this.subscribers.get("*");
            if (wildcardSubscribers) {
              wildcardSubscribers.forEach((callback) => callback(message));
            }
          } else {
            // Broadcast other message types to all subscribers
            this.subscribers.forEach((subscribers) => {
              subscribers.forEach((callback) => callback(message));
            });
          }
        } catch (error) {
          console.error("WebSocket Manager: Failed to parse message:", error);
        }
      };

      this.ws.onclose = () => {
        this.isConnecting = false;
        this.notifyStateChange();

        if (this.reconnectAttempts < this.maxReconnectAttempts) {
          this.reconnectAttempts++;

          this.reconnectTimeout = setTimeout(() => {
            this.connect(this.url!);
          }, this.reconnectInterval);
        } else {
          console.error("WebSocket Manager: Max reconnection attempts reached");
        }
      };

      this.ws.onerror = (error) => {
        console.error("WebSocket Manager: Error:", error);
        this.isConnecting = false;
        this.notifyStateChange();
      };
    } catch (error) {
      console.error("WebSocket Manager: Failed to create WebSocket:", error);
      this.isConnecting = false;
      this.notifyStateChange();
    }
  }

  disconnect() {
    if (this.reconnectTimeout) {
      clearTimeout(this.reconnectTimeout);
      this.reconnectTimeout = null;
    }

    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }

    this.isConnecting = false;
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
    this.notifyStateChange();
  }

  subscribe(topics: string[], onMessage: (message: any) => void) {
    const localTopics = topics.length === 0 ? ["*"] : topics;

    localTopics.forEach((topic) => {
      if (!this.subscribers.has(topic)) {
        this.subscribers.set(topic, new Set());
      }
      this.subscribers.get(topic)!.add(onMessage);
    });

    return () => {
      localTopics.forEach((topic) => {
        const subscribers = this.subscribers.get(topic);
        if (subscribers) {
          subscribers.delete(onMessage);
          if (subscribers.size === 0) {
            this.subscribers.delete(topic);
          }
        }
      });
    };
  }

  sendMessage(message: any) {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(message));
    } else {
      console.warn(
        "WebSocket Manager: Not connected, message not sent:",
        message
      );
    }
  }

  onStateChange(
    callback: (isConnected: boolean, isConnecting: boolean) => void
  ) {
    this.stateChangeCallbacks.add(callback);
    // Immediately notify of current state
    callback(this.isConnected(), this.isConnecting);

    return () => {
      this.stateChangeCallbacks.delete(callback);
    };
  }

  private isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN || false;
  }

  private notifyStateChange() {
    const isConnected = this.isConnected();
    this.stateChangeCallbacks.forEach((callback) => {
      callback(isConnected, this.isConnecting);
    });
  }
}

interface WebSocketMessage {
  type: string;
  [key: string]: any;
}

interface WebSocketContextType {
  isConnected: boolean;
  isConnecting: boolean;
  subscribe: (
    topics: string[],
    onMessage: (message: WebSocketMessage) => void
  ) => () => void;
  sendMessage: (message: WebSocketMessage) => void;
}

const WebSocketContext = createContext<WebSocketContextType | null>(null);

interface WebSocketProviderProps {
  children: React.ReactNode;
  url: string;
}

// Global manager instance - created once outside of React
const globalManager = WebSocketManager.getInstance();

export function WebSocketProvider({
  children,
  url,
}: Readonly<WebSocketProviderProps>) {
  const [isConnected, setIsConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const hasInitialized = useRef(false);

  // Subscribe to state changes from the manager
  useEffect(() => {
    if (hasInitialized.current) return;
    hasInitialized.current = true;

    const unsubscribe = globalManager.onStateChange((connected, connecting) => {
      setIsConnected((prev) => (prev !== connected ? connected : prev));
      setIsConnecting((prev) => (prev !== connecting ? connecting : prev));
    });

    // Connect to the URL
    globalManager.connect(url);

    return unsubscribe;
  }, [url]);

  const subscribe = useCallback(
    (topics: string[], onMessage: (message: WebSocketMessage) => void) => {
      return globalManager.subscribe(topics, onMessage);
    },
    []
  );

  const sendMessage = useCallback((message: WebSocketMessage) => {
    globalManager.sendMessage(message);
  }, []);

  const contextValue = useMemo(
    () => ({
      isConnected,
      isConnecting,
      subscribe,
      sendMessage,
    }),
    [isConnected, isConnecting, subscribe, sendMessage]
  );

  return (
    <WebSocketContext.Provider value={contextValue}>
      {children}
    </WebSocketContext.Provider>
  );
}

export function useWebSocketContext() {
  const context = useContext(WebSocketContext);
  if (!context) {
    throw new Error(
      "useWebSocketContext must be used within a WebSocketProvider"
    );
  }
  return context;
}
