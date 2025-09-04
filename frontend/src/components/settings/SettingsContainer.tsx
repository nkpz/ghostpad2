import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { MessageSquare, User, Wrench } from "lucide-react";
import { ChatSettings } from "./ChatSettings";
import { PersonaSettings } from "./PersonaSettings";
import { SystemPromptSettings, SamplingSettings, Persona, SystemPromptItem } from "@/types";
import { ToolsSettings } from "./ToolsSettings";

interface SettingsContainerProps {
  systemPromptSettings: SystemPromptSettings;
  samplingSettings: SamplingSettings;
  personas: Persona[];
  userDescription?: string;
  handleUserDescriptionChange?: (value: string) => void;
  userName?: string;
  handleUserNameChange?: (value: string) => void;
  currentConversation?: any;
  activePersonas?: Persona[];
  addPersonaToConversation?: (conversationId: string, personaId: string) => void;
  removePersonaFromConversation?: (conversationId: string, personaId: string) => void;
  handleSystemPromptChange: (field: keyof SystemPromptSettings, value: string | boolean | SystemPromptItem[]) => void;
  handleSamplingChange: (field: keyof SamplingSettings, value: number) => void;
  addSystemPromptItem: () => void;
  updateSystemPromptItem: (index: number, updates: Partial<SystemPromptItem>) => void;
  deleteSystemPromptItem: (index: number) => void;
  idPrefix?: string;
}

export function SettingsContainer({
  systemPromptSettings,
  samplingSettings,
  personas,
  currentConversation,
  activePersonas,
  addPersonaToConversation,
  removePersonaFromConversation,
  handleSystemPromptChange,
  handleSamplingChange,
  addSystemPromptItem,
  updateSystemPromptItem,
  deleteSystemPromptItem,
  userDescription,
  handleUserDescriptionChange,
  userName,
  handleUserNameChange,
  idPrefix = "",
}: Readonly<SettingsContainerProps>) {
  return (
    <Tabs defaultValue="chat" className="h-full flex flex-col">
      <TabsList className="grid w-full grid-cols-3 mb-4">
        <TabsTrigger value="chat" className="flex flex-col items-center gap-1 py-2">
          <MessageSquare className="h-4 w-4" />
          <span className="text-xs">Chat</span>
        </TabsTrigger>
        <TabsTrigger value="persona" className="flex flex-col items-center gap-1 py-2">
          <User className="h-4 w-4" />
          <span className="text-xs">Persona</span>
        </TabsTrigger>
        <TabsTrigger value="tools" className="flex flex-col items-center gap-1 py-2">
          <Wrench className="h-4 w-4" />
          <span className="text-xs">Tools</span>
        </TabsTrigger>
      </TabsList>


      <TabsContent value="chat" className="flex-1 overflow-y-auto space-y-4">
        <ChatSettings
          systemPromptSettings={systemPromptSettings}
          samplingSettings={samplingSettings}
          handleSystemPromptChange={handleSystemPromptChange}
          handleSamplingChange={handleSamplingChange}
          userDescription={userDescription}
          handleUserDescriptionChange={handleUserDescriptionChange}
          userName={userName}
          handleUserNameChange={handleUserNameChange}
          addSystemPromptItem={addSystemPromptItem}
          updateSystemPromptItem={updateSystemPromptItem}
          deleteSystemPromptItem={deleteSystemPromptItem}
          idPrefix={idPrefix}
        />
      </TabsContent>

      <TabsContent value="persona" className="flex-1 overflow-y-auto space-y-4 px-4">
        <PersonaSettings
          personas={personas}
          currentConversation={currentConversation}
          activePersonas={activePersonas}
          addPersonaToConversation={addPersonaToConversation}
          removePersonaFromConversation={removePersonaFromConversation}
        />
      </TabsContent>

      <TabsContent value="tools" className="flex-1 overflow-y-auto space-y-4 px-4">
        <ToolsSettings />
      </TabsContent>
    </Tabs>
  );
}
