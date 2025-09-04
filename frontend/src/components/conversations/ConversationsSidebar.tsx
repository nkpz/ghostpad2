import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ConversationList } from "./ConversationList";
import { Conversation } from "@/types";
import { memo } from "react";

interface ConversationsSidebarProps {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  createNewConversation: (personaIds?: number[]) => void;
  selectConversation: (conversationId: string) => void;
  handleDeleteConversation: (conversationId: string) => void;
  isOpen: boolean;
  isMobile?: boolean;
  onClose?: () => void;
}

const getContainerClass = (isMobile: boolean, isOpen: boolean) => {
  if (isMobile) {
    return "fixed left-0 top-0 h-full w-80 z-10 xl:hidden";
  }
  const opacityClass = isOpen ? "w-80 opacity-100" : "w-0 opacity-0";
  return `hidden xl:block transition-all duration-300 ease-in-out overflow-hidden ${opacityClass}`;
};

export const ConversationsSidebar = memo(function ConversationsSidebar({
  conversations,
  currentConversation,
  createNewConversation,
  selectConversation,
  handleDeleteConversation,
  isOpen,
  isMobile = false,
  onClose,
}: ConversationsSidebarProps) {
  if (isMobile && !isOpen) return null;

  const containerClasses = getContainerClass(isMobile, isOpen);

  const cardClasses = isMobile
    ? "h-full flex flex-col w-80 shadow-lg"
    : "w-80 flex flex-col h-full";

  return (
    <div className={containerClasses}>
      <Card className={cardClasses}>
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Conversations</CardTitle>
            <Button onClick={() => createNewConversation?.()} size="sm">
              New Chat
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-2 min-h-0">
          <ConversationList
            conversations={conversations}
            currentConversation={currentConversation}
            selectConversation={selectConversation}
            handleDeleteConversation={handleDeleteConversation}
            onClose={isMobile ? onClose : undefined}
          />
        </CardContent>
      </Card>
    </div>
  );
});
