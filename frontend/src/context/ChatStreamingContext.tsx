import React, {
  createContext,
  useContext,
  useRef,
  useState,
  ReactNode,
  useMemo,
  useCallback,
} from "react";
import { ChatMessage, Conversation } from "@/types";
import { useSettingsContext } from "./SettingsContext";
import { useConversationContext } from "./ConversationContext";
import { replacePlaceholders } from "@/utils/placeholders";

interface ChatStreamingState {
  isLoading: boolean;
  isStreaming: boolean;
  localStreamingMessages: ChatMessage[];
  streamingMessageRef: React.MutableRefObject<ChatMessage | null>;
}

interface ChatStreamingActions {
  setIsLoading: (loading: boolean) => void;
  setIsStreaming: (streaming: boolean) => void;
  setLocalStreamingMessages: React.Dispatch<
    React.SetStateAction<ChatMessage[]>
  >;
  stopGeneration: () => void;
  handleStreamingMessage: (
    messageContent: string,
    currentConversation: Conversation | null,
    messages: ChatMessage[],
    onMessagesUpdate: (messages: ChatMessage[]) => void,
    onConversationUpdate: (conversation: Conversation | null) => void,
    onConversationsUpdate: (
      updater: (conversations: Conversation[]) => Conversation[]
    ) => void,
    generateConversationTitle: (
      conversationId: string,
      userMessage: string,
      assistantMessage: string
    ) => void
  ) => Promise<void>;
  handleRegenerateMessage: (
    userMessageContent: string,
    messageToRegenerate: ChatMessage,
    currentConversation: Conversation | null,
    messages: ChatMessage[],
    onMessagesUpdate: (messages: ChatMessage[]) => void,
    onConversationUpdate: (conversation: Conversation | null) => void,
    onConversationsUpdate: (
      updater: (conversations: Conversation[]) => Conversation[]
    ) => void,
    generateConversationTitle: (
      conversationId: string,
      userMessage: string,
      assistantMessage: string
    ) => void
  ) => Promise<void>;
}

interface ChatStreamingContextValue
  extends ChatStreamingState,
    ChatStreamingActions {}

const ChatStreamingContext = createContext<
  ChatStreamingContextValue | undefined
>(undefined);

