import { useState } from "react";
import { Button } from "@/components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { LibraryLoader } from "./LibraryLoader";
import { LibrarySaver } from "./LibrarySaver";
import { DataSource } from "@/types";

interface LibraryManagerProps {
  id: string;
  data_source: DataSource;
  props?: {
    placeholder?: string;
  };
  getValueById?: (id: string) => string;
  onValueChange?: (id: string, value: string) => void;
}

export function LibraryManager({
  id,
  data_source,
  props,
  getValueById,
  onValueChange,
}: Readonly<LibraryManagerProps>) {
  const [loadModalOpen, setLoadModalOpen] = useState(false);
  const [saveModalOpen, setSaveModalOpen] = useState(false);

  const handleLibraryLoad = async (action: any) => {
    if (action.type === "library_load" && onValueChange) {
      onValueChange(action.target_component_id, action.content);
      setLoadModalOpen(false);
    }
  };

  const handleLibrarySave = async (action: any) => {
    if (action.type === "library_save_success") {
      setSaveModalOpen(false);
    }
  };

  return (
    <>
      <div className="flex gap-2">
        <Button variant="outline" onClick={() => setLoadModalOpen(true)}>
          Load from library
        </Button>
        <Button variant="outline" onClick={() => setSaveModalOpen(true)}>
          Save to library
        </Button>
      </div>

      {/* Load Modal */}
      <Dialog open={loadModalOpen} onOpenChange={setLoadModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Load from Library</DialogTitle>
          </DialogHeader>
          <LibraryLoader
            id={`${id}_loader`}
            data_source={data_source}
            props={{
              height: "400px",
              placeholder: props?.placeholder || "No library items found",
            }}
            onAction={handleLibraryLoad}
          />
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setLoadModalOpen(false)}
            >
              Close
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Save Modal */}
      <Dialog open={saveModalOpen} onOpenChange={setSaveModalOpen}>
        <DialogContent className="max-w-xl">
          <DialogHeader>
            <DialogTitle>Save to Library</DialogTitle>
          </DialogHeader>
          <LibrarySaver
            id={`${id}_saver`}
            data_source={{
              ...data_source,
              content_source_id: data_source.target_component_id,
            }}
            props={{
              placeholder: "Library item name",
            }}
            getValueById={getValueById}
            onAction={handleLibrarySave}
          />
          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setSaveModalOpen(false)}
            >
              Cancel
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>
  );
}
