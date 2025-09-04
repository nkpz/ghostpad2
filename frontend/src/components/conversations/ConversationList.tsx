import { ConversationItem } from "./ConversationItem";
import { Conversation } from "@/types";
import { memo } from "react";

interface ConversationListProps {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  selectConversation: (conversationId: string) => void;
  handleDeleteConversation: (conversationId: string) => void;
  onClose?: () => void;
}

export const ConversationList = memo(function ConversationList({
  conversations,
  currentConversation,
  selectConversation,
  handleDeleteConversation,
  onClose,
}: ConversationListProps) {
  return (
    <div className="space-y-2">
      {conversations.map((conversation) => (
        <ConversationItem
          key={conversation.id}
          conversation={conversation}
          currentConversation={currentConversation}
          selectConversation={selectConversation}
          handleDeleteConversation={handleDeleteConversation}
          onClose={onClose}
        />
      ))}
      {conversations.length === 0 && (
        <div className="text-center text-muted-foreground py-8">
          No conversations yet.
          <br />
          Start a new chat!
        </div>
      )}
    </div>
  );
});