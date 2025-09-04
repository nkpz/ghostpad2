import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { DataSource } from "@/types";

interface LibrarySaverProps {
  id: string;
  data_source: DataSource;
  props?: {
    placeholder?: string;
    save_button_text?: string;
  };
  getValueById?: (id: string) => string;
  onAction?: (action: any) => Promise<void>;
}

export function LibrarySaver({
  data_source,
  props,
  getValueById,
  onAction,
}: Readonly<LibrarySaverProps>) {
  const [saveName, setSaveName] = useState("");
  const [saving, setSaving] = useState(false);

  const handleSave = async () => {
    if (!saveName.trim()) {
      alert("Please enter a name for the library item");
      return;
    }

    // Get the content to save from the specified content source
    const currentValue =
      getValueById && data_source.content_source_id
        ? getValueById(data_source.content_source_id)
        : "";

    if (!currentValue.trim()) {
      alert("Cannot save empty content");
      return;
    }

    try {
      setSaving(true);
      const response = await fetch("/api/library", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          type: data_source.library_type,
          name: saveName.trim(),
          content: currentValue,
        }),
      });

      if (response.ok) {
        setSaveName("");
        if (onAction) {
          await onAction({
            type: "library_save_success",
            name: saveName.trim(),
          });
        }
      } else {
        throw new Error("Failed to save to library");
      }
    } catch (error) {
      console.error("Failed to save library item:", error);
      alert("Failed to save to library");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Input
        placeholder={props?.placeholder || "Library item name"}
        value={saveName}
        onChange={(e) => setSaveName(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" && !saving) {
            handleSave();
          }
        }}
      />
      <Button onClick={handleSave} disabled={!saveName.trim() || saving}>
        {saving ? "Saving..." : props?.save_button_text || "Save"}
      </Button>
    </div>
  );
}
