import { useState, useMemo } from "react";
import { Button } from "@/components/ui/button";
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover";
import { Wrench } from "lucide-react";
import { DynamicIcon } from "@/components/ui/DynamicIcon";
import { useToolFeatures } from "@/hooks";
import { useToast } from "@/components/ui/toast";
import { UIv1Modal } from "@/components/ui-v1/UIv1Modal";

interface ToolsDropdownProps {
  activePersonas?: { id: string; name: string }[];
  currentConversationId?: string | null;
  refreshMessages: (conversationId: string) => Promise<void>;
}

export function ToolsDropdown({
  activePersonas,
  currentConversationId,
  refreshMessages,
}: Readonly<ToolsDropdownProps>) {
  const { state: featureState } = useToolFeatures();
  const uiFeatures = useMemo(
    () => featureState.features.filter((f) => f.type === "ui_v1"),
    [featureState.features]
  );

  const [openUIv1Modals, setOpenUIv1Modals] = useState<Record<string, boolean>>(
    {}
  );
  const { show } = useToast();

  const layoutHandlers = {
    modal: (feature: any) => {
      setOpenUIv1Modals((prev) => ({ ...prev, [feature.id]: true }));
    },
    instant: async (feature: any) => {
      try {
        // Execute instant tool via API
        const response = await fetch("/api/tool_submit", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            handler: feature.id,
            params: {
              conversation_id: currentConversationId,
            },
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        show(`${feature.label || "Tool"} executed successfully`);

        if (currentConversationId) {
          await refreshMessages(currentConversationId);
        }
      } catch (error) {
        console.error("Failed to execute instant tool:", error);
        show(`Failed to execute ${feature.label || "tool"}`);
      }
    },
  };

  const handleUIFeatureClick = (feature: any) => {
    const layoutType = feature.layout?.type;
    if (!layoutType) {
      console.error(
        `UI feature '${feature.id}' is missing layout.type property`
      );
      return;
    }
    const handler = layoutHandlers[layoutType as keyof typeof layoutHandlers];
    if (!handler) {
      console.error(
        `No handler found for layout type '${layoutType}' in feature '${feature.id}'`
      );
      return;
    }
    handler(feature);
  };

  const modalFeatures = uiFeatures.filter(
    (feature) => feature.layout?.type === "modal"
  );

  const hasAnyTools = uiFeatures.length > 0;

  if (!hasAnyTools) return null;


  return (
    <>
      <Popover>
        <PopoverTrigger asChild>
          <Button
            variant="ghost"
            size="sm"
            className="h-16 w-16 p-0 hover:bg-muted"
            title="Tools"
          >
            <Wrench className="h-7 w-7 text-muted-foreground" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-48 p-1">
          {/* UI v1 features */}
          {uiFeatures.map((feature) => (
            <Button
              key={feature.id}
              variant="ghost"
              size="sm"
              className="w-full justify-start"
              onClick={() => handleUIFeatureClick(feature)}
            >
              {feature.icon ? (
                <DynamicIcon name={feature.icon} className="h-4 w-4 mr-2" />
              ) : (
                <Wrench className="h-4 w-4 mr-2" />
              )}
              {feature.label || "UI Tool"}
            </Button>
          ))}
        </PopoverContent>
      </Popover>

      {/* UI v1 Modals */}
      {modalFeatures.map((feature) => (
        <UIv1Modal
          key={feature.id}
          feature={feature}
          isOpen={openUIv1Modals[feature.id] || false}
          onOpenChange={(open) => {
            setOpenUIv1Modals((prev) => ({ ...prev, [feature.id]: open }));
          }}
          activePersonas={activePersonas}
          currentConversationId={currentConversationId}
          refreshMessages={refreshMessages}
        />
      ))}
    </>
  );
}
