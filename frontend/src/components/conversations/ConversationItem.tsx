import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { MoreVertical, Trash2 } from "lucide-react";
import { Conversation } from "@/types";
import { memo, useCallback } from "react";

interface ConversationItemProps {
  conversation: Conversation;
  currentConversation: Conversation | null;
  selectConversation: (conversationId: string) => void;
  handleDeleteConversation: (conversationId: string) => void;
  onClose?: () => void;
}

export const ConversationItem = memo(function ConversationItem({
  conversation,
  currentConversation,
  selectConversation,
  handleDeleteConversation,
  onClose,
}: ConversationItemProps) {
  const handleClick = useCallback(() => {
    selectConversation(conversation.id);
    onClose?.();
  }, [selectConversation, conversation.id, onClose]);

  const handleDelete = useCallback(() => {
    handleDeleteConversation(conversation.id);
  }, [handleDeleteConversation, conversation.id]);

  return (
    <div
      className={`group relative p-3 rounded-lg hover:bg-muted transition-colors ${
        currentConversation?.id === conversation.id ? "bg-muted" : ""
      }`}
    >
      <div onClick={handleClick} className="cursor-pointer pr-8">
        <div className="font-medium text-sm truncate">
          {conversation.title}
        </div>
        <div className="text-xs text-muted-foreground">
          {conversation.message_count} messages
        </div>
      </div>

      <div className="absolute top-3 right-3 opacity-0 group-hover:opacity-100 transition-opacity">
        <Popover>
          <PopoverTrigger
            className="inline-flex items-center justify-center h-6 w-6 rounded-md hover:bg-muted-foreground/20 transition-colors"
            onClick={(e) => e.stopPropagation()}
          >
            <MoreVertical className="h-4 w-4" />
          </PopoverTrigger>
          <PopoverContent className="w-48 p-1" align="end">
            <Button
              variant="ghost"
              size="sm"
              className="w-full justify-start text-destructive hover:text-destructive hover:bg-destructive/10"
              onClick={handleDelete}
            >
              <Trash2 className="h-4 w-4 mr-2" />
              Delete conversation
            </Button>
          </PopoverContent>
        </Popover>
      </div>
    </div>
  );
});