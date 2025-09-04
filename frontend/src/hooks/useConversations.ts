import { useState, useCallback, useMemo } from "react";
import { Conversation, ChatMessage } from "@/types";

export function useConversations(push?: (path: string) => void) {
  const [conversations, setConversations] = useState<Conversation[]>([]);
  const [currentConversation, setCurrentConversation] =
    useState<Conversation | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [activePersonas, setActivePersonas] = useState<any[]>([]);
  const [deleteConversationId, setDeleteConversationId] = useState<
    string | null
  >(null);
  const [isDeleteDialogOpen, setIsDeleteDialogOpen] = useState<boolean>(false);

  const loadConversations = useCallback(async () => {
    try {
      const response = await fetch("/api/conversations");
      const data = await response.json();
      setConversations(data.conversations);
      return data.conversations;
    } catch (err) {
      console.error("Failed to load conversations:", err);
      return [];
    }
  }, []);

  const loadMessages = useCallback(async (conversationId: string) => {
    try {
      const response = await fetch(
        `/api/conversations/${conversationId}/messages`
      );
      const data = await response.json();
      // Sort messages by sequence_order to ensure proper display order
      const sortedMessages = (data.messages || []).sort(
        (a: ChatMessage, b: ChatMessage) =>
          (a.sequence_order || 0) - (b.sequence_order || 0)
      );
      setMessages(sortedMessages);
      // Map personas from API to frontend Persona-like shape
      if (data.personas) {
        const mapped = (data.personas || []).map((p: any) => ({
          id: String(p.id),
          name: p.name,
          description: p.description || "",
          avatar: p.name ? p.name.charAt(0).toUpperCase() : "P",
          isActive: true,
          color: "bg-gray-500",
          avatar_url: p.avatar_url || null,
        }));
        setActivePersonas(mapped);
      } else {
        setActivePersonas([]);
      }
    } catch (err) {
      console.error("Failed to load messages:", err);
    }
  }, []);

  const createNewConversation = useCallback(
    async (personaIds?: number[]) => {
      try {
        const body: any = { title: "New Chat" };
        if (personaIds?.length) {
          body.persona_ids = personaIds;
        }

        const response = await fetch("/api/conversations", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(body),
        });
        const newConv = await response.json();
        // Add the new conversation to the list and load its messages (and attached personas)
        setConversations((prev) => [newConv, ...prev]);
        setCurrentConversation(newConv);
        // Load messages for the newly created conversation to ensure personas are fresh
        await loadMessages(newConv.id);
        return newConv.id;
      } catch (err) {
        console.error("Failed to create conversation:", err);
        return null;
      }
    },
    [loadMessages]
  );

  const selectConversation = useCallback(
    async (
      conversationId: string,
      allConversations: Conversation[] = conversations
    ) => {
      const conversation = allConversations.find(
        (c) => c.id === conversationId
      );

      if (!conversation) {
        // If conversation not found, redirect to root - never fetch and add to list
        if (push) push("/");
        else window.location.href = "/";
        return;
      }

      setCurrentConversation(conversation);
      await loadMessages(conversation.id);
    },
    [conversations, push, loadMessages]
  );

  const handleDeleteConversation = useCallback((conversationId: string) => {
    setDeleteConversationId(conversationId);
    setIsDeleteDialogOpen(true);
  }, []);

  const confirmDeleteConversation = useCallback(async () => {
    if (!deleteConversationId) return;

    try {
      const response = await fetch(
        `/api/conversations/${deleteConversationId}`,
        {
          method: "DELETE",
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      setConversations((prev) =>
        prev.filter((conv) => conv.id !== deleteConversationId)
      );

      if (currentConversation?.id === deleteConversationId) {
        setCurrentConversation(null);
        setMessages([]);
        // Redirect to root when viewing a deleted conversation (prefer client-side push)
        if (push) push("/");
        else window.location.href = "/";
      }

      setIsDeleteDialogOpen(false);
      setDeleteConversationId(null);
    } catch (err) {
      console.error("Failed to delete conversation:", err);
      alert("Failed to delete conversation. Please try again.");
    }
  }, [deleteConversationId, currentConversation, push]);

  const cancelDeleteConversation = useCallback(() => {
    setIsDeleteDialogOpen(false);
    setDeleteConversationId(null);
  }, []);

  const generateConversationTitle = useCallback(
    async (
      conversationId: string,
      userMessage: string,
      assistantMessage: string
    ) => {
      try {
        const response = await fetch("/api/chat/generate-title", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
            user_message: userMessage,
            assistant_message: assistantMessage,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();

        if (currentConversation && currentConversation.id === conversationId) {
          setCurrentConversation((prev) =>
            prev ? { ...prev, title: data.title } : null
          );
        }

        setConversations((prev) =>
          prev.map((conv) =>
            conv.id === conversationId ? { ...conv, title: data.title } : conv
          )
        );
      } catch (err) {
        console.error("❌ Failed to generate conversation title:", err);
      }
    },
    [currentConversation]
  );

  const updateConversationMessageCount = useCallback(
    (conversationId: string, increment: number) => {
      setConversations((prev) =>
        prev.map((conv) =>
          conv.id === conversationId
            ? { ...conv, message_count: conv.message_count + increment }
            : conv
        )
      );
    },
    []
  );

  return useMemo(
    () => ({
      state: {
        conversations,
        currentConversation,
        messages,
        deleteConversationId,
        isDeleteDialogOpen,
        activePersonas,
      },
      setters: {
        setMessages,
        setCurrentConversation,
        setConversations,
        setIsDeleteDialogOpen,
      },
      actions: {
        loadConversations,
        loadMessages,
        createNewConversation,
        selectConversation,
        handleDeleteConversation,
        confirmDeleteConversation,
        cancelDeleteConversation,
        generateConversationTitle,
        updateConversationMessageCount,
      },
    }),
    [
      conversations,
      currentConversation,
      messages,
      deleteConversationId,
      isDeleteDialogOpen,
      activePersonas,
      setMessages,
      setCurrentConversation,
      setConversations,
      setIsDeleteDialogOpen,
      loadConversations,
      loadMessages,
      createNewConversation,
      selectConversation,
      handleDeleteConversation,
      confirmDeleteConversation,
      cancelDeleteConversation,
      generateConversationTitle,
      updateConversationMessageCount,
    ]
  );
}
