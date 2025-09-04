import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { SettingsContainer } from "./SettingsContainer";
import { Persona } from "@/types";
import { useSettingsContext } from "@/context/SettingsContext";
import { useConversationContext } from "@/context/ConversationContext";
import { useCallback } from "react";

interface SettingsProps {
  isOpenMobile?: boolean;
  isOpenDesktop?: boolean;
  personas: Persona[];
}

export function Settings({
  isOpenMobile = false,
  isOpenDesktop = false,
  personas,
}: Readonly<SettingsProps>) {
  const settings = useSettingsContext();
  const conversation = useConversationContext();

  const addPersonaToConversation = useCallback(async (conversationId: string, personaId: string) => {
    try {
      await fetch(`/api/conversations/${conversationId}/personas/${personaId}`, { method: 'POST' });
      await conversation.loadMessages(conversationId);
      window.dispatchEvent(new CustomEvent('personasUpdated'));
    } catch (err) {
      console.error('Failed to add persona to conversation', err);
    }
  }, [conversation.loadMessages]);

  const removePersonaFromConversation = useCallback(async (conversationId: string, personaId: string) => {
    try {
      await fetch(`/api/conversations/${conversationId}/personas/${personaId}`, { method: 'DELETE' });
      await conversation.loadMessages(conversationId);
      window.dispatchEvent(new CustomEvent('personasUpdated'));
    } catch (err) {
      console.error('Failed to remove persona from conversation', err);
    }
  }, [conversation.loadMessages]);

  return (
    <>
      {/* Mobile Settings - Fixed overlay on small screens */}
      <div className={`xl:hidden ${isOpenMobile ? 'block' : 'hidden'}`}>
        <div className="fixed right-0 top-0 h-full w-80 z-10">
          <Card className="h-full flex flex-col w-80 shadow-lg">
            <CardHeader className="flex-shrink-0">
              <CardTitle className="text-lg">Settings</CardTitle>
            </CardHeader>
            <CardContent className="flex-1 overflow-y-auto p-2">
              <SettingsContainer
                systemPromptSettings={settings.systemPromptSettings}
                samplingSettings={settings.samplingSettings}
                personas={personas}
                userDescription={settings.userDescription}
                handleUserDescriptionChange={settings.handleUserDescriptionChange}
                userName={settings.userName}
                handleUserNameChange={settings.handleUserNameChange}
                currentConversation={conversation.currentConversation}
                activePersonas={conversation.activePersonas}
                addPersonaToConversation={addPersonaToConversation}
                removePersonaFromConversation={removePersonaFromConversation}
                handleSystemPromptChange={settings.handleSystemPromptChange}
                handleSamplingChange={settings.handleSamplingChange}
                addSystemPromptItem={settings.addSystemPromptItem}
                updateSystemPromptItem={settings.updateSystemPromptItem}
                deleteSystemPromptItem={settings.deleteSystemPromptItem}
                idPrefix="_mobile"
              />
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Desktop Settings - Collapsible sidebar on large screens */}
      <div className={`hidden xl:block transition-all duration-300 ease-in-out overflow-hidden ${
        isOpenDesktop ? "w-80 opacity-100" : "w-0 opacity-0"
      }`}>
        <Card className="h-full flex flex-col w-80">
          <CardHeader className="flex-shrink-0">
            <CardTitle className="text-lg">Settings</CardTitle>
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-2">
            <SettingsContainer
              systemPromptSettings={settings.systemPromptSettings}
              samplingSettings={settings.samplingSettings}
              personas={personas}
              userDescription={settings.userDescription}
              handleUserDescriptionChange={settings.handleUserDescriptionChange}
              userName={settings.userName}
              handleUserNameChange={settings.handleUserNameChange}
              currentConversation={conversation.currentConversation}
              activePersonas={conversation.activePersonas}
              addPersonaToConversation={addPersonaToConversation}
              removePersonaFromConversation={removePersonaFromConversation}
              handleSystemPromptChange={settings.handleSystemPromptChange}
              handleSamplingChange={settings.handleSamplingChange}
              addSystemPromptItem={settings.addSystemPromptItem}
              updateSystemPromptItem={settings.updateSystemPromptItem}
              deleteSystemPromptItem={settings.deleteSystemPromptItem}
              idPrefix="_desktop"
            />
          </CardContent>
        </Card>
      </div>
    </>
  );
}