export function ChatStreamingProvider({
  children,
}: Readonly<{ children: ReactNode }>) {
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [isStreaming, setIsStreaming] = useState<boolean>(false);
  const [localStreamingMessages, setLocalStreamingMessages] = useState<
    ChatMessage[]
  >([]);
  const streamingMessageRef = useRef<ChatMessage | null>(null);
  const finalMessagesRef = useRef<ChatMessage[] | null>(null);
  const abortControllerRef = useRef<AbortController | null>(null);
  const conversationUpdatesRef = useRef<{
    newConversation?: Conversation;
    updateMessageCount?: { id: string; increment: number };
    generateTitle?: {
      conversationId: string;
      userMessage: string;
      assistantMessage: string;
    };
  } | null>(null);

  // Get contexts for placeholder replacement
  const { userName } = useSettingsContext();
  const { activePersonas } = useConversationContext();

  // Helper function to get character name for placeholder replacement
  const getCharName = useCallback(() => {
    return activePersonas && activePersonas.length > 0
      ? activePersonas[0].name
      : "Assistant";
  }, [activePersonas]);

  const stopGeneration = useCallback(
    (onMessagesUpdate?: (messages: ChatMessage[]) => void) => {
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null;
      }

      // Preserve user messages that were added during streaming
      if (onMessagesUpdate && localStreamingMessages.length > 0) {
        // Filter out any incomplete assistant messages (temp ids) but keep user messages
        const preservedMessages = localStreamingMessages.filter(
          (msg) => msg.role === "user" || !msg.id.toString().startsWith("temp-")
        );
        onMessagesUpdate(preservedMessages);
      }

      setIsLoading(false);
      setIsStreaming(false);
      setLocalStreamingMessages([]);
      streamingMessageRef.current = null;
    },
    [localStreamingMessages]
  );

  const handleStreamingMessage = async (
    messageContent: string,
    currentConversation: Conversation | null,
    messages: ChatMessage[],
    onMessagesUpdate: (messages: ChatMessage[]) => void,
    onConversationUpdate: (conversation: Conversation | null) => void,
    onConversationsUpdate: (
      updater: (conversations: Conversation[]) => Conversation[]
    ) => void,
    generateConversationTitle: (
      conversationId: string,
      userMessage: string,
      assistantMessage: string
    ) => void,
    apiEndpoint: string = "/api/chat/stream",
    requestBody?: object
  ) => {
    let streamingMessage: ChatMessage | null = null;
    let streamingSystemMessage: ChatMessage | null = null;
    const originalUserMessage = messageContent;
    const existingMessageCountBefore = messages.length;

    // Create new AbortController for this request
    abortControllerRef.current = new AbortController();

    // Initialize local streaming state
    setIsStreaming(true);
    setLocalStreamingMessages([...messages]); // Start with current messages

    try {
      const response = await fetch(apiEndpoint, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(
          requestBody ?? {
            content: messageContent,
            conversation_id: currentConversation?.id,
          }
        ),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) throw new Error("No response body");

      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split("\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            try {
              const data = JSON.parse(line.slice(6));

              if (data.type === "user_message") {
                setLocalStreamingMessages((prev) => [...prev, data.message]);
              } else if (data.type === "stream_start") {
                // Don't create streaming message yet - wait for first stream_chunk
              } else if (data.type === "stream_chunk") {
                if (!streamingMessage) {
                  // Create new streaming message (could be initial or continuation after system message)
                  streamingMessage = {
                    id: `temp-${Date.now()}`, // Use temp prefix to distinguish
                    role: "assistant",
                    content: data.content,
                    created_at: new Date().toISOString(),
                    conversation_id: currentConversation?.id || "",
                  };
                  streamingMessageRef.current = streamingMessage;
                  setLocalStreamingMessages((prev) => [
                    ...prev,
                    streamingMessage!,
                  ]);
                } else {
                  streamingMessage.content += data.content;
                  streamingMessageRef.current = streamingMessage;
                  setLocalStreamingMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === streamingMessage!.id
                        ? { ...streamingMessage! }
                        : msg
                    )
                  );
                }
              } else if (data.type === "assistant_complete") {
                // Assistant message was flushed - replace temp message with real one and position correctly
                if (streamingMessage && data.message) {
                  const tempId = streamingMessage.id;
                  setLocalStreamingMessages((prev) => {
                    // Remove the temp message and insert the real one at correct position
                    const withoutTemp = prev.filter((msg) => msg.id !== tempId);

                    // Find correct insertion point based on sequence_order
                    let insertIndex = withoutTemp.length;
                    for (let i = 0; i < withoutTemp.length; i++) {
                      if (
                        typeof withoutTemp[i]?.sequence_order !== "undefined" &&
                        typeof data?.message?.sequence_order !== "undefined" &&
                        (withoutTemp[i]?.sequence_order ?? 0) >
                          (data?.message?.sequence_order ?? 0)
                      ) {
                        insertIndex = i;
                        break;
                      }
                    }
                    if (data?.message) {
                      withoutTemp.splice(insertIndex, 0, data.message);
                    }
                    return withoutTemp;
                  });
                  streamingMessage = null; // Clear reference since this message is now complete
                  streamingMessageRef.current = null;
                }
              } else if (data.type === "system_message_start") {
                // System message streaming started - no action needed yet
              } else if (data.type === "system_chunk") {
                // Accumulate system chunks into a single streaming system message
                if (!streamingSystemMessage) {
                  const processedContent = replacePlaceholders(
                    data.content,
                    userName,
                    getCharName()
                  );
                  streamingSystemMessage = {
                    id: `temp-system-${Date.now()}`, // Use temp prefix
                    role: "system",
                    content: processedContent,
                    created_at: new Date().toISOString(),
                    conversation_id: currentConversation?.id || "",
                  };
                  setLocalStreamingMessages((prev) => [
                    ...prev,
                    streamingSystemMessage!,
                  ]);
                } else {
                  // Update existing streaming system message content with placeholder replacement
                  streamingSystemMessage.content += data.content;
                  const processedContent = replacePlaceholders(
                    streamingSystemMessage.content,
                    userName,
                    getCharName()
                  );
                  const updatedMessage: ChatMessage = {
                    ...streamingSystemMessage,
                    content: processedContent,
                  };
                  streamingSystemMessage = updatedMessage;
                  setLocalStreamingMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === updatedMessage.id ? updatedMessage : msg
                    )
                  );
                }
              } else if (data.type === "system_complete") {
                // Replace the temporary streaming system message with the persisted one
                if (data?.message?.id && streamingSystemMessage) {
                  const tempId = streamingSystemMessage.id;
                  setLocalStreamingMessages((prev) =>
                    prev.map((msg) => (msg.id === tempId ? data.message : msg))
                  );
                  streamingSystemMessage = null;
                } else if (data?.message?.id) {
                  setLocalStreamingMessages((prev) => [...prev, data.message]);
                }
              } else if (
                data.type === "complete" ||
                data.type === "message_complete"
              ) {
                if (streamingMessage && data?.message) {
                  // Replace the temporary assistant message with the real one from server
                  const tempId = streamingMessage.id;
                  streamingMessage = data.message;
                  streamingMessageRef.current = streamingMessage;

                  setLocalStreamingMessages((prev) =>
                    prev.map((msg) => (msg.id === tempId ? data.message : msg))
                  );
                } else if (streamingMessage) {
                  streamingMessage.content =
                    data?.content || streamingMessage.content;
                  streamingMessageRef.current = streamingMessage;
                  setLocalStreamingMessages((prev) =>
                    prev.map((msg) =>
                      msg.id === streamingMessage?.id
                        ? { ...streamingMessage }
                        : msg
                    )
                  );
                }

                setLocalStreamingMessages((currentLocal) => {
                  const finalMessages = currentLocal;

                  finalMessagesRef.current = finalMessages;
                  return finalMessages;
                });

                const conversationId =
                  streamingMessage?.conversation_id ||
                  currentConversation?.id ||
                  "";
                const isNewConversation = !currentConversation;
                const isFirstExchange =
                  isNewConversation || existingMessageCountBefore === 0;

                if (isNewConversation) {
                  const newConv: Conversation = {
                    id: conversationId,
                    title: "New Chat",
                    created_at: new Date().toISOString(),
                    message_count: 2,
                  };
                  conversationUpdatesRef.current = {
                    newConversation: newConv,
                  };
                } else {
                  conversationUpdatesRef.current = {
                    updateMessageCount: {
                      id: currentConversation.id,
                      increment: 2,
                    },
                  };
                }

                if (isFirstExchange) {
                  if (conversationUpdatesRef.current) {
                    conversationUpdatesRef.current.generateTitle = {
                      conversationId,
                      userMessage: originalUserMessage,
                      assistantMessage:
                        data?.message?.content ||
                        streamingMessage?.content ||
                        "",
                    };
                  }
                }
              } else if (data.error) {
                throw new Error(data.error);
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === "AbortError") {
        console.info("Request was aborted by user");
      } else {
        console.error("Failed to send streaming message:", err);
        alert("Failed to send message. Please check your OpenAI settings.");
      }
    } finally {
      abortControllerRef.current = null;
      // Commit final messages to global state only once at the end
      if (finalMessagesRef.current) {
        onMessagesUpdate(finalMessagesRef.current);
        finalMessagesRef.current = null;
      }

      // Apply conversation updates only once at the end
      if (conversationUpdatesRef.current) {
        const updates = conversationUpdatesRef.current;

        if (updates.newConversation) {
          onConversationUpdate(updates.newConversation);
          onConversationsUpdate((prev) => [updates.newConversation!, ...prev]);
        } else if (updates.updateMessageCount) {
          onConversationsUpdate((prev) =>
            prev.map((conv) =>
              conv.id === updates.updateMessageCount!.id
                ? {
                    ...conv,
                    message_count:
                      conv.message_count +
                      updates.updateMessageCount!.increment,
                  }
                : conv
            )
          );
        }

        if (updates.generateTitle) {
          generateConversationTitle(
            updates.generateTitle.conversationId,
            updates.generateTitle.userMessage,
            updates.generateTitle.assistantMessage
          );
        }

        conversationUpdatesRef.current = null;
      }

      setIsLoading(false);
      setIsStreaming(false);
      setLocalStreamingMessages([]);
      streamingMessageRef.current = null;
    }
  };

  const handleRegenerateMessage = async (
    userMessageContent: string,
    messageToRegenerate: ChatMessage,
    currentConversation: Conversation | null,
    messages: ChatMessage[],
    onMessagesUpdate: (messages: ChatMessage[]) => void,
    onConversationUpdate: (conversation: Conversation | null) => void,
    onConversationsUpdate: (
      updater: (conversations: Conversation[]) => Conversation[]
    ) => void,
    generateConversationTitle: (
      conversationId: string,
      userMessage: string,
      assistantMessage: string
    ) => void
  ) => {
    // Clean up messages for regeneration - remove the old assistant message completely
    const messageIndex = messages.findIndex(
      (msg) => msg.id === messageToRegenerate.id
    );
    let userMessageIndex = -1;
    for (let i = messageIndex - 1; i >= 0; i--) {
      if (messages[i].role === "user") {
        userMessageIndex = i;
        break;
      }
    }
    const cleanMessages =
      userMessageIndex >= 0
        ? messages.slice(0, userMessageIndex + 1)
        : messages.slice(0, messageIndex);
    onMessagesUpdate(cleanMessages);

    // Call shared streaming logic with regeneration endpoint and request body
    await handleStreamingMessage(
      userMessageContent,
      currentConversation,
      cleanMessages,
      onMessagesUpdate,
      onConversationUpdate,
      onConversationsUpdate,
      generateConversationTitle,
      "/api/chat/regenerate",
      {
        conversation_id: currentConversation?.id,
        user_prompt: userMessageContent,
        message_id_to_replace: messageToRegenerate.id,
        use_streaming: true,
      }
    );
  };

  const value = useMemo(
    () => ({
      isLoading,
      isStreaming,
      localStreamingMessages,
      streamingMessageRef,
      setIsLoading,
      setIsStreaming,
      setLocalStreamingMessages,
      stopGeneration,
      handleStreamingMessage,
      handleRegenerateMessage,
    }),
    [
      isLoading,
      isStreaming,
      localStreamingMessages,
      streamingMessageRef,
      setIsLoading,
      setIsStreaming,
      setLocalStreamingMessages,
      stopGeneration,
      handleStreamingMessage,
      handleRegenerateMessage,
    ]
  );

  return (
    <ChatStreamingContext.Provider value={value}>
      {children}
    </ChatStreamingContext.Provider>
  );
}

export function useChatStreaming() {
  const context = useContext(ChatStreamingContext);
  if (context === undefined) {
    throw new Error(
      "useChatStreaming must be used within a ChatStreamingProvider"
    );
  }
  return context;
}
