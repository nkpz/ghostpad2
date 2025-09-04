import { useEffect, useMemo, useState } from "react";
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";

interface PromptEditModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  baselineText: string; // Last saved (or starting) value used for Revert
  onSave: (edited: string) => void; // Persist or propagate edited text
}

export function PromptEditModal({ open, onOpenChange, title = "Edit Text", baselineText, onSave }: Readonly<PromptEditModalProps>) {
  const [instructions, setInstructions] = useState("");
  const [workingText, setWorkingText] = useState(baselineText);
  const [isGenerating, setIsGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      // Reset state each time the modal opens
      setInstructions("");
      setWorkingText(baselineText);
      setError(null);
    }
  }, [open, baselineText]);

  const canGenerate = useMemo(() => instructions.trim().length > 0 && !isGenerating, [instructions, isGenerating]);

  const handleGenerate = async () => {
    if (!canGenerate) return;
    setIsGenerating(true);
    setError(null);
    try {
      // Adjust instructions based on whether we have existing text
      const isGenerateFromScratch = !workingText.trim();
      const finalInstructions = isGenerateFromScratch 
        ? `Generate new content: ${instructions}`
        : `Edit the following text: ${instructions}`;
      
      const res = await fetch("/api/prompt/edit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          draft: workingText || "", 
          instructions: finalInstructions
        })
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data.detail || `Request failed with ${res.status}`);
      }
      const data = await res.json();
      setWorkingText(data.edited || "");
    } catch (e: any) {
      setError(e?.message || "Failed to generate edits");
    } finally {
      setIsGenerating(false);
    }
  };

  const handleRevert = () => {
    setWorkingText(baselineText);
  };

  const handleSave = () => {
    onSave(workingText);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>{title}</DialogTitle>
          <DialogDescription>Preview the current draft, add instructions, and let AI propose edits. You can iterate multiple times before saving.</DialogDescription>
        </DialogHeader>

        <div className="space-y-3">
          <div>
            <label htmlFor="edit-draft-textarea" className="text-xs block mb-1">Current Draft</label>
            <Textarea id="edit-draft-textarea" value={workingText} onChange={(e) => setWorkingText(e.target.value)} className="min-h-40 text-xs" />
          </div>
          <div>
            <label htmlFor="edit-instructions-input" className="text-xs block mb-1">Instructions</label>
            <Input id="edit-instructions-input" value={instructions} onChange={(e) => setInstructions(e.target.value)} placeholder="e.g., Make it more concise and friendlier in tone" />
          </div>
          {error ? <div className="text-xs text-destructive">{error}</div> : null}
        </div>

        <DialogFooter>
          <div className="flex w-full items-center justify-between gap-2">
            <div className="flex gap-2">
              <Button variant="outline" size="sm" onClick={handleRevert}>Revert</Button>
            </div>
            <div className="flex gap-2">
              <Button size="sm" onClick={handleGenerate} disabled={!canGenerate}>
                {isGenerating ? "Generating..." : "Generate"}
              </Button>
              <Button size="sm" variant="secondary" onClick={handleSave}>Save</Button>
            </div>
          </div>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

export default PromptEditModal;


