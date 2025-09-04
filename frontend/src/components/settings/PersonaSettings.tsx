import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Persona } from "@/types";
import { Button } from "@/components/ui/button";
import { Pencil, Plus, Minus, Sparkles, Trash2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
  DialogDescription,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { useState } from "react";
import PromptEditModal from "@/components/settings/PromptEditModal";
import { PersonaDeleteDialog } from "@/components/settings/PersonaDeleteDialog";

interface PersonaSettingsProps {
  personas: Persona[];
  currentConversation?: any;
  activePersonas?: Persona[];
  addPersonaToConversation?: (
    conversationId: string,
    personaId: string
  ) => void;
  removePersonaFromConversation?: (
    conversationId: string,
    personaId: string
  ) => void;
}

interface PersonaItemProps {
  persona: Persona;
  isAttached: boolean;
  currentConversation?: any;
  onEdit: (persona: Persona) => void;
  onDelete: (persona: Persona) => void;
  addPersonaToConversation?: (
    conversationId: string,
    personaId: string
  ) => void;
  removePersonaFromConversation?: (
    conversationId: string,
    personaId: string
  ) => void;
}

function PersonaItem({
  persona,
  isAttached,
  currentConversation,
  onEdit,
  onDelete,
  addPersonaToConversation,
  removePersonaFromConversation,
}: Readonly<PersonaItemProps>) {
  return (
    <div
      key={persona.id}
      className="p-3 rounded-lg border bg-card hover:shadow-sm transition-all"
    >
      <div className="flex items-center gap-3">
        <Avatar className={`h-10 w-10 ${persona.color}`}>
          <AvatarFallback className="text-white font-medium text-lg">
            {persona.avatar}
          </AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between gap-4">
            <div className="font-medium text-sm truncate">{persona.name}</div>
          </div>
          <div className="text-xs text-muted-foreground mt-1 line-clamp-3">
            {persona.description}
          </div>
          <div className="flex items-center gap-2 justify-end pt-1">
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onDelete(persona)}
              aria-label={`Delete ${persona.name}`}
            >
              <Trash2 className="h-4 w-4" />
            </Button>
            <Button
              size="sm"
              variant="ghost"
              onClick={() => onEdit(persona)}
              aria-label={`Edit ${persona.name}`}
            >
              <Pencil className="h-4 w-4" />
            </Button>
            {currentConversation && isAttached ? (
              <Button
                size="sm"
                variant="ghost"
                onClick={() =>
                  removePersonaFromConversation?.(
                    currentConversation.id,
                    persona.id
                  )
                }
                aria-label={`Remove ${persona.name}`}
              >
                <Minus className="h-4 w-4" />
              </Button>
            ) : null}
            {currentConversation && !isAttached ? (
              <Button
                size="sm"
                variant="ghost"
                onClick={() =>
                  addPersonaToConversation?.(currentConversation.id, persona.id)
                }
                aria-label={`Add ${persona.name}`}
              >
                <Plus className="h-4 w-4" />
              </Button>
            ) : null}
          </div>{" "}
        </div>
      </div>
    </div>
  );
}

