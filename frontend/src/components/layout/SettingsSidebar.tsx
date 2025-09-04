import { useState, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AutocompleteInput } from "@/components/ui/autocomplete-input";
import { OpenAISettings, ModelInfo, ConnectionTestResponse } from "@/types";

export function SettingsSidebar() {
  const [settings, setSettings] = useState<OpenAISettings>({
    base_url: "",
    api_key: "",
    model_name: "",
    streaming_enabled: true,
  });
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState("");
  const [availableModels, setAvailableModels] = useState<ModelInfo[]>([]);

  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      const response = await fetch("/api/settings/openai");
      const data: OpenAISettings = await response.json();
      setSettings(data);
    } catch (error) {
      console.error("Failed to fetch settings:", error);
      setMessage("Failed to load settings");
    } finally {
      setLoading(false);
    }
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage("");

    try {
      const response = await fetch("/api/settings/openai", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });

      if (response.ok) {
        setMessage("Settings saved successfully!");
        // Dispatch a custom event to notify the main app that settings changed
        window.dispatchEvent(new CustomEvent("settingsUpdated"));
      } else {
        setMessage("Failed to save settings");
      }
    } catch (error) {
      console.error("Failed to save settings:", error);
      setMessage("Failed to save settings");
    } finally {
      setSaving(false);
    }
  };

  const handleInputChange = (
    field: keyof OpenAISettings,
    value: string | boolean
  ) => {
    setSettings((prev) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleTestConnection = async () => {
    setTesting(true);
    setMessage("");

    try {
      const response = await fetch("/api/settings/openai/test", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify(settings),
      });

      const result: ConnectionTestResponse = await response.json();

      if (result.success) {
        setMessage(result.message);
        if (result.model_info?.models) {
          setAvailableModels(result.model_info.models);
        }
      } else {
        setMessage(result.message);
        setAvailableModels([]);
      }
    } catch (error) {
      console.error("Failed to test connection:", error);
      setMessage("Failed to test connection");
      setAvailableModels([]);
    } finally {
      setTesting(false);
    }
  };

  if (loading) {
    return <div className="p-4">Loading settings...</div>;
  }

  const modelOptions = availableModels.map((model) => ({
    id: model.id,
    label: model.id,
    sublabel: model.owned_by ? `by ${model.owned_by}` : undefined,
  }));

  return (
    <div className="space-y-4">
      <div className="space-y-2">
        <Label htmlFor="base_url">API Base URL</Label>
        <Input
          id="base_url"
          type="url"
          placeholder="https://api.openai.com/v1"
          value={settings.base_url}
          onChange={(e) => handleInputChange("base_url", e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="api_key">API Key</Label>
        <Input
          id="api_key"
          type="password"
          placeholder="sk-..."
          value={settings.api_key}
          onChange={(e) => handleInputChange("api_key", e.target.value)}
        />
      </div>

      <div className="space-y-2">
        <Label htmlFor="model_name">Model Name</Label>
        <AutocompleteInput
          id="model_name"
          value={settings.model_name}
          onChange={(value) => handleInputChange("model_name", value)}
          options={modelOptions}
          placeholder={
            availableModels.length === 0
              ? "Test connection first to load models"
              : "Type or select a model..."
          }
        />
      </div>

      <div className="space-y-4 pt-4">
        <div className="flex gap-2">
          <Button
            onClick={handleTestConnection}
            disabled={testing || !settings.base_url || !settings.api_key}
            variant="outline"
            className="flex-1"
            size="sm"
          >
            {testing ? "Testing..." : "Test Connection"}
          </Button>
          <Button
            onClick={handleSave}
            disabled={saving}
            className="flex-1"
            size="sm"
          >
            {saving ? "Saving..." : "Save Settings"}
          </Button>
        </div>

        {message && (
          <div
            className={`text-sm p-2 rounded ${
              message.includes("successful")
                ? "text-green-700 bg-green-50 border border-green-200"
                : "text-red-700 bg-red-50 border border-red-200"
            }`}
          >
            {message}
          </div>
        )}
      </div>
    </div>
  );
}
