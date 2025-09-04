import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Persona } from "@/types";
import { useState } from "react";

interface PersonaDeleteDialogProps {
  isOpen: boolean;
  onOpenChange: (open: boolean) => void;
  onConfirm: (deleteConversations: boolean) => void;
  onCancel: () => void;
  persona: Persona | null;
}

export function PersonaDeleteDialog({
  isOpen,
  onOpenChange,
  onConfirm,
  onCancel,
  persona,
}: Readonly<PersonaDeleteDialogProps>) {
  const [deleteConversations, setDeleteConversations] = useState(false);

  const handleConfirm = () => {
    onConfirm(deleteConversations);
    setDeleteConversations(false);
  };

  const handleCancel = () => {
    onCancel();
    setDeleteConversations(false);
  };

  const handleOpenChange = (open: boolean) => {
    if (!open) {
      setDeleteConversations(false);
    }
    onOpenChange(open);
  };

  return (
    <Dialog open={isOpen} onOpenChange={handleOpenChange}>
      <DialogContent className="max-w-lg">
        <DialogHeader>
          <DialogTitle>Delete Persona</DialogTitle>
          <DialogDescription>
            Are you sure you want to delete "{persona?.name}"? This action
            cannot be undone and will permanently remove this persona.
          </DialogDescription>
        </DialogHeader>
        
        <div className="py-4">
          <label className="flex items-center space-x-2 cursor-pointer">
            <input
              type="checkbox"
              checked={deleteConversations}
              onChange={(e) => setDeleteConversations(e.target.checked)}
              className="rounded border-gray-300 text-primary focus:ring-primary"
            />
            <span className="text-sm text-gray-700">
              Delete all associated conversations
            </span>
          </label>
          {deleteConversations && (
            <p className="text-xs text-red-600 mt-2">
              Warning: This will also permanently delete all conversations that include this persona.
            </p>
          )}
        </div>

        <DialogFooter>
          <Button variant="outline" onClick={handleCancel}>
            Cancel
          </Button>
          <Button variant="destructive" onClick={handleConfirm}>
            Delete
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}