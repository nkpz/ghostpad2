import { createContext, useContext, ReactNode, useMemo } from "react";
import { useSettings } from "@/hooks/useSettings";
import {
  SamplingSettings,
  SystemPromptItem,
  SystemPromptSettings,
} from "@/types";

interface SettingsContextValue {
  // State
  isDarkMode: boolean;
  systemPromptSettings: any;
  samplingSettings: any;
  userDescription: string;
  userName: string;

  // Actions
  toggleDarkMode: () => void;
  handleSystemPromptChange: (
    field: keyof SystemPromptSettings,
    value: string | boolean | SystemPromptItem[]
  ) => void;
  handleSamplingChange: (field: keyof SamplingSettings, value: number) => void;
  handleUserDescriptionChange: (description: string) => void;
  handleUserNameChange: (name: string) => void;
  addSystemPromptItem: () => void;
  updateSystemPromptItem: (index: number, updates: any) => void;
  deleteSystemPromptItem: (index: number) => void;
}

const SettingsContext = createContext<SettingsContextValue | undefined>(
  undefined
);

export function SettingsProvider({
  children,
}: Readonly<{ children?: ReactNode }>) {
  const settingsService = useSettings();

  const value = useMemo(
    () => ({
      // State
      isDarkMode: settingsService.state.isDarkMode,
      systemPromptSettings: settingsService.state.systemPromptSettings,
      samplingSettings: settingsService.state.samplingSettings,
      userDescription: settingsService.state.userDescription,
      userName: settingsService.state.userName,

      // Actions
      toggleDarkMode: settingsService.actions.toggleDarkMode,
      handleSystemPromptChange:
        settingsService.actions.handleSystemPromptChange,
      handleSamplingChange: settingsService.actions.handleSamplingChange,
      handleUserDescriptionChange:
        settingsService.actions.handleUserDescriptionChange,
      handleUserNameChange: settingsService.actions.handleUserNameChange,
      addSystemPromptItem: settingsService.actions.addSystemPromptItem,
      updateSystemPromptItem: settingsService.actions.updateSystemPromptItem,
      deleteSystemPromptItem: settingsService.actions.deleteSystemPromptItem,
    }),
    [
      settingsService.state.isDarkMode,
      settingsService.state.systemPromptSettings,
      settingsService.state.samplingSettings,
      settingsService.state.userDescription,
      settingsService.state.userName,
      settingsService.actions.toggleDarkMode,
      settingsService.actions.handleSystemPromptChange,
      settingsService.actions.handleSamplingChange,
      settingsService.actions.handleUserDescriptionChange,
      settingsService.actions.handleUserNameChange,
      settingsService.actions.addSystemPromptItem,
      settingsService.actions.updateSystemPromptItem,
      settingsService.actions.deleteSystemPromptItem,
    ]
  );

  return (
    <SettingsContext.Provider value={value}>
      {children}
    </SettingsContext.Provider>
  );
}

export function useSettingsContext() {
  const context = useContext(SettingsContext);
  if (context === undefined) {
    throw new Error(
      "useSettingsContext must be used within a SettingsProvider"
    );
  }
  return context;
}
