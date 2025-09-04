import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Menu, Settings as SettingsIcon } from "lucide-react";
import { Conversation } from "@/types";
import { ReactNode } from "react";

interface ChatContainerProps {
  currentConversation: Conversation | null;
  activePersonas: any[];
  toggleConversationsSidebar: () => void;
  toggleDesktopConversationsSidebar: () => void;
  toggleSettingsSidebar: () => void;
  children: ReactNode;
}

export function ChatContainer({
  currentConversation,
  activePersonas,
  toggleConversationsSidebar,
  toggleDesktopConversationsSidebar,
  toggleSettingsSidebar,
  children,
}: Readonly<ChatContainerProps>) {
  // Format assistant names for display
  const formatAssistantNames = () => {
    if (
      !currentConversation ||
      !activePersonas ||
      activePersonas.length === 0
    ) {
      return null;
    }

    if (activePersonas.length === 1) {
      return `with ${activePersonas[0].name}`;
    }

    const additionalCount = activePersonas.length - 1;
    return `with ${activePersonas[0].name} +${additionalCount}`;
  };

  const assistantText = formatAssistantNames();

  return (
    <Card className="flex-1 flex flex-col min-h-0">
      {/* Chat Header */}
      <CardHeader className="flex-shrink-0">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleConversationsSidebar}
              className="flex items-center gap-2 xl:hidden"
            >
              <Menu className="h-4 w-4" />
              <span className="hidden sm:inline">Conversations</span>
            </Button>
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleDesktopConversationsSidebar}
              className="hidden xl:flex items-center gap-2"
            >
              <Menu className="h-4 w-4" />
              <span>Conversations</span>
            </Button>
          </div>

          <div className="absolute left-1/2 transform -translate-x-1/2 text-center max-w-[25%]">
            <CardTitle className="truncate">
              {currentConversation?.title || "Select a conversation"}
            </CardTitle>
            {assistantText && (
              <div className="text-sm text-muted-foreground italic mt-1">
                {assistantText}
              </div>
            )}
          </div>

          <div className="flex items-center gap-2">
            <Button
              variant="ghost"
              size="sm"
              onClick={toggleSettingsSidebar}
              className="flex items-center gap-2"
            >
              <SettingsIcon className="h-4 w-4" />
              <span className="hidden sm:inline">Settings</span>
            </Button>
          </div>
        </div>
      </CardHeader>

      {children}
    </Card>
  );
}
