import { useRef, useEffect, useMemo, useCallback } from "react";
import { ChatMessage } from "@/types";

interface UseScrollingProps {
  messages: ChatMessage[];
  isLoading: boolean;
}

export function useScrolling({ messages }: UseScrollingProps) {
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const wasAtBottomRef = useRef<boolean>(true);

  const isAtBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return false;

    const { scrollHeight, scrollTop, clientHeight } = container;
    return scrollHeight - scrollTop === clientHeight;
  }, []);

  const scrollToBottom = useCallback(() => {
    const container = messagesContainerRef.current;
    if (!container) return;

    container.scrollTo({ top: container.scrollHeight, behavior: "smooth" });
  }, []);

  const handleUserScroll = useCallback(() => {
    // Update the ref to track current bottom state
    wasAtBottomRef.current = isAtBottom();
  }, [isAtBottom]);

  // Auto-scroll when messages change
  useEffect(() => {
    if (messages.length === 0) return;

    const lastMessage = messages[messages.length - 1];

    // When user sends a message, always scroll to bottom
    if (lastMessage.role === "user") {
      wasAtBottomRef.current = true;
      setTimeout(scrollToBottom, 50);
      return;
    }

    // For other messages, only auto-scroll if we were at bottom before this message
    if (wasAtBottomRef.current) {
      setTimeout(scrollToBottom, 50);
    }
  }, [messages, scrollToBottom]);

  return useMemo(
    () => ({
      refs: {
        messagesContainerRef,
      },
      actions: {
        handleUserScroll,
        scrollToBottom,
      },
    }),
    [messagesContainerRef, handleUserScroll, scrollToBottom]
  );
}
