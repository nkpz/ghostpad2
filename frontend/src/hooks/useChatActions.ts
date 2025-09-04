import { useCallback, useMemo } from "react";
import { useChatStreaming } from "@/context/ChatStreamingContext";
import { useConversationContext } from "@/context/ConversationContext";

export function useChatActions() {
  const streaming = useChatStreaming();
  const conversation = useConversationContext();

  const createHandleSendMessage = useCallback(
    (messageContent: string) => async () => {
      if (streaming.isLoading) return;

      streaming.setIsLoading(true);

      await streaming.handleStreamingMessage(
        messageContent,
        conversation.currentConversation,
        conversation.messages,
        conversation.setMessages,
        conversation.setCurrentConversation,
        conversation.setConversations,
        conversation.generateConversationTitle
      );
    },
    [streaming, conversation]
  );

  // Get the messages to display - either streaming local messages or global messages
  const displayMessages = useMemo(() => {
    return streaming.isStreaming
      ? streaming.localStreamingMessages
      : conversation.messages;
  }, [
    streaming.isStreaming,
    streaming.localStreamingMessages,
    conversation.messages,
  ]);

  return useMemo(
    () => ({
      isLoading: streaming.isLoading,
      isStreaming: streaming.isStreaming,
      messages: displayMessages,
      createHandleSendMessage,
    }),
    [
      streaming.isLoading,
      streaming.isStreaming,
      displayMessages,
      createHandleSendMessage,
    ]
  );
}