export function PersonaSettings({
  personas,
  currentConversation,
  activePersonas = [],
  addPersonaToConversation,
  removePersonaFromConversation,
}: Readonly<PersonaSettingsProps>) {
  const [isOpen, setIsOpen] = useState(false);
  const [editing, setEditing] = useState<Partial<Persona> | null>(null);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [avatarUrl, setAvatarUrl] = useState("");
  const [isDescEditOpen, setIsDescEditOpen] = useState(false);
  const [isDeleteOpen, setIsDeleteOpen] = useState(false);
  const [personaToDelete, setPersonaToDelete] = useState<Persona | null>(null);

  const openCreate = () => {
    setEditing(null);
    setName("");
    setDescription("");
    setAvatarUrl("");
    setIsOpen(true);
  };

  const openEdit = (p: Persona) => {
    setEditing(p);
    setName(p.name || "");
    setDescription(p.description || "");
    setAvatarUrl((p as any).avatar_url || "");
    setIsOpen(true);
  };

  const handleSave = async () => {
    try {
      if (editing?.id) {
        // Update
        await fetch(`/api/personas/${editing.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, description, avatar_url: avatarUrl }),
        });
      } else {
        // Create
        await fetch("/api/personas", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ name, description, avatar_url: avatarUrl }),
        });
      }

      // Notify app to refresh personas
      window.dispatchEvent(new CustomEvent("personasUpdated"));
      setIsOpen(false);
    } catch (err) {
      console.error("Failed to save persona", err);
    }
  };

  const openDeleteDialog = (persona: Persona) => {
    setPersonaToDelete(persona);
    setIsDeleteOpen(true);
  };

  const handleDeleteConfirm = async (deleteConversations: boolean) => {
    if (!personaToDelete) return;

    try {
      const params = new URLSearchParams();
      if (deleteConversations) {
        params.append("delete_conversations", "true");
      }

      const url = `/api/personas/${personaToDelete.id}${
        params.toString() ? `?${params.toString()}` : ""
      }`;

      await fetch(url, {
        method: "DELETE",
      });

      // Notify app to refresh personas
      window.dispatchEvent(new CustomEvent("personasUpdated"));

      // If conversations were deleted, also refresh conversations list
      if (deleteConversations) {
        window.dispatchEvent(new CustomEvent("conversationsUpdated"));
      }

      setIsDeleteOpen(false);
      setPersonaToDelete(null);
    } catch (err) {
      console.error("Failed to delete persona", err);
    }
  };

  const handleDeleteCancel = () => {
    setIsDeleteOpen(false);
    setPersonaToDelete(null);
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h3 className="text-sm font-medium mb-3 text-primary">Personas</h3>
        <Button size="sm" onClick={openCreate}>
          New Persona
        </Button>
      </div>

      {/* Active Personas Section: show personas attached to the current conversation */}
      <div>
        <h4 className="text-sm font-medium mb-3 text-primary">
          Active Personas
        </h4>
        <div className="space-y-2">
          {(activePersonas || []).map((persona) => (
            <PersonaItem
              key={persona.id}
              persona={persona}
              isAttached={true}
              currentConversation={currentConversation}
              onEdit={openEdit}
              onDelete={openDeleteDialog}
              addPersonaToConversation={addPersonaToConversation}
              removePersonaFromConversation={removePersonaFromConversation}
            />
          ))}
        </div>
      </div>

      {/* Inactive Personas Section */}
      <div>
        <h4 className="text-sm font-medium mb-3 text-muted-foreground">
          Available Personas
        </h4>
        <div className="grid grid-cols-1 gap-3">
          {personas
            .filter((p) => !(activePersonas || []).some((ap) => ap.id === p.id))
            .map((persona) => (
              <PersonaItem
                key={persona.id}
                persona={persona}
                isAttached={false}
                currentConversation={currentConversation}
                onEdit={openEdit}
                onDelete={openDeleteDialog}
                addPersonaToConversation={addPersonaToConversation}
                removePersonaFromConversation={removePersonaFromConversation}
              />
            ))}
        </div>
      </div>

      {/* Dialog for create/edit */}
      <Dialog open={isOpen} onOpenChange={(open) => setIsOpen(open)}>
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>
              {editing ? "Edit Persona" : "New Persona"}
            </DialogTitle>
            <DialogDescription>
              {editing ? "Edit persona details" : "Create a new persona"}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4">
            <div>
              <label htmlFor="name-input" className="text-xs block mb-1">Name</label>
              <Input id="name-input" value={name} onChange={(e) => setName(e.target.value)} />
            </div>
            <div>
              <div className="flex items-center justify-between mb-1">
                <label htmlFor="description-textarea" className="text-xs">Description</label>
                <Button
                  size="sm"
                  variant="ghost"
                  onClick={() => setIsDescEditOpen(true)}
                  aria-label="AI edit description"
                >
                  <Sparkles className="h-4 w-4" />
                  <span className="sr-only">AI edit</span>
                </Button>
              </div>
              <Textarea
                id="description-textarea"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
              />
            </div>
            <div>
              <label className="text-xs block mb-1">Avatar URL</label>
              <Input
                value={avatarUrl}
                onChange={(e) => setAvatarUrl(e.target.value)}
              />
            </div>
          </div>

          <DialogFooter>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setIsOpen(false)}
            >
              Cancel
            </Button>
            <Button size="sm" onClick={handleSave}>
              {editing ? "Save" : "Create"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* AI Edit Modal for persona description */}
      <PromptEditModal
        open={isDescEditOpen}
        onOpenChange={setIsDescEditOpen}
        title={
          editing
            ? `Edit "${editing.name}" Description`
            : "Edit Persona Description"
        }
        baselineText={description}
        onSave={(edited) => setDescription(edited)}
      />

      {/* Delete Confirmation Modal */}
      <PersonaDeleteDialog
        isOpen={isDeleteOpen}
        onOpenChange={setIsDeleteOpen}
        onConfirm={handleDeleteConfirm}
        onCancel={handleDeleteCancel}
        persona={personaToDelete}
      />
    </div>
  );
}
