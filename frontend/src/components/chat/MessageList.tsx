import { CardContent } from "@/components/ui/card";
import { ChatMessage, Conversation } from "@/types";
import { MessageItem } from "./MessageItem";

interface MessageListProps {
  messages: ChatMessage[];
  currentConversation: Conversation | null;
  isLoading: boolean;
  messagesContainerRef: React.RefObject<HTMLDivElement>;
  handleUserScroll: (e: React.UIEvent<HTMLDivElement>) => void;
  editingMessageId: number | null;
  editingMessageContent: string;
  regeneratingMessageId: number | null;
  setEditingMessageContent: (content: string) => void;
  startEditingMessage: (message: ChatMessage) => void;
  cancelEditingMessage: () => void;
  saveEditedMessage: () => void;
  regenerateMessage: (message: ChatMessage) => void;
  deleteMessage: (message: ChatMessage) => void;
  deleteMessageAndAfter: (message: ChatMessage) => void;
}

export function MessageList({
  messages,
  currentConversation,
  messagesContainerRef,
  handleUserScroll,
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
}: Readonly<MessageListProps>) {
  return (
    <CardContent className="flex-1 p-0 min-h-0">
      <div
        ref={messagesContainerRef}
        className="h-full overflow-y-auto p-4 space-y-4"
        onScroll={handleUserScroll}
      >
        {messages.length === 0 && !currentConversation && (
          <div className="text-center text-muted-foreground py-8">
            Start a new conversation or select an existing one to begin
            chatting.
          </div>
        )}
        {messages
          .slice()
          .sort((a, b) => {
            const aIsTemp = typeof a.id === 'string' && a.id.startsWith('temp-');
            const bIsTemp = typeof b.id === 'string' && b.id.startsWith('temp-');
            
            if (aIsTemp && bIsTemp) return 0; // Keep temp messages in order they appear
            if (aIsTemp) return 1; // Put temp messages after non-temp
            if (bIsTemp) return -1; // Put non-temp before temp
            
            // For non-temp messages, use sequence_order (defaulting to large number if missing)
            const aOrder = a.sequence_order ?? Number.MAX_SAFE_INTEGER;
            const bOrder = b.sequence_order ?? Number.MAX_SAFE_INTEGER;
            return aOrder - bOrder;
          })
          .map((message) => (
            <MessageItem
            key={message.id}
            message={message}
            editingMessageId={editingMessageId}
            editingMessageContent={editingMessageContent}
            regeneratingMessageId={regeneratingMessageId}
            setEditingMessageContent={setEditingMessageContent}
            startEditingMessage={startEditingMessage}
            cancelEditingMessage={cancelEditingMessage}
            saveEditedMessage={saveEditedMessage}
            regenerateMessage={regenerateMessage}
            deleteMessage={deleteMessage}
            deleteMessageAndAfter={deleteMessageAndAfter}
          />
        ))}
      </div>
    </CardContent>
  );
}