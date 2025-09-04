import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { SettingsSidebar } from "@/components/layout/SettingsSidebar";

interface SettingsModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  isDarkMode: boolean;
  toggleDarkMode: () => void;
}

export function SettingsModal({
  open,
  onOpenChange,
  isDarkMode,
  toggleDarkMode,
}: Readonly<SettingsModalProps>) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-md">
        <DialogHeader>
          <DialogTitle>Settings</DialogTitle>
        </DialogHeader>

        <div className="space-y-6">
          {/* Dark Mode Toggle */}
          <div className="flex items-center justify-between">
            <Label htmlFor="dark-mode">Dark Mode</Label>
            <Switch
              id="dark-mode"
              checked={isDarkMode}
              onCheckedChange={toggleDarkMode}
            />
          </div>

          {/* API Settings */}
          <div>
            <h3 className="text-sm font-medium mb-3">API Settings</h3>
            <SettingsSidebar />
          </div>
        </div>
      </DialogContent>
    </Dialog>
  );
}
