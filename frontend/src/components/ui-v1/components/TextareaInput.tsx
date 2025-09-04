import { useCallback, useState } from "react";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Sparkles } from "lucide-react";
import PromptEditModal from "@/components/settings/PromptEditModal";

interface ComponentAction {
  type: string;
  trigger: string;
  target: string;
  params?: Record<string, any>;
}

interface TextareaInputProps {
  id: string;
  props?: {
    placeholder?: string;
    value?: string;
    disabled?: boolean;
    className?: string;
    min_height?: string;
    rows?: number;
    submit_target?: string;
    show_ai_edit?: boolean; // Enable AI editing sparkles button
    ai_edit_label?: string; // Custom label for AI editing modal
  };
  actions?: ComponentAction[];
  onValueChange?: (id: string, value: string) => void;
  onAction?: (action: ComponentAction) => Promise<void>;
}

export function TextareaInput({
  id,
  props = {},
  actions = [],
  onValueChange,
  onAction,
}: Readonly<TextareaInputProps>) {
  const value = props.value || "";
  const [isAiEditOpen, setIsAiEditOpen] = useState(false);

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLTextAreaElement>) => {
      const newValue = e.target.value;

      // Notify parent component of value change
      if (onValueChange) {
        onValueChange(id, newValue);
      }
    },
    [id, actions, onValueChange]
  );

  const handleKeyDown = useCallback(
    async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
      if (e.key === "Enter" && e.ctrlKey && onAction && props.submit_target) {
        // Ctrl+Enter to submit (common pattern for textareas)
        const submitAction: ComponentAction = {
          type: "submit",
          trigger: "enter",
          target: props.submit_target,
          params: {},
        };

        await onAction(submitAction);
      }
    },
    [props.submit_target, onAction]
  );

  const handleAiEditSave = useCallback(
    (editedText: string) => {
      if (onValueChange) {
        onValueChange(id, editedText);
      }
    },
    [id, onValueChange]
  );

  const style = props.min_height ? { minHeight: props.min_height } : {};

  return (
    <>
      <div className="space-y-2">
        {props.show_ai_edit && (
          <div className="flex items-center justify-end">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => setIsAiEditOpen(true)}
              disabled={props.disabled}
              aria-label="AI edit text"
            >
              <Sparkles className="h-4 w-4" />
              <span className="sr-only">AI edit</span>
            </Button>
          </div>
        )}
        <Textarea
          id={id}
          value={value}
          onChange={handleChange}
          onKeyDown={handleKeyDown}
          placeholder={props.placeholder}
          disabled={props.disabled}
          className={props.className}
          rows={props.rows}
          style={style}
        />
      </div>

      {/* AI Edit Modal */}
      {props.show_ai_edit && (
        <PromptEditModal
          open={isAiEditOpen}
          onOpenChange={setIsAiEditOpen}
          title={props.ai_edit_label || "Edit Text"}
          baselineText={value}
          onSave={handleAiEditSave}
        />
      )}
    </>
  );
}
