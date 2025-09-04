import { createContext, useContext, ReactNode, useMemo } from "react";
import { useConversations } from "@/hooks/useConversations";
import { Conversation, ChatMessage } from "@/types";

interface ConversationContextValue {
  // State
  conversations: Conversation[];
  currentConversation: Conversation | null;
  messages: ChatMessage[];
  deleteConversationId: string | null;
  isDeleteDialogOpen: boolean;
  activePersonas: any[];

  // Setters
  setMessages: (
    messages: ChatMessage[] | ((prev: ChatMessage[]) => ChatMessage[])
  ) => void;
  setCurrentConversation: (conversation: Conversation | null) => void;
  setConversations: (
    conversations: Conversation[] | ((prev: Conversation[]) => Conversation[])
  ) => void;
  setIsDeleteDialogOpen: (open: boolean) => void;

  // Actions
  loadConversations: () => Promise<Conversation[]>;
  loadMessages: (conversationId: string) => Promise<void>;
  createNewConversation: (personaIds?: number[]) => Promise<number | null>;
  selectConversation: (
    conversationId: string,
    allConversations?: Conversation[]
  ) => Promise<void>;
  handleDeleteConversation: (conversationId: string) => void;
  confirmDeleteConversation: () => Promise<void>;
  cancelDeleteConversation: () => void;
  generateConversationTitle: (
    conversationId: string,
    userMessage: string,
    assistantMessage: string
  ) => Promise<void>;
  updateConversationMessageCount: (
    conversationId: string,
    increment: number
  ) => void;
}

const ConversationContext = createContext<ConversationContextValue | undefined>(
  undefined
);

export function ConversationProvider({
  children,
  push,
}: Readonly<{ children: ReactNode; push?: (path: string) => void }>) {
  const conversationsService = useConversations(push);

  const value = useMemo(
    () => ({
      // State
      conversations: conversationsService.state.conversations,
      currentConversation: conversationsService.state.currentConversation,
      messages: conversationsService.state.messages,
      deleteConversationId: conversationsService.state.deleteConversationId,
      isDeleteDialogOpen: conversationsService.state.isDeleteDialogOpen,
      activePersonas: conversationsService.state.activePersonas,

      // Setters
      setMessages: conversationsService.setters.setMessages,
      setCurrentConversation:
        conversationsService.setters.setCurrentConversation,
      setConversations: conversationsService.setters.setConversations,
      setIsDeleteDialogOpen: conversationsService.setters.setIsDeleteDialogOpen,

      // Actions
      loadConversations: conversationsService.actions.loadConversations,
      loadMessages: conversationsService.actions.loadMessages,
      createNewConversation: conversationsService.actions.createNewConversation,
      selectConversation: conversationsService.actions.selectConversation,
      handleDeleteConversation:
        conversationsService.actions.handleDeleteConversation,
      confirmDeleteConversation:
        conversationsService.actions.confirmDeleteConversation,
      cancelDeleteConversation:
        conversationsService.actions.cancelDeleteConversation,
      generateConversationTitle:
        conversationsService.actions.generateConversationTitle,
      updateConversationMessageCount:
        conversationsService.actions.updateConversationMessageCount,
    }),
    [
      conversationsService.state.conversations,
      conversationsService.state.currentConversation,
      conversationsService.state.messages,
      conversationsService.state.deleteConversationId,
      conversationsService.state.isDeleteDialogOpen,
      conversationsService.state.activePersonas,
      conversationsService.setters.setMessages,
      conversationsService.setters.setCurrentConversation,
      conversationsService.setters.setConversations,
      conversationsService.setters.setIsDeleteDialogOpen,
      conversationsService.actions.loadConversations,
      conversationsService.actions.loadMessages,
      conversationsService.actions.createNewConversation,
      conversationsService.actions.selectConversation,
      conversationsService.actions.handleDeleteConversation,
      conversationsService.actions.confirmDeleteConversation,
      conversationsService.actions.cancelDeleteConversation,
      conversationsService.actions.generateConversationTitle,
      conversationsService.actions.updateConversationMessageCount,
    ]
  );

  return (
    <ConversationContext.Provider value={value}>
      {children}
    </ConversationContext.Provider>
  );
}

export function useConversationContext() {
  const context = useContext(ConversationContext);
  if (context === undefined) {
    throw new Error(
      "useConversationContext must be used within a ConversationProvider"
    );
  }
  return context;
}
