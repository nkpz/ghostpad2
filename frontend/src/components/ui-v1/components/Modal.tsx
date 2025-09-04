import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface ModalProps {
  id: string;
  props?: {
    title?: string;
    size?: "sm" | "md" | "lg" | "xl";
    open?: boolean;
  };
  children?: React.ReactNode;
  onOpenChange?: (open: boolean) => void;
}

function getModalSizeClasses(size?: "sm" | "md" | "lg" | "xl"): string {
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

export function Modal({
  props,
  children,
  onOpenChange,
}: Readonly<ModalProps>) {
  const isOpen = props?.open || false;
  const title = props?.title || "";

  const modalSize = getModalSizeClasses(props?.size);

  return (
    <Dialog open={isOpen} onOpenChange={onOpenChange}>
      <DialogContent className={modalSize}>
        {title && (
          <DialogHeader>
            <DialogTitle>{title}</DialogTitle>
          </DialogHeader>
        )}
        {children}
      </DialogContent>
    </Dialog>
  );
}
