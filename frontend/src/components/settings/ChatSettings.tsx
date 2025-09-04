import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Slider } from "@/components/ui/slider";
import { Textarea } from "@/components/ui/textarea";
import {
  SystemPromptSettings,
  SamplingSettings,
  SystemPromptItem,
} from "@/types";
import { useEffect, useState, memo, useMemo, useRef } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Sparkles,
  Trash2,
  ChevronDown,
  ChevronUp,
  Plus,
  Edit,
  ArrowUp,
  ArrowDown,
} from "lucide-react";
import PromptEditModal from "@/components/settings/PromptEditModal";

interface CollapsibleSectionProps {
  title: string;
  description?: string;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}

const CollapsibleSection = memo(
  ({
    title,
    description,
    isOpen,
    onToggle,
    children,
  }: CollapsibleSectionProps) => (
    <div className="border rounded-lg">
      <div
        className="flex items-center justify-between p-4 cursor-pointer hover:bg-muted/50 transition-colors"
        onClick={onToggle}
      >
        <div>
          <h3 className="text-sm font-medium">{title}</h3>
          {description && (
            <p className="text-xs text-muted-foreground mt-1">{description}</p>
          )}
        </div>
        {isOpen ? (
          <ChevronUp className="h-4 w-4 text-muted-foreground" />
        ) : (
          <ChevronDown className="h-4 w-4 text-muted-foreground" />
        )}
      </div>
      {isOpen && <div className="px-4 pb-4">{children}</div>}
    </div>
  )
);

CollapsibleSection.displayName = "CollapsibleSection";

interface ChatSettingsProps {
  systemPromptSettings: SystemPromptSettings;
  samplingSettings: SamplingSettings;
  handleSystemPromptChange: (
    field: keyof SystemPromptSettings,
    value: string | boolean | SystemPromptItem[]
  ) => void;
  handleSamplingChange: (field: keyof SamplingSettings, value: number) => void;
  userDescription?: string;
  handleUserDescriptionChange?: (value: string) => void;
  userName?: string;
  handleUserNameChange?: (value: string) => void;
  addSystemPromptItem: () => void;
  updateSystemPromptItem: (
    index: number,
    updates: Partial<SystemPromptItem>
  ) => void;
  deleteSystemPromptItem: (index: number) => void;
  idPrefix?: string;
}

