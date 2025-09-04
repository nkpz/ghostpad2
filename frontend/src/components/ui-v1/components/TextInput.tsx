import { useCallback } from "react";
import { Input } from "@/components/ui/input";

interface ComponentAction {
  type: string;
  trigger: string;
  target: string;
  params?: Record<string, any>;
}

interface TextInputProps {
  id: string;
  props?: {
    placeholder?: string;
    value?: string;
    disabled?: boolean;
    className?: string;
    submit_target?: string;
  };
  actions?: ComponentAction[];
  onValueChange?: (id: string, value: string) => void;
  onAction?: (action: ComponentAction) => Promise<void>;
}

export function TextInput({
  id,
  props = {},
  actions = [],
  onValueChange,
  onAction,
}: Readonly<TextInputProps>) {
  const value = props.value || "";

  const handleChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const newValue = e.target.value;

      // Notify parent component of value change
      if (onValueChange) {
        onValueChange(id, newValue);
      }
    },
    [id, actions, onValueChange]
  );

  const handleKeyDown = useCallback(
    async (e: React.KeyboardEvent<HTMLInputElement>) => {
      if (e.key === "Enter" && onAction && props.submit_target) {
        // Create a submit action that references the target button
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

  return (
    <Input
      id={id}
      value={value}
      onChange={handleChange}
      onKeyDown={handleKeyDown}
      placeholder={props.placeholder}
      disabled={props.disabled}
      className={props.className}
    />
  );
}
