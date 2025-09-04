import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";
import logo from "@/assets/images/logo.svg";
import { useState } from "react";
import { ToolsDropdown } from "@/components/dropdowns/ToolsDropdown";
import { SettingsModal } from "@/components/modals/SettingsModal";

interface HeaderProps {
  isDarkMode: boolean;
  toggleDarkMode: () => void;
  activePersonas?: { id: string; name: string }[];
  currentConversationId?: string | null;
  userName?: string | null;
  refreshMessages: (conversationId: string) => Promise<void>;
}

export function Header({
  isDarkMode,
  toggleDarkMode,
  activePersonas,
  currentConversationId,
  refreshMessages,
}: Readonly<HeaderProps>) {
  const [isSettingsOpen, setIsSettingsOpen] = useState(false);

  return (
    <div className="flex-shrink-0 p-6 pb-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <img src={logo} alt="Ghostpad Logo" className="h-16 w-16" />
          <h1 className="text-xl font-bold">Ghostpad</h1>
        </div>

        <div className="flex items-center gap-1">
          <ToolsDropdown
            activePersonas={activePersonas}
            currentConversationId={currentConversationId}
            refreshMessages={refreshMessages}
          />

          <Button
            variant="ghost"
            size="sm"
            onClick={() => setIsSettingsOpen(true)}
            className="h-16 w-16 p-0 hover:bg-muted"
            title="Settings"
          >
            <Settings className="h-7 w-7 text-muted-foreground" />
          </Button>
        </div>
      </div>

      <SettingsModal
        open={isSettingsOpen}
        onOpenChange={setIsSettingsOpen}
        isDarkMode={isDarkMode}
        toggleDarkMode={toggleDarkMode}
      />
    </div>
  );
}
