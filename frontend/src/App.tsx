import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import { Persona } from "@/types";
import { useMessageActions, useScrolling } from "@/hooks";
import { usePromptSuggestion } from "@/hooks/usePromptSuggestion";
import { useChatActions } from "@/hooks/useChatActions";
import {
  ChatStreamingProvider,
  useChatStreaming,
} from "@/context/ChatStreamingContext";
import {
  ConversationProvider,
  useConversationContext,
} from "@/context/ConversationContext";
import {
  SettingsProvider,
  useSettingsContext,
} from "@/context/SettingsContext";
import { Header, MainLayout, MobileOverlay } from "@/components/layout";
import { ChatContainer, MessageList, MessageInput } from "@/components/chat";
import { Settings } from "@/components/settings";
import { ConversationsSidebar, DeleteDialog } from "@/components/conversations";
import { WidgetContainer } from "@/components/widgets";
import { WebSocketProvider } from "@/context/WebSocketContext";
import Route from "./components/router/Route";
import { useRouterContext } from "./components/router/Router";

function AppContent() {
  // Mobile settings sidebar open state
  const [isSettingsSidebarOpen, setIsSettingsSidebarOpen] =
    useState<boolean>(false);
  // Desktop settings sidebar open state (persisted)
  const [isDesktopSettingsSidebarOpen, setIsDesktopSettingsSidebarOpen] =
    useState<boolean>(true);
  const [isConversationsSidebarOpen, setIsConversationsSidebarOpen] =
    useState<boolean>(false);
  const [
    isDesktopConversationsSidebarOpen,
    setIsDesktopConversationsSidebarOpen,
  ] = useState<boolean>(true);
  const [personas, setPersonas] = useState<Persona[]>([]);
  const [newMessage, setNewMessage] = useState<string>("");
  const { push } = useRouterContext();

  // Use contexts instead of direct hooks
  const conversation = useConversationContext();
  const settings = useSettingsContext();
  const chat = useChatActions();
  const streaming = useChatStreaming();

  // Prompt suggestion hook
  const promptSuggestion = usePromptSuggestion({
    onSuggestionUpdate: setNewMessage,
    onError: (error) => alert(`Suggestion error: ${error}`),
  });

  // Load personas from backend
  useEffect(() => {
    const fetchPersonas = async () => {
      try {
        const res = await fetch("/api/personas");
        if (!res.ok) return;
        const data = await res.json();
        const mapped: Persona[] = (data.personas || []).map((p: any) => ({
          id: String(p.id),
          name: p.name || "Persona",
          description: p.description || "",
          avatar: p.name ? p.name.charAt(0).toUpperCase() : "P",
          isActive: false,
          color: "bg-gray-500",
        }));
        setPersonas(mapped);
      } catch (err) {
        console.error("Failed to load personas:", err);
      }
    };

    fetchPersonas();

    const onUpdated = () => fetchPersonas();
    window.addEventListener("personasUpdated", onUpdated as EventListener);
    return () =>
      window.removeEventListener("personasUpdated", onUpdated as EventListener);
  }, []);

  // Listen for conversations updates (when personas are deleted with conversations)
  useEffect(() => {
    const onConversationsUpdated = () => {
      conversation.loadConversations();
    };

    window.addEventListener("conversationsUpdated", onConversationsUpdated);
    return () =>
      window.removeEventListener(
        "conversationsUpdated",
        onConversationsUpdated
      );
  }, []); // Empty deps - listener setup once, always calls latest function

  const messageActionsService = useMessageActions({
    currentConversation: conversation.currentConversation,
    messages: chat.messages, // Use chat messages (includes streaming)
    setMessages: conversation.setMessages,
    onConversationUpdate: conversation.setCurrentConversation,
    onConversationsUpdate: conversation.setConversations,
    generateConversationTitle: conversation.generateConversationTitle,
  });

  const scrollingService = useScrolling({
    messages: chat.messages, // Use chat messages (includes streaming)
    isLoading: chat.isLoading,
  });

  const handleSendMessage = useCallback(
    (messageContent?: string) => {
      const content = messageContent || newMessage;

      setNewMessage("");
      return chat.createHandleSendMessage(content)();
    },
    [newMessage, chat.createHandleSendMessage]
  );

  const handleStopGeneration = useCallback(() => {
    streaming.stopGeneration();
  }, [streaming.stopGeneration, conversation.setMessages]);

  const handleSuggestPrompt = useCallback(() => {
    if (
      streaming.isLoading ||
      streaming.isStreaming ||
      promptSuggestion.isGenerating
    )
      return;
    promptSuggestion.generateSuggestion(conversation.currentConversation?.id);
  }, [
    streaming.isLoading,
    streaming.isStreaming,
    promptSuggestion,
    conversation.currentConversation?.id,
  ]);

  const isUserTurn = useMemo(() => {
    const nonSystemMessages = chat.messages.filter(
      (msg) => msg.role !== "system"
    );
    const lastNonSystemMessage =
      nonSystemMessages[nonSystemMessages.length - 1];
    return lastNonSystemMessage?.role === "user";
  }, [chat.messages]);

  useEffect(() => {
    // Load conversations first, then select
    const loadAndSelectConversations = async () => {
      const conversations = await conversation.loadConversations();

      const path = window.location.pathname;
      const match = path.match(/\/c\/([a-f0-9-]+)/i);
      if (match) {
        const conversationId = match[1];
        conversation.selectConversation(conversationId, conversations);
      }
    };

    loadAndSelectConversations();

    // Load settings sidebar desktop state from localStorage
    const savedSidebarState = localStorage.getItem("settingsSidebarOpen");
    if (savedSidebarState !== null) {
      setIsDesktopSettingsSidebarOpen(JSON.parse(savedSidebarState));
    } else {
      // Default: open on large screens, closed on small screens
      const isLargeScreen = window.innerWidth >= 1280;
      setIsDesktopSettingsSidebarOpen(isLargeScreen);
    }

    // Load conversations sidebar state from localStorage
    const savedConversationsSidebarState = localStorage.getItem(
      "conversationsSidebarOpen"
    );
    if (savedConversationsSidebarState !== null) {
      setIsDesktopConversationsSidebarOpen(
        JSON.parse(savedConversationsSidebarState)
      );
    }
  }, []);

  const toggleSettingsSidebar = useCallback(() => {
    // Toggle desktop or mobile version depending on viewport width
    if (window.innerWidth >= 1280) {
      const newState = !isDesktopSettingsSidebarOpen;
      setIsDesktopSettingsSidebarOpen(newState);
      localStorage.setItem("settingsSidebarOpen", JSON.stringify(newState));
    } else {
      setIsSettingsSidebarOpen(!isSettingsSidebarOpen);
    }
  }, [isDesktopSettingsSidebarOpen, isSettingsSidebarOpen]);

  const toggleConversationsSidebar = useCallback(() => {
    setIsConversationsSidebarOpen(!isConversationsSidebarOpen);
  }, [isConversationsSidebarOpen]);

  const toggleDesktopConversationsSidebar = useCallback(() => {
    const newState = !isDesktopConversationsSidebarOpen;
    setIsDesktopConversationsSidebarOpen(newState);
    localStorage.setItem("conversationsSidebarOpen", JSON.stringify(newState));
  }, [isDesktopConversationsSidebarOpen]);

  const handleSelectConversation = useCallback(
    (id: string) => {
      conversation.selectConversation(id);
      push(`/c/${id}`);
    },
    [conversation.selectConversation, push]
  );

  const handleCreateNewConversation = useCallback(async () => {
    const personaIds = (conversation.activePersonas || []).map((p: any) =>
      Number(p.id)
    );
    const newConversationId = await conversation.createNewConversation(
      personaIds
    );
    if (newConversationId) {
      push(`/c/${newConversationId}`);
    }
  }, [conversation.activePersonas, conversation.createNewConversation, push]);

  return (
    <WebSocketProvider url={`ws://${window.location.host}/ws/kv`}>
      <div className="h-screen flex flex-col gap-2">
        <Header
          isDarkMode={settings.isDarkMode}
          toggleDarkMode={settings.toggleDarkMode}
          activePersonas={conversation.activePersonas}
          currentConversationId={conversation.currentConversation?.id}
          userName="User"
          refreshMessages={conversation.loadMessages}
        />

        <WidgetContainer />

        <MainLayout>
          <ConversationsSidebar
            conversations={conversation.conversations}
            currentConversation={conversation.currentConversation}
            createNewConversation={handleCreateNewConversation}
            selectConversation={handleSelectConversation}
            handleDeleteConversation={conversation.handleDeleteConversation}
            isOpen={isDesktopConversationsSidebarOpen}
            isMobile={false}
          />

          <Route path="/">
            <ChatContainer
              currentConversation={conversation.currentConversation}
              activePersonas={conversation.activePersonas}
              toggleConversationsSidebar={toggleConversationsSidebar}
              toggleDesktopConversationsSidebar={
                toggleDesktopConversationsSidebar
              }
              toggleSettingsSidebar={toggleSettingsSidebar}
            >
              <MessageList
                messages={chat.messages}
                currentConversation={conversation.currentConversation}
                isLoading={chat.isLoading}
                messagesContainerRef={
                  scrollingService.refs.messagesContainerRef
                }
                handleUserScroll={scrollingService.actions.handleUserScroll}
                editingMessageId={messageActionsService.state.editingMessageId}
                editingMessageContent={
                  messageActionsService.state.editingMessageContent
                }
                regeneratingMessageId={
                  messageActionsService.state.regeneratingMessageId
                }
                setEditingMessageContent={
                  messageActionsService.actions.setEditingMessageContent
                }
                startEditingMessage={
                  messageActionsService.actions.startEditingMessage
                }
                cancelEditingMessage={
                  messageActionsService.actions.cancelEditingMessage
                }
                saveEditedMessage={
                  messageActionsService.actions.saveEditedMessage
                }
                regenerateMessage={
                  messageActionsService.actions.regenerateMessage
                }
                deleteMessage={messageActionsService.actions.deleteMessage}
                deleteMessageAndAfter={
                  messageActionsService.actions.deleteMessageAndAfter
                }
              />

              <MessageInput
                newMessage={newMessage}
                isLoading={chat.isLoading}
                isStreaming={streaming.isStreaming}
                isUserTurn={isUserTurn}
                handleSendMessage={handleSendMessage}
                handleStopGeneration={handleStopGeneration}
                handleSuggestPrompt={handleSuggestPrompt}
                isGeneratingSuggestion={promptSuggestion.isGenerating}
              />
            </ChatContainer>
          </Route>

          <Route path="/c/:id">
            <ChatContainer
              currentConversation={conversation.currentConversation}
              activePersonas={conversation.activePersonas}
              toggleConversationsSidebar={toggleConversationsSidebar}
              toggleDesktopConversationsSidebar={
                toggleDesktopConversationsSidebar
              }
              toggleSettingsSidebar={toggleSettingsSidebar}
            >
              <MessageList
                messages={chat.messages}
                currentConversation={conversation.currentConversation}
                isLoading={chat.isLoading}
                messagesContainerRef={
                  scrollingService.refs.messagesContainerRef
                }
                handleUserScroll={scrollingService.actions.handleUserScroll}
                editingMessageId={messageActionsService.state.editingMessageId}
                editingMessageContent={
                  messageActionsService.state.editingMessageContent
                }
                regeneratingMessageId={
                  messageActionsService.state.regeneratingMessageId
                }
                setEditingMessageContent={
                  messageActionsService.actions.setEditingMessageContent
                }
                startEditingMessage={
                  messageActionsService.actions.startEditingMessage
                }
                cancelEditingMessage={
                  messageActionsService.actions.cancelEditingMessage
                }
                saveEditedMessage={
                  messageActionsService.actions.saveEditedMessage
                }
                regenerateMessage={
                  messageActionsService.actions.regenerateMessage
                }
                deleteMessage={messageActionsService.actions.deleteMessage}
                deleteMessageAndAfter={
                  messageActionsService.actions.deleteMessageAndAfter
                }
              />

              <MessageInput
                newMessage={newMessage}
                isLoading={chat.isLoading}
                isStreaming={streaming.isStreaming}
                isUserTurn={isUserTurn}
                handleSendMessage={handleSendMessage}
                handleStopGeneration={handleStopGeneration}
                handleSuggestPrompt={handleSuggestPrompt}
                isGeneratingSuggestion={promptSuggestion.isGenerating}
              />
            </ChatContainer>
          </Route>

          <Settings
            isOpenMobile={isSettingsSidebarOpen}
            isOpenDesktop={isDesktopSettingsSidebarOpen}
            personas={personas}
          />

          <ConversationsSidebar
            conversations={conversation.conversations}
            currentConversation={conversation.currentConversation}
            createNewConversation={handleCreateNewConversation}
            selectConversation={handleSelectConversation}
            handleDeleteConversation={conversation.handleDeleteConversation}
            isOpen={isConversationsSidebarOpen}
            isMobile={true}
            onClose={() => setIsConversationsSidebarOpen(false)}
          />

          <MobileOverlay
            isSettingsSidebarOpen={isSettingsSidebarOpen}
            isConversationsSidebarOpen={isConversationsSidebarOpen}
            toggleSettingsSidebar={toggleSettingsSidebar}
            toggleConversationsSidebar={toggleConversationsSidebar}
          />
        </MainLayout>

        <DeleteDialog
          isOpen={conversation.isDeleteDialogOpen}
          onOpenChange={conversation.setIsDeleteDialogOpen}
          onConfirm={conversation.confirmDeleteConversation}
          onCancel={conversation.cancelDeleteConversation}
        />
      </div>
    </WebSocketProvider>
  );
}

function App() {
  const { push } = useRouterContext();

  return (
    <SettingsProvider>
      <ConversationProvider push={push}>
        <ChatStreamingProvider>
          <AppContent />
        </ChatStreamingProvider>
      </ConversationProvider>
    </SettingsProvider>
  );
}

export default App;
