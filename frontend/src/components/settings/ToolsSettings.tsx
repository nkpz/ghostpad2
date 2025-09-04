import { useEffect, useState, useCallback, useMemo } from "react";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Settings } from "lucide-react";
import { ToolInfo } from "@/types";
import { ToolFileModal } from "./ToolFileModal";

interface ToolFile {
  name: string;
  tools: ToolInfo[];
  enabled_count: number;
  total_count: number;
  all_enabled: boolean;
  any_enabled: boolean;
}

export function ToolsSettings() {
  const [files, setFiles] = useState<ToolFile[]>([]);
  const [loading, setLoading] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [searchQuery, setSearchQuery] = useState<string>("");
  const [selectedFile, setSelectedFile] = useState<ToolFile | null>(null);

  const loadFiles = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await fetch("/api/tools/by-file");
      if (!res.ok) throw new Error(`Failed to load tool files (${res.status})`);
      const data = await res.json();
      setFiles(data.files || []);
    } catch (e: any) {
      console.error("Error loading tool files:", e);
      setError(e?.message ?? "Failed to load tool files");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadFiles();
  }, [loadFiles]);

  const toggleFileData = (
    file: ToolFile,
    selectedFilename: string,
    enabled: boolean
  ) => {
    if (file.name === selectedFilename) {
      const newEnabledCount = enabled ? file.total_count : 0;
      return {
        ...file,
        all_enabled: enabled,
        any_enabled: enabled,
        enabled_count: newEnabledCount,
        tools: file.tools.map((t) => ({ ...t, enabled })),
      };
    }
    return file;
  };

  const toggleFileTools = async (fileName: string, enabled: boolean) => {
    try {
      const res = await fetch(
        `/api/tools/file/${encodeURIComponent(fileName)}/toggle`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        }
      );

      if (!res.ok) throw new Error("Failed to toggle file tools");

      // Optimistically update the UI
      setFiles((prevFiles) => {
        const newFiles = prevFiles.map((f) =>
          toggleFileData(f, fileName, enabled)
        );

        // Update selected file if it's open
        if (selectedFile && selectedFile.name === fileName) {
          const updatedFile = newFiles.find((f) => f.name === fileName);
          if (updatedFile) {
            setSelectedFile(updatedFile);
          }
        }

        return newFiles;
      });

      // Notify listeners (e.g., feature hooks) that tools were updated
      window.dispatchEvent(new Event("toolsUpdated"));
    } catch (e) {
      console.error(e);
    }
  };

  const toggleToolData = (f: ToolFile, tool: ToolInfo, enabled: boolean) => {
    if (f.tools.some((t) => t.id === tool.id)) {
      const newTools = f.tools.map((t) =>
        t.id === tool.id ? { ...t, enabled } : t
      );
      const newEnabledCount = newTools.filter((t) => t.enabled).length;
      const newAllEnabled = newEnabledCount === f.total_count;
      const newAnyEnabled = newEnabledCount > 0;

      const updatedFile = {
        ...f,
        tools: newTools,
        enabled_count: newEnabledCount,
        all_enabled: newAllEnabled,
        any_enabled: newAnyEnabled,
      };

      // Update selected file if it's open
      if (selectedFile && selectedFile.name === f.name) {
        setSelectedFile(updatedFile);
      }

      return updatedFile;
    }
    return f;
  };

  const toggleTool = async (tool: ToolInfo, enabled: boolean) => {
    try {
      const res = await fetch(
        `/api/tools/${encodeURIComponent(tool.id)}/toggle`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ enabled }),
        }
      );
      if (!res.ok) throw new Error("Failed to toggle tool");

      // Optimistically update the UI
      setFiles((prevFiles) => {
        const newFiles = prevFiles.map((f) => toggleToolData(f, tool, enabled));
        return newFiles;
      });

      // Notify listeners (e.g., feature hooks) that tools were updated
      window.dispatchEvent(new Event("toolsUpdated"));
    } catch (e) {
      console.error(e);
    }
  };

  // Filter and sort files based on search query
  const filteredFiles = useMemo(() => {
    let result = files;

    // Apply search filter if query exists
    if (searchQuery.trim()) {
      const query = searchQuery.toLowerCase().trim();
      result = files.filter(
        (file) =>
          file.name.toLowerCase().includes(query) ||
          file.tools.some(
            (tool) =>
              tool.name.toLowerCase().includes(query) ||
              tool.description?.toLowerCase().includes(query)
          )
      );
    }

    // Sort alphabetically by file name
    return result.sort((a, b) => a.name.localeCompare(b.name));
  }, [files, searchQuery]);

  const totalTools = files.reduce((sum, file) => sum + file.enabled_count, 0);

  const getToggleLabel = (file: ToolFile) => {
    if (file.all_enabled) return "All enabled";
    return file.any_enabled ? "Partially enabled" : "All disabled";
  };

  return (
    <div className="space-y-4">
      {!loading && !error && files.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <Input
              placeholder="Search tool files..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="max-w-sm"
            />
          </div>

          <div className="text-sm text-muted-foreground">
            {totalTools} tools enabled
          </div>

          {searchQuery.trim() && (
            <div className="text-sm text-muted-foreground">
              Showing {filteredFiles.length} of {files.length} files
            </div>
          )}
        </div>
      )}

      {loading && (
        <div className="text-muted-foreground">Loading tool files...</div>
      )}
      {error && <div className="text-destructive">{error}</div>}
      {!loading && !error && files.length === 0 && (
        <div className="text-muted-foreground">No tool files found.</div>
      )}
      {!loading &&
        !error &&
        files.length > 0 &&
        filteredFiles.length === 0 &&
        searchQuery.trim() && (
          <div className="text-muted-foreground">
            No files match your search.
          </div>
        )}

      {!loading && !error && filteredFiles.length > 0 && (
        <div className="divide-y rounded-md border">
          {filteredFiles.map((file) => (
            <div key={file.name} className="p-4">
              <div className="space-y-3">
                {/* File header */}
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 max-w-3/4">
                    <span className="font-medium truncate">{file.name}.py</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFile(file)}
                    >
                      <Settings className="w-3 h-3" />
                    </Button>
                  </div>
                </div>

                {/* File-level toggle */}
                <div className="flex items-center justify-between gap-3">
                  <span className="text-sm text-muted-foreground">
                    {file.enabled_count}/{file.total_count}
                  </span>
                  <div className="flex items-center gap-2">
                    <Label htmlFor={`file-${file.name}`}>
                      {getToggleLabel(file)}
                    </Label>
                    <Switch
                      id={`file-${file.name}`}
                      checked={file.all_enabled}
                      onCheckedChange={(v) => toggleFileTools(file.name, v)}
                    />
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Tool file modal */}
      <ToolFileModal
        isOpen={!!selectedFile}
        onClose={() => setSelectedFile(null)}
        fileName={selectedFile?.name || ""}
        tools={selectedFile?.tools || []}
        onToggleTool={toggleTool}
        onToggleAllTools={(enabled) =>
          selectedFile
            ? toggleFileTools(selectedFile.name, enabled)
            : Promise.resolve()
        }
      />
    </div>
  );
}
