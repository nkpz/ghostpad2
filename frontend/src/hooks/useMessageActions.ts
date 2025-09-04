import { useState, useMemo, useCallback } from "react";
import { ChatMessage, Conversation } from "@/types";
import { useChatStreaming } from "@/context/ChatStreamingContext";

interface UseMessageActionsProps {
  currentConversation: Conversation | null;
  messages: ChatMessage[];
  setMessages: (
    messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])
  ) => void;
  onConversationUpdate: (conversation: Conversation | null) => void;
  onConversationsUpdate: (
    updater: (conversations: Conversation[]) => Conversation[]
  ) => void;
  generateConversationTitle: (
    conversationId: string,
    userMessage: string,
    assistantMessage: string
  ) => Promise<void>;
}

export function useMessageActions({
  currentConversation,
  messages,
  setMessages,
  onConversationUpdate,
  onConversationsUpdate,
  generateConversationTitle,
}: UseMessageActionsProps) {
  const { handleRegenerateMessage } = useChatStreaming();
  const [editingMessageId, setEditingMessageId] = useState<number | null>(null);
  const [editingMessageContent, setEditingMessageContent] =
    useState<string>("");
  const [regeneratingMessageId, setRegeneratingMessageId] = useState<
    number | null
  >(null);

  const startEditingMessage = useCallback((message: ChatMessage) => {
    setEditingMessageId(message.id as number);
    setEditingMessageContent(message.content);
  }, []);

  const cancelEditingMessage = useCallback(() => {
    setEditingMessageId(null);
    setEditingMessageContent("");
  }, []);

  const saveEditedMessage = useCallback(async () => {
    if (!editingMessageId) return;

    try {
      const response = await fetch(`/api/messages/${editingMessageId}`, {
        method: "PUT",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          content: editingMessageContent,
        }),
      });

      if (!response.ok) {
        throw new Error(`Failed to update message: ${response.status}`);
      }

      const updatedMessage = await response.json();

      setMessages((prev) =>
        prev.map((msg) =>
          msg.id === editingMessageId
            ? { ...msg, content: updatedMessage.content }
            : msg
        )
      );

      setEditingMessageId(null);
      setEditingMessageContent("");
    } catch (error) {
      console.error("Failed to save message edit:", error);
      alert("Failed to save message. Please try again.");
    }
  }, [editingMessageId, editingMessageContent, setMessages]);

  const regenerateMessage = useCallback(
    async (messageToRegenerate: ChatMessage) => {
      if (!currentConversation) return;

      setRegeneratingMessageId(messageToRegenerate.id as number);

      try {
        const messageIndex = messages.findIndex(
          (msg) => msg.id === messageToRegenerate.id
        );

        // Find the most recent user message before this assistant message (skip system messages)
        let userMessage = null;
        for (let i = messageIndex - 1; i >= 0; i--) {
          if (messages[i].role === "user") {
            userMessage = messages[i];
            break;
          }
        }

        if (!userMessage) {
          throw new Error(
            "Cannot find the user message that prompted this response"
          );
        }

        await handleRegenerateMessage(
          userMessage.content,
          messageToRegenerate,
          currentConversation,
          messages,
          setMessages,
          onConversationUpdate,
          onConversationsUpdate,
          generateConversationTitle
        );
      } catch (error) {
        console.error("Failed to regenerate message:", error);
        alert("Failed to regenerate message. Please try again.");
      } finally {
        setRegeneratingMessageId(null);
      }
    },
    [
      currentConversation,
      messages,
      handleRegenerateMessage,
      setMessages,
      onConversationUpdate,
      onConversationsUpdate,
      generateConversationTitle,
    ]
  );

  const deleteMessage = useCallback(
    async (messageToDelete: ChatMessage) => {
      try {
        const response = await fetch(`/api/messages/${messageToDelete.id}`, {
          method: "DELETE",
        });

        if (!response.ok) {
          throw new Error(`Failed to delete message: ${response.status}`);
        }

        setMessages((prev) =>
          prev.filter((msg) => msg.id !== messageToDelete.id)
        );
      } catch (error) {
        console.error("Failed to delete message:", error);
        alert("Failed to delete message. Please try again.");
      }
    },
    [setMessages]
  );

  const deleteMessageAndAfter = useCallback(
    async (messageToDelete: ChatMessage) => {
      try {
        const messageIndex = messages.findIndex(
          (msg) => msg.id === messageToDelete.id
        );

        if (messageIndex === -1) return;

        // Get all messages to delete (the selected message and all after it)
        const messagesToDelete = messages.slice(messageIndex);
        const messageIdsToDelete = messagesToDelete.map((msg) => msg.id);

        // Delete all messages in parallel
        const deletePromises = messageIdsToDelete.map(async (messageId) => {
          const response = await fetch(`/api/messages/${messageId}`, {
            method: "DELETE",
          });

          if (!response.ok) {
            throw new Error(
              `Failed to delete message ${messageId}: ${response.status}`
            );
          }
        });

        await Promise.all(deletePromises);

        // Update local state to remove the deleted messages
        setMessages((prev) =>
          prev.filter((msg) => !messageIdsToDelete.includes(msg.id))
        );
      } catch (error) {
        console.error(
          "Failed to delete message and subsequent messages:",
          error
        );
        alert("Failed to delete messages. Please try again.");
      }
    },
    [messages, setMessages]
  );

  return useMemo(
    () => ({
      state: {
        editingMessageId,
        editingMessageContent,
        regeneratingMessageId,
      },
      actions: {
        setEditingMessageContent,
        startEditingMessage,
        cancelEditingMessage,
        saveEditedMessage,
        regenerateMessage,
        deleteMessage,
        deleteMessageAndAfter,
      },
    }),
    [
      editingMessageId,
      editingMessageContent,
      regeneratingMessageId,
      setEditingMessageContent,
      startEditingMessage,
      cancelEditingMessage,
      saveEditedMessage,
      regenerateMessage,
      deleteMessage,
      deleteMessageAndAfter,
    ]
  );
}
