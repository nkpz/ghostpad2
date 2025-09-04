import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { ToolInfo } from "@/types";

interface ToolFileModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileName: string;
  tools: ToolInfo[];
  onToggleTool: (tool: ToolInfo, enabled: boolean) => Promise<void>;
  onToggleAllTools: (enabled: boolean) => Promise<void>;
}

export function ToolFileModal({ 
  isOpen, 
  onClose, 
  fileName, 
  tools, 
  onToggleTool,
  onToggleAllTools 
}: Readonly<ToolFileModalProps>) {
  const [isUpdating, setIsUpdating] = useState(false);
  
  const enabledCount = tools.filter(t => t.enabled).length;
  const totalCount = tools.length;
  const allEnabled = enabledCount === totalCount;
  const anyEnabled = enabledCount > 0;

  const handleToggleAll = async (enabled: boolean) => {
    setIsUpdating(true);
    try {
      await onToggleAllTools(enabled);
    } finally {
      setIsUpdating(false);
    }
  };

  const handleToggleTool = async (tool: ToolInfo, enabled: boolean) => {
    setIsUpdating(true);
    try {
      await onToggleTool(tool, enabled);
    } finally {
      setIsUpdating(false);
    }
  };

  return (
    <Dialog open={isOpen} onOpenChange={onClose}>
      <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle className="flex items-center justify-between">
            <span>Tools in {fileName}</span>
            <span className="text-sm font-normal text-muted-foreground">
              {enabledCount}/{totalCount} enabled
            </span>
          </DialogTitle>
        </DialogHeader>
        
        <div className="space-y-4">
          {/* File-level controls */}
          <div className="flex items-center justify-between p-3 bg-muted/30 rounded-lg">
            <div>
              <div className="font-medium">File-level control</div>
              <div className="text-sm text-muted-foreground">
                Toggle all tools in this file
              </div>
            </div>
            <div className="flex items-center gap-3">
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleAll(false)}
                disabled={!anyEnabled || isUpdating}
              >
                Disable All
              </Button>
              <Button
                variant="outline"
                size="sm"
                onClick={() => handleToggleAll(true)}
                disabled={allEnabled || isUpdating}
              >
                Enable All
              </Button>
            </div>
          </div>

          {/* Individual tools */}
          <div className="space-y-2">
            <div className="text-sm font-medium text-muted-foreground">Individual Tools</div>
            <div className="divide-y rounded-md border">
              {tools.map((tool) => (
                <div key={tool.id} className="p-3">
                  <div className="space-y-2">
                    {/* Title line */}
                    <div className="flex items-center gap-2 min-w-0">
                      <span className="font-medium truncate">{tool.name}</span>
                    </div>
                    
                    {/* Tags line */}
                    <div className="flex items-center gap-2">
                      {tool.auto_tool && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-blue-100 text-blue-700">auto</span>
                      )}
                      {tool.one_time && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-yellow-100 text-yellow-700">one-time</span>
                      )}
                      {tool.ui_feature && (
                        <span className="text-[10px] px-1.5 py-0.5 rounded bg-green-100 text-green-700">ui-feature</span>
                      )}
                    </div>

                    {/* Description + switch line */}
                    <div className="flex items-center justify-between gap-2">
                      <div className="text-sm text-muted-foreground max-w-prose flex-1">
                        {tool.description || "No description available"}
                      </div>
                      <div className="flex items-center gap-2 shrink-0">
                        <Label htmlFor={`tool-${tool.id}`}>Enabled</Label>
                        <Switch
                          id={`tool-${tool.id}`}
                          checked={!!tool.enabled}
                          onCheckedChange={(v) => handleToggleTool(tool, v)}
                          disabled={isUpdating}
                        />
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}