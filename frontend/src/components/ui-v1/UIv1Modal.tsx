import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { ToolFeature } from "@/types";
import { ComponentListRenderer } from "./ComponentListRenderer";

interface UIv1ModalProps {
  feature: ToolFeature;
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  activePersonas?: { id: string; name: string }[];
  currentConversationId?: string | null;
  refreshMessages?: (conversationId: string) => Promise<void>;
}

function getModalSizeClasses(size?: string): string {
  switch (size) {
    case "sm":
      return "w-[40vw] max-w-sm";
    case "lg":
      return "w-[80vw] max-w-4xl";
    case "xl":
      return "w-[90vw] max-w-6xl";
    default:
      return "w-[60vw] max-w-2xl";
  }
}

export function UIv1Modal({
  feature,
  isOpen,
  onOpenChange,
  activePersonas,
  currentConversationId,
  refreshMessages,
}: Readonly<UIv1ModalProps>) {
  if (!feature.layout || feature.layout.type !== "modal") {
    return null;
  }

  const { layout } = feature;
  const modalSize = getModalSizeClasses(layout.size);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className={modalSize}>
        <DialogHeader>
          <DialogTitle>{layout.title || feature.label}</DialogTitle>
        </DialogHeader>
        {/* Render components */}
        {layout.components && layout.components.length > 0 ? (
          <ComponentListRenderer
            components={layout.components}
            activePersonas={activePersonas}
            currentConversationId={currentConversationId}
            refreshMessages={refreshMessages}
          />
        ) : (
          <div className="text-center text-muted-foreground py-8">
            Empty modal - UI components will be rendered here
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
