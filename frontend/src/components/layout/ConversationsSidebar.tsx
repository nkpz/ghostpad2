import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { MoreVertical, Trash2 } from "lucide-react";
import { Conversation } from "@/types";

interface ConversationsSidebarProps {
  conversations: Conversation[];
  currentConversation: Conversation | null;
  createNewConversation: (personaIds?: number[]) => void;
  selectConversation: (conversation: Conversation) => void;
  handleDeleteConversation: (conversationId: string) => void;
  isOpen: boolean;
}

export function ConversationsSidebar({
  conversations,
  currentConversation,
  createNewConversation,
  selectConversation,
  handleDeleteConversation,
  isOpen,
}: Readonly<ConversationsSidebarProps>) {
  return (
    <div
      className={`hidden xl:block transition-all duration-300 ease-in-out overflow-hidden ${
        isOpen ? "w-80 opacity-100" : "w-0 opacity-0"
      }`}
    >
      <Card className="w-80 flex flex-col h-full">
        <CardHeader className="flex-shrink-0">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Conversations</CardTitle>
            <Button onClick={() => createNewConversation?.()} size="sm">
              New Chat
            </Button>
          </div>
        </CardHeader>
        <CardContent className="flex-1 overflow-y-auto p-2 min-h-0">
          <div className="space-y-2">
            {conversations.map((conv) => (
              <div
                key={conv.id}
                className={`group relative p-3 rounded-lg hover:bg-muted transition-colors ${
                  currentConversation?.id === conv.id ? "bg-muted" : ""
                }`}
              >
                <div
                  onClick={() => selectConversation(conv)}
                  className="cursor-pointer pr-8"
                >
                  <div className="font-medium text-sm truncate">
                    {conv.title}
                  </div>
                  <div className="text-xs text-muted-foreground">
                    {conv.message_count} messages
                  </div>
                </div>

                {/* Triple-dot menu */}
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
                        onClick={() => handleDeleteConversation(conv.id)}
                      >
                        <Trash2 className="h-4 w-4 mr-2" />
                        Delete conversation
                      </Button>
                    </PopoverContent>
                  </Popover>
                </div>
              </div>
            ))}
            {conversations.length === 0 && (
              <div className="text-center text-muted-foreground py-8">
                No conversations yet.
                <br />
                Start a new chat!
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}