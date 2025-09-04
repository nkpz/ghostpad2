import { useState, useCallback } from "react";
import { Button } from "@/components/ui/button";

interface UIButtonProps {
  id: string;
  props?: {
    label?: string;
    variant?: "default" | "outline" | "ghost" | "destructive";
    size?: "default" | "sm" | "lg" | "icon";
    disabled?: boolean;
    className?: string;
  };
  actions?: Array<{
    type: string;
    trigger: string;
    target: string;
    params?: Record<string, any>;
  }>;
  onAction?: (action: any) => Promise<void>;
  getAllValues?: () => Record<string, string>;
}

export function UIButton({
  props = {},
  actions = [],
  onAction,
}: Readonly<UIButtonProps>) {
  const [isLoading, setIsLoading] = useState(false);

  const handleClick = useCallback(async () => {
    try {
      setIsLoading(true);

      // Handle click actions
      const clickActions = actions.filter(
        (action) => action.trigger === "click"
      );

      for (const action of clickActions) {
        if (onAction) {
          await onAction(action);
        }
      }
    } catch (error) {
      console.error("Button action error:", error);
    } finally {
      setIsLoading(false);
    }
  }, [actions, onAction]);

  return (
    <Button
      onClick={handleClick}
      variant={props.variant || "default"}
      size={props.size || "default"}
      disabled={props.disabled || isLoading}
      className={props.className}
    >
      {isLoading ? "Loading..." : props.label || "Button"}
    </Button>
  );
}