export const ChatSettings = memo(function ChatSettings({
  systemPromptSettings,
  samplingSettings,
  handleSystemPromptChange,
  handleSamplingChange,
  userDescription = "",
  handleUserDescriptionChange = () => {},
  userName = "User",
  handleUserNameChange = () => {},
  addSystemPromptItem,
  updateSystemPromptItem,
  deleteSystemPromptItem,
  idPrefix = "",
}: ChatSettingsProps) {
  const [systemSnippets, setSystemSnippets] = useState<
    { id: number; name: string; content: string }[]
  >([]);
  const [userSnippets, setUserSnippets] = useState<
    { id: number; name: string; content: string }[]
  >([]);
  const [isSystemSaveOpen, setIsSystemSaveOpen] = useState(false);
  const [isSystemLoadOpen, setIsSystemLoadOpen] = useState(false);
  const [isUserSaveOpen, setIsUserSaveOpen] = useState(false);
  const [isUserLoadOpen, setIsUserLoadOpen] = useState(false);
  const [isUserEditOpen, setIsUserEditOpen] = useState(false);
  const [editingPromptIndex, setEditingPromptIndex] = useState<number | null>(
    null
  );
  const [loadingPromptIndex, setLoadingPromptIndex] = useState<number | null>(
    null
  );
  const [savingPromptIndex, setSavingPromptIndex] = useState<number | null>(
    null
  );
  const [saveName, setSaveName] = useState("");
  const [isSamplingOpen, setIsSamplingOpen] = useState(() => {
    const saved = localStorage.getItem("chatSettings.samplingOpen");
    return saved !== null ? JSON.parse(saved) : true;
  });
  const [isSystemPromptOpen, setIsSystemPromptOpen] = useState(() => {
    const saved = localStorage.getItem("chatSettings.systemPromptOpen");
    return saved !== null ? JSON.parse(saved) : false;
  });
  const [isUserDescriptionOpen, setIsUserDescriptionOpen] = useState(() => {
    const saved = localStorage.getItem("chatSettings.userDescriptionOpen");
    return saved !== null ? JSON.parse(saved) : false;
  });
  const [expandedPromptItems, setExpandedPromptItems] = useState<Set<number>>(
    () => {
      try {
        const saved = localStorage.getItem(`chatSettings.expandedPromptItems`);
        if (saved) {
          const expandedArray = JSON.parse(saved);
          return new Set(expandedArray);
        }
      } catch (e) {
        console.warn(
          "Failed to parse expanded prompt items from localStorage:",
          e
        );
      }
      return new Set();
    }
  );

  const updateExpandedItems = (newExpanded: Set<number>) => {
    setExpandedPromptItems(newExpanded);
    try {
      localStorage.setItem(
        `chatSettings.expandedPromptItems`,
        JSON.stringify(Array.from(newExpanded))
      );
    } catch (e) {
      console.warn("Failed to save expanded prompt items to localStorage:", e);
    }
  };

  useEffect(() => {
    const load = async () => {
      try {
        const resSys = await fetch("/api/library?type=system_prompt");
        const dataSys = await resSys.json();
        setSystemSnippets(dataSys.snippets || []);

        const resUser = await fetch("/api/library?type=user_description");
        const dataUser = await resUser.json();
        setUserSnippets(dataUser.snippets || []);
      } catch (err) {
        console.error("Failed to load library snippets", err);
      }
    };
    load();
  }, []);

  // Validate expanded items when system_prompts changes
  const lastPromptsLengthRef = useRef(0);
  useEffect(() => {
    const promptsLength = systemPromptSettings.system_prompts.length;

    if (promptsLength > 0 && promptsLength !== lastPromptsLengthRef.current) {
      const currentExpanded = Array.from(expandedPromptItems);
      const validIndices = currentExpanded.filter(
        (index) => index >= 0 && index < promptsLength
      );

      if (validIndices.length !== currentExpanded.length) {
        updateExpandedItems(new Set(validIndices));
      }

      lastPromptsLengthRef.current = promptsLength;
    }
  }, [systemPromptSettings.system_prompts.length]);

  const refreshSnippets = async () => {
    try {
      const resSys = await fetch("/api/library?type=system_prompt");
      const dataSys = await resSys.json();
      setSystemSnippets(dataSys.snippets || []);

      const resUser = await fetch("/api/library?type=user_description");
      const dataUser = await resUser.json();
      setUserSnippets(dataUser.snippets || []);
    } catch (err) {
      console.error("Failed to refresh library snippets", err);
    }
  };

  const saveSnippet = async (type: string, name: string, content: string) => {
    await fetch("/api/library", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ type, name, content }),
    });
    await refreshSnippets();
  };

  const openSystemSave = () => {
    setSaveName("");
    setIsSystemSaveOpen(true);
  };
  const openUserSave = () => {
    setSaveName("");
    setIsUserSaveOpen(true);
  };
  const confirmSaveSystem = async () => {
    if (!saveName || savingPromptIndex === null) return;
    // Get the content from the specific prompt item being saved
    const promptItem = systemPromptSettings.system_prompts[savingPromptIndex];
    if (promptItem) {
      await saveSnippet("system_prompt", saveName, promptItem.content);
    }
    setIsSystemSaveOpen(false);
    setSavingPromptIndex(null);
  };
  const confirmSaveUser = async () => {
    if (!saveName) return;
    const userContent = JSON.stringify({
      name: userName || "User",
      description: userDescription || "",
    });
    await saveSnippet("user_description", saveName, userContent);
    setIsUserSaveOpen(false);
  };

  const handleLoadSystemSnippet = (id?: number, itemIndex?: number) => {
    const sid = id;
    const s = systemSnippets.find((x) => String(x.id) === String(sid));
    if (s && itemIndex !== undefined) {
      // Update only the specific prompt item, keeping title and just updating content
      updateSystemPromptItem(itemIndex, { content: s.content });
    }
    setIsSystemLoadOpen(false);
  };

  const handleLoadUserSnippet = (id?: number) => {
    const sid = id;
    const s = userSnippets.find((x) => String(x.id) === String(sid));
    if (s) {
      const parsed = JSON.parse(s.content);
      handleUserNameChange?.(parsed.name || "User");
      handleUserDescriptionChange?.(parsed.description || "");
    }
    setIsUserLoadOpen(false);
  };

  const handleDeleteSnippet = async (id: number) => {
    try {
      await fetch(`/api/library/${id}`, { method: "DELETE" });
      await refreshSnippets();
    } catch (e) {
      console.error(e);
    }
  };

  const processedUserSnippets = useMemo(() => {
    return userSnippets.map((s) => {
      try {
        const parsed = JSON.parse(s.content);
        return {
          ...s,
          displayContent: `${parsed.name}: ${parsed.description}`,
        };
      } catch {
        return { ...s, displayContent: s.content };
      }
    });
  }, [userSnippets]);

  const movePromptUp = (index: number) => {
    if (index > 0) {
      const newPrompts = [...systemPromptSettings.system_prompts];
      [newPrompts[index - 1], newPrompts[index]] = [
        newPrompts[index],
        newPrompts[index - 1],
      ];
      handleSystemPromptChange("system_prompts", newPrompts);

      // Update expanded items to follow the moved items
      const newExpanded = new Set<number>();
      expandedPromptItems.forEach((expandedIndex) => {
        if (expandedIndex === index) {
          newExpanded.add(index - 1);
        } else if (expandedIndex === index - 1) {
          newExpanded.add(index);
        } else {
          newExpanded.add(expandedIndex);
        }
      });
      updateExpandedItems(newExpanded);
    }
  };

  const movePromptDown = (index: number) => {
    if (index < systemPromptSettings.system_prompts.length - 1) {
      const newPrompts = [...systemPromptSettings.system_prompts];
      [newPrompts[index], newPrompts[index + 1]] = [
        newPrompts[index + 1],
        newPrompts[index],
      ];
      handleSystemPromptChange("system_prompts", newPrompts);

      // Update expanded items to follow the moved items
      const newExpanded = new Set<number>();
      expandedPromptItems.forEach((expandedIndex) => {
        if (expandedIndex === index) {
          newExpanded.add(index + 1);
        } else if (expandedIndex === index + 1) {
          newExpanded.add(index);
        } else {
          newExpanded.add(expandedIndex);
        }
      });
      updateExpandedItems(newExpanded);
    }
  };

  return (
    <>
      <div className="space-y-4">
        <CollapsibleSection
          title="Sampling Parameters"
          description="Control the AI's creativity and randomness."
          isOpen={isSamplingOpen}
          onToggle={() => {
            const newValue = !isSamplingOpen;
            setIsSamplingOpen(newValue);
            localStorage.setItem(
              "chatSettings.samplingOpen",
              JSON.stringify(newValue)
            );
          }}
        >
          <div className="space-y-4">
            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs">Temperature</Label>
                <span className="text-xs text-muted-foreground">
                  {samplingSettings.temperature.toFixed(2)}
                </span>
              </div>
              <Slider
                min={0}
                max={2}
                step={0.1}
                value={samplingSettings.temperature}
                onChange={(e) =>
                  handleSamplingChange("temperature", e.target.valueAsNumber)
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Conservative</span>
                <span>Creative</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs">Top P</Label>
                <span className="text-xs text-muted-foreground">
                  {samplingSettings.top_p.toFixed(2)}
                </span>
              </div>
              <Slider
                min={0.1}
                max={1}
                step={0.05}
                value={samplingSettings.top_p}
                onChange={(e) =>
                  handleSamplingChange("top_p", e.target.valueAsNumber)
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Focused</span>
                <span>Diverse</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs">Max Tokens</Label>
                <span className="text-xs text-muted-foreground">
                  {samplingSettings.max_tokens}
                </span>
              </div>
              <Slider
                min={100}
                max={4000}
                step={100}
                value={samplingSettings.max_tokens}
                onChange={(e) =>
                  handleSamplingChange("max_tokens", e.target.valueAsNumber)
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Short</span>
                <span>Long</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs">Frequency Penalty</Label>
                <span className="text-xs text-muted-foreground">
                  {samplingSettings.frequency_penalty.toFixed(2)}
                </span>
              </div>
              <Slider
                min={-2}
                max={2}
                step={0.1}
                value={samplingSettings.frequency_penalty}
                onChange={(e) =>
                  handleSamplingChange(
                    "frequency_penalty",
                    e.target.valueAsNumber
                  )
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Repetitive</span>
                <span>Diverse</span>
              </div>
            </div>

            <div className="space-y-2">
              <div className="flex justify-between items-center">
                <Label className="text-xs">Presence Penalty</Label>
                <span className="text-xs text-muted-foreground">
                  {samplingSettings.presence_penalty.toFixed(2)}
                </span>
              </div>
              <Slider
                min={-2}
                max={2}
                step={0.1}
                value={samplingSettings.presence_penalty}
                onChange={(e) =>
                  handleSamplingChange(
                    "presence_penalty",
                    e.target.valueAsNumber
                  )
                }
                className="w-full"
              />
              <div className="flex justify-between text-xs text-muted-foreground">
                <span>Repetitive</span>
                <span>Novel</span>
              </div>
            </div>

            {samplingSettings.seed !== undefined && (
              <div className="space-y-2">
                <div className="flex justify-between items-center">
                  <Label className="text-xs">Seed</Label>
                  <span className="text-xs text-muted-foreground">
                    {samplingSettings.seed >= 0
                      ? samplingSettings.seed
                      : "Random"}
                  </span>
                </div>
                <Slider
                  min={-1}
                  max={999999}
                  step={1}
                  value={samplingSettings.seed || 0}
                  onChange={(e) =>
                    handleSamplingChange("seed", e.target.valueAsNumber)
                  }
                  className="w-full"
                />
                <div className="flex justify-between text-xs text-muted-foreground">
                  <span>Deterministic</span>
                  <span>Varied</span>
                </div>
              </div>
            )}
          </div>
        </CollapsibleSection>

        <CollapsibleSection
          title="System Prompt"
          description="Configure system-level instructions for the AI model."
          isOpen={isSystemPromptOpen}
          onToggle={() => {
            const newValue = !isSystemPromptOpen;
            setIsSystemPromptOpen(newValue);
            localStorage.setItem(
              "chatSettings.systemPromptOpen",
              JSON.stringify(newValue)
            );
          }}
        >
          <div className="space-y-4">
            <div className="flex items-center space-x-2">
              <Switch
                id={`system_prompt_enabled${idPrefix}`}
                checked={systemPromptSettings.enabled}
                onCheckedChange={(checked) =>
                  handleSystemPromptChange("enabled", checked)
                }
              />
              <Label
                htmlFor={`system_prompt_enabled${idPrefix}`}
                className="text-xs"
              >
                Enable system prompt
              </Label>
            </div>

            <div>
              <div className="flex items-center justify-between mb-2">
                <Label className="text-xs">System Prompts</Label>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={addSystemPromptItem}
                  disabled={!systemPromptSettings.enabled}
                >
                  <Plus className="h-4 w-4" />
                  Add Prompt
                </Button>
              </div>

              {systemPromptSettings.system_prompts.map((item, index) => {
                const isExpanded = expandedPromptItems.has(index);

                return (
                  <div key={index} className="border">
                    <div className="p-2">
                      {/* Row 1: Title */}
                      <div className="flex-1 min-w-0">
                        <span className="text-sm font-medium text-muted-foreground truncate">
                          {item.title || `Prompt ${index + 1}`}
                        </span>
                      </div>

                      {/* Row 2: Buttons */}
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => movePromptUp(index)}
                            disabled={
                              !systemPromptSettings.enabled || index === 0
                            }
                          >
                            <ArrowUp className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => movePromptDown(index)}
                            disabled={
                              !systemPromptSettings.enabled ||
                              index ===
                                systemPromptSettings.system_prompts.length - 1
                            }
                          >
                            <ArrowDown className="h-4 w-4" />
                          </Button>
                        </div>

                        <div className="flex items-center gap-1">
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => {
                              const newExpanded = new Set(expandedPromptItems);
                              if (isExpanded) {
                                newExpanded.delete(index);
                              } else {
                                newExpanded.add(index);
                              }
                              updateExpandedItems(newExpanded);
                            }}
                            disabled={!systemPromptSettings.enabled}
                          >
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button
                            size="sm"
                            variant="ghost"
                            onClick={() => deleteSystemPromptItem(index)}
                            disabled={!systemPromptSettings.enabled}
                          >
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </div>
                    </div>

                    {isExpanded && (
                      <div className="px-3 py-3 space-y-3 border-t">
                        <div className="space-y-2">
                          <Label className="text-xs">Title</Label>
                          <Input
                            value={item.title}
                            onChange={(e) =>
                              updateSystemPromptItem(index, {
                                title: e.target.value,
                              })
                            }
                            placeholder="Prompt title"
                            disabled={!systemPromptSettings.enabled}
                            className="text-xs"
                          />
                        </div>
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <Label className="text-xs">Prompt</Label>
                            <Button
                              size="sm"
                              variant="ghost"
                              onClick={() => {
                                setEditingPromptIndex(index);
                              }}
                              disabled={!systemPromptSettings.enabled}
                              aria-label="AI edit system prompt"
                            >
                              <Sparkles className="h-4 w-4" />
                              <span className="sr-only">AI edit</span>
                            </Button>
                          </div>
                          <Textarea
                            value={item.content}
                            onChange={(e) =>
                              updateSystemPromptItem(index, {
                                content: e.target.value,
                              })
                            }
                            placeholder="Enter your system prompt content here."
                            disabled={!systemPromptSettings.enabled}
                            className="min-h-24 text-xs"
                          />
                        </div>
                        <Label>Library</Label>
                        <div className="flex gap-2">
                          <Button
                            size="sm"
                            variant="outline"
                            onClick={() => {
                              setLoadingPromptIndex(index);
                              setIsSystemLoadOpen(true);
                            }}
                            disabled={!systemPromptSettings.enabled}
                          >
                            Load Prompt
                          </Button>
                          <Button
                            size="sm"
                            onClick={() => {
                              setSavingPromptIndex(index);
                              openSystemSave();
                            }}
                            disabled={!systemPromptSettings.enabled}
                          >
                            Save Prompt
                          </Button>
                        </div>
                      </div>
                    )}
                  </div>
                );
              })}

              {systemPromptSettings.system_prompts.length === 0 && (
                <div className="text-center py-8 text-muted-foreground text-sm">
                  No system prompts configured. Click "Add Prompt" to create
                  your first one.
                </div>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Switch
                id={`include_datetime${idPrefix}`}
                checked={systemPromptSettings.include_datetime}
                onCheckedChange={(checked) =>
                  handleSystemPromptChange("include_datetime", checked)
                }
                disabled={!systemPromptSettings.enabled}
              />
              <Label
                htmlFor={`include_datetime${idPrefix}`}
                className="text-xs"
              >
                Include current date and time in system prompt
              </Label>
            </div>

            <div className="space-y-2">
              <Label htmlFor={`thinking_mode${idPrefix}`} className="text-xs">
                Toggle Thinking
              </Label>
              <select
                id={`thinking_mode${idPrefix}`}
                value={systemPromptSettings.thinking_mode}
                onChange={(e) =>
                  handleSystemPromptChange("thinking_mode", e.target.value)
                }
                disabled={!systemPromptSettings.enabled}
                className="w-full px-3 py-2 text-xs border border-input bg-background rounded-md focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
              >
                <option value="default">Default (no modification)</option>
                <option value="</think>">
                  &lt;/think&gt; (disable thinking)
                </option>
                <option value="/no_think">/no_think (disable thinking)</option>
                <option value="<no_think>">
                  &lt;no_think&gt; (disable thinking)
                </option>
                <option value="<think>">
                  &lt;think&gt; (force enable thinking)
                </option>
                <option value="/think">/think (force enable thinking)</option>
              </select>
              <p className="text-xs text-muted-foreground">
                Controls the AI's thinking process. Default uses model defaults,
                other options override thinking behavior.
              </p>
            </div>
          </div>
        </CollapsibleSection>

        <CollapsibleSection
          title="User Description"
          description="Describe the persona who typically plays the User role."
          isOpen={isUserDescriptionOpen}
          onToggle={() => {
            const newValue = !isUserDescriptionOpen;
            setIsUserDescriptionOpen(newValue);
            localStorage.setItem(
              "chatSettings.userDescriptionOpen",
              JSON.stringify(newValue)
            );
          }}
        >
          <div className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor={`user_name${idPrefix}`} className="text-xs">
                User Name
              </Label>
              <Input
                id={`user_name${idPrefix}`}
                placeholder="Enter the user's name"
                value={userName}
                onChange={(e) =>
                  handleUserNameChange?.(e.target.value)
                }
                className="text-xs"
              />
            </div>
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label
                  htmlFor={`user_description${idPrefix}`}
                  className="text-xs"
                >
                  User Description
                </Label>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsUserEditOpen(true)}
                  aria-label="AI edit user description"
                >
                  <Sparkles className="h-4 w-4" />
                  <span className="sr-only fixed">AI edit</span>
                </Button>
              </div>
              <Textarea
                id={`user_description${idPrefix}`}
                placeholder="Describe the typical user persona."
                value={userDescription}
                onChange={(e) =>
                  handleUserDescriptionChange?.(e.target.value)
                }
                className="min-h-20 text-xs"
              />
              <div className="flex items-center gap-2 mt-2">
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => setIsUserLoadOpen(true)}
                  >
                    Load from library
                  </Button>
                  <Button size="sm" onClick={openUserSave}>
                    Save to library
                  </Button>
                </div>
              </div>
            </div>
          </div>
        </CollapsibleSection>
      </div>

      {/* System Save Modal */}
      <Dialog
        open={isSystemSaveOpen}
        onOpenChange={(open) => {
          setIsSystemSaveOpen(open);
          if (!open) setSavingPromptIndex(null);
        }}
      >
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Save System Prompt</DialogTitle>
            <DialogDescription>
              Provide a name for this system prompt snippet.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Snippet name"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsSystemSaveOpen(false);
                setSavingPromptIndex(null);
              }}
            >
              Cancel
            </Button>
            <Button size="sm" onClick={confirmSaveSystem}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* System Load Modal */}
      <Dialog
        open={isSystemLoadOpen}
        onOpenChange={(open) => {
          setIsSystemLoadOpen(open);
          if (!open) setLoadingPromptIndex(null);
        }}
      >
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Load System Prompt</DialogTitle>
            <DialogDescription>
              Select a system prompt snippet to load.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 max-h-80 overflow-auto">
            {systemSnippets.map((s) => (
              <div
                key={s.id}
                className="p-2 rounded border flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground line-clamp-3">
                    {s.content}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() =>
                      handleLoadSystemSnippet(s.id, loadingPromptIndex || 0)
                    }
                  >
                    Load
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteSnippet(s.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => {
                setIsSystemLoadOpen(false);
                setLoadingPromptIndex(null);
              }}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Save Modal */}
      <Dialog open={isUserSaveOpen} onOpenChange={setIsUserSaveOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Save User Description</DialogTitle>
            <DialogDescription>
              Provide a name for this user description snippet.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Input
              value={saveName}
              onChange={(e) => setSaveName(e.target.value)}
              placeholder="Snippet name"
            />
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsUserSaveOpen(false)}
            >
              Cancel
            </Button>
            <Button size="sm" onClick={confirmSaveUser}>
              Save
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* User Load Modal */}
      <Dialog open={isUserLoadOpen} onOpenChange={setIsUserLoadOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Load User Description</DialogTitle>
            <DialogDescription>
              Select a user description snippet to load.
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-2 max-h-80 overflow-auto">
            {processedUserSnippets.map((s) => (
              <div
                key={s.id}
                className="p-2 rounded border flex items-center justify-between"
              >
                <div>
                  <div className="font-medium">{s.name}</div>
                  <div className="text-xs text-muted-foreground line-clamp-3">
                    {s.displayContent}
                  </div>
                </div>
                <div className="flex gap-2">
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleLoadUserSnippet(s.id)}
                  >
                    Load
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    onClick={() => handleDeleteSnippet(s.id)}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </div>
            ))}
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsUserLoadOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Edit Modals */}
      <PromptEditModal
        open={isUserEditOpen}
        onOpenChange={setIsUserEditOpen}
        title="Edit User Description"
        baselineText={userDescription || ""}
        onSave={(edited) =>
          handleUserDescriptionChange?.(edited)
        }
      />

      {/* Individual System Prompt AI Edit Modal */}
      {editingPromptIndex !== null && (
        <PromptEditModal
          open={editingPromptIndex !== null}
          onOpenChange={(open) => {
            if (!open) setEditingPromptIndex(null);
          }}
          title={`Edit ${
            systemPromptSettings.system_prompts[editingPromptIndex]?.title ||
            `Prompt ${editingPromptIndex + 1}`
          }`}
          baselineText={
            systemPromptSettings.system_prompts[editingPromptIndex]?.content ||
            ""
          }
          onSave={(edited) => {
            if (editingPromptIndex !== null) {
              updateSystemPromptItem(editingPromptIndex, { content: edited });
              setEditingPromptIndex(null);
            }
          }}
        />
      )}
    </>
  );
});
