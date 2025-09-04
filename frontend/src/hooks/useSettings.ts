import { useState, useEffect, useCallback, useRef, useMemo } from "react";
import {
  SystemPromptSettings,
  SamplingSettings,
  SystemPromptItem,
} from "@/types";

export function useSettings() {
  const [systemPromptSettings, setSystemPromptSettings] =
    useState<SystemPromptSettings>({
      system_prompts: [],
      include_datetime: false,
      enabled: true,
      thinking_mode: "default",
    });
  const [userDescription, setUserDescription] = useState<string>("");
  const [userName, setUserName] = useState<string>("User");
  const [samplingSettings, setSamplingSettings] = useState<SamplingSettings>({
    temperature: 1.0,
    top_p: 1.0,
    max_tokens: 1000,
    frequency_penalty: 0.0,
    presence_penalty: 0.0,
  });
  const [isDarkMode, setIsDarkMode] = useState<boolean>(() => {
    const saved = localStorage.getItem("darkMode");
    if (saved !== null) {
      return JSON.parse(saved);
    }
    return window.matchMedia("(prefers-color-scheme: dark)").matches;
  });

  const systemPromptSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const loadSystemPromptSettings = useCallback(async () => {
    try {
      const response = await fetch("/api/settings/system-prompt");
      const data = await response.json();
      setSystemPromptSettings(data);
    } catch (err) {
      console.error("Failed to load system prompt settings:", err);
    }
  }, []);

  const loadUserDescription = useCallback(async () => {
    try {
      const response = await fetch("/api/settings/user-description");
      const data = await response.json();
      setUserDescription(data.user_description || "");
      setUserName(data.user_name || "User");
    } catch (err) {
      console.error("Failed to load user description:", err);
    }
  }, []);

  const saveSystemPromptSettings = useCallback(
    async (settings: SystemPromptSettings) => {
      try {
        const response = await fetch("/api/settings/system-prompt", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(settings),
        });
        if (response.ok) {
          setSystemPromptSettings(settings);
        }
      } catch (err) {
        console.error("Failed to save system prompt settings:", err);
      }
    },
    []
  );

  const debouncedSaveSystemPromptSettings = useMemo(() => {
    return (settings: SystemPromptSettings) => {
      if (systemPromptSaveTimeoutRef.current) {
        clearTimeout(systemPromptSaveTimeoutRef.current);
      }

      systemPromptSaveTimeoutRef.current = setTimeout(() => {
        saveSystemPromptSettings(settings);
      }, 500);
    };
  }, [saveSystemPromptSettings]);

  const userDescriptionSaveTimeoutRef = useRef<NodeJS.Timeout | null>(null);

  const saveUserDescriptionSettings = useCallback(
    async (description: string, name: string) => {
      try {
        const response = await fetch("/api/settings/user-description", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            user_description: description,
            user_name: name,
          }),
        });
        if (response.ok) {
          setUserDescription(description);
          setUserName(name);
        }
      } catch (err) {
        console.error("Failed to save user description:", err);
      }
    },
    []
  );

  const debouncedSaveUserDescription = useMemo(() => {
    return (description: string, name: string) => {
      if (userDescriptionSaveTimeoutRef.current) {
        clearTimeout(userDescriptionSaveTimeoutRef.current);
      }
      userDescriptionSaveTimeoutRef.current = setTimeout(() => {
        saveUserDescriptionSettings(description, name);
      }, 500);
    };
  }, [saveUserDescriptionSettings]);

  const handleSystemPromptChange = useCallback(
    (
      field: keyof SystemPromptSettings,
      value: string | boolean | SystemPromptItem[]
    ) => {
      setSystemPromptSettings((current) => {
        const newSettings = {
          ...current,
          [field]: value,
        };
        debouncedSaveSystemPromptSettings(newSettings);
        return newSettings;
      });
    },
    [debouncedSaveSystemPromptSettings]
  );

  const addSystemPromptItem = useCallback(() => {
    const newItem: SystemPromptItem = {
      title: "New Prompt",
      content: "",
    };
    handleSystemPromptChange("system_prompts", [
      ...systemPromptSettings.system_prompts,
      newItem,
    ]);
  }, [systemPromptSettings.system_prompts, handleSystemPromptChange]);

  const updateSystemPromptItem = useCallback(
    (index: number, updates: Partial<SystemPromptItem>) => {
      const updatedItems = systemPromptSettings.system_prompts.map((item, i) =>
        i === index ? { ...item, ...updates } : item
      );
      handleSystemPromptChange("system_prompts", updatedItems);
    },
    [systemPromptSettings.system_prompts, handleSystemPromptChange]
  );

  const deleteSystemPromptItem = useCallback(
    (index: number) => {
      const filteredItems = systemPromptSettings.system_prompts.filter(
        (_, i) => i !== index
      );
      handleSystemPromptChange("system_prompts", filteredItems);
    },
    [systemPromptSettings.system_prompts, handleSystemPromptChange]
  );

  const handleUserDescriptionChange = useCallback(
    (value: string) => {
      setUserDescription(value);
      debouncedSaveUserDescription(value, userName);
    },
    [debouncedSaveUserDescription, userName]
  );

  const handleUserNameChange = useCallback(
    (value: string) => {
      setUserName(value);
      debouncedSaveUserDescription(userDescription, value);
    },
    [debouncedSaveUserDescription, userDescription]
  );

  const loadSamplingSettings = useCallback(async () => {
    try {
      const response = await fetch("/api/settings/sampling");
      const data = await response.json();
      setSamplingSettings(data);
    } catch (err) {
      console.error("Failed to load sampling settings:", err);
    }
  }, []);

  const saveSamplingSettings = useCallback(
    async (settings: SamplingSettings) => {
      try {
        const response = await fetch("/api/settings/sampling", {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
          },
          body: JSON.stringify(settings),
        });
        if (response.ok) {
          setSamplingSettings(settings);
        }
      } catch (err) {
        console.error("Failed to save sampling settings:", err);
      }
    },
    []
  );

  const handleSamplingChange = useCallback(
    (field: keyof SamplingSettings, value: number) => {
      setSamplingSettings((current) => {
        const newSettings = {
          ...current,
          [field]: value,
        };
        saveSamplingSettings(newSettings);
        return newSettings;
      });
    },
    [saveSamplingSettings]
  );

  const toggleDarkMode = useCallback(() => {
    setIsDarkMode((current) => !current);
  }, []);

  useEffect(() => {
    if (isDarkMode) {
      document.documentElement.classList.add("dark");
    } else {
      document.documentElement.classList.remove("dark");
    }
    localStorage.setItem("darkMode", JSON.stringify(isDarkMode));
  }, [isDarkMode]);

  useEffect(() => {
    loadSystemPromptSettings();
    loadUserDescription();
    loadSamplingSettings();

    return () => {
      if (systemPromptSaveTimeoutRef.current) {
        clearTimeout(systemPromptSaveTimeoutRef.current);
      }
    };
  }, [loadSystemPromptSettings, loadSamplingSettings]);

  return useMemo(
    () => ({
      state: {
        systemPromptSettings,
        samplingSettings,
        isDarkMode,
        userDescription,
        userName,
      },
      actions: {
        handleSystemPromptChange,
        handleSamplingChange,
        toggleDarkMode,
        handleUserDescriptionChange,
        handleUserNameChange,
        addSystemPromptItem,
        updateSystemPromptItem,
        deleteSystemPromptItem,
      },
    }),
    [
      systemPromptSettings,
      samplingSettings,
      isDarkMode,
      userDescription,
      userName,
      handleSystemPromptChange,
      handleSamplingChange,
      toggleDarkMode,
      handleUserDescriptionChange,
      handleUserNameChange,
      addSystemPromptItem,
      updateSystemPromptItem,
      deleteSystemPromptItem,
    ]
  );
}
