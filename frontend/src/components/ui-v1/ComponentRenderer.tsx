import React from "react";
import { HtmlRenderer } from "./components/HtmlRenderer";
import { TextInput } from "./components/TextInput";
import { TextareaInput } from "./components/TextareaInput";
import { UIButton } from "./components/UIButton";
import { ListDisplay } from "./components/ListDisplay";
import { TableDisplay, TableDisplayRef } from "./components/TableDisplay";
import { PersonaSelector } from "./components/PersonaSelector";
import { NumberInput } from "./components/NumberInput";
import { Modal } from "./components/Modal";
import { LibraryLoader } from "./components/LibraryLoader";
import { LibrarySaver } from "./components/LibrarySaver";
import { LibraryManager } from "./components/LibraryManager";
import { DataSource } from "@/types";

interface ComponentConfig {
  id: string;
  type: string;
  data_source?: DataSource;
  props?: Record<string, any>;
  actions?: Array<any>;
  children?: ComponentConfig[];
}

interface ComponentRendererProps {
  component: ComponentConfig;
  onAction?: (action: any) => Promise<void>;
  onValueChange?: (id: string, value: string) => void;
  getValueById?: (id: string) => string;
  getAllValues?: () => Record<string, string>;
  activePersonas?: { id: string; name: string }[];
  currentConversationId?: string | null;
}

export const ComponentRenderer = React.forwardRef<any, ComponentRendererProps>(
  (
    {
      component,
      onAction,
      onValueChange,
      getValueById,
      getAllValues,
      activePersonas,
      currentConversationId,
    },
    ref
  ) => {
    const { id, type, data_source, props, actions } = component;

    switch (type) {
      case "html_renderer":
        if (!data_source) {
          return <div>Error: html_renderer requires data_source</div>;
        }
        return <HtmlRenderer id={id} data_source={data_source} props={props} />;

      case "text_input":
        return (
          <TextInput
            id={id}
            props={{
              ...props,
              value: getValueById ? getValueById(id) : "",
            }}
            actions={actions}
            onValueChange={onValueChange}
            onAction={onAction}
          />
        );

      case "textarea_input":
        return (
          <TextareaInput
            id={id}
            props={{
              ...props,
              value: getValueById ? getValueById(id) : "",
            }}
            actions={actions}
            onValueChange={onValueChange}
            onAction={onAction}
          />
        );

      case "button":
        return (
          <UIButton
            id={id}
            props={props}
            actions={actions}
            onAction={onAction}
            getAllValues={getAllValues}
          />
        );

      case "list_display":
        if (!data_source) {
          return <div>Error: list_display requires data_source</div>;
        }
        return (
          <ListDisplay
            id={id}
            data_source={data_source}
            props={props}
            onAction={onAction}
            currentConversationId={currentConversationId}
          />
        );

      case "table_display": {
        // Create loadData function for persona properties
        const loadData =
          data_source?.type === "persona_properties"
            ? async () => {
                const { key, include_user } = data_source;
                if (!key) return {};

                const keysToFetch: string[] = [];

                // Add user key if requested
                if (include_user) {
                  keysToFetch.push(`${key}-user`);
                }

                // Add persona keys
                if (activePersonas) {
                  for (const persona of activePersonas) {
                    const normalized = persona.name
                      .trim()
                      .toLowerCase()
                      .split(/\s+/)
                      .join("-");
                    keysToFetch.push(`${key}-${normalized}`);
                  }
                }

                if (keysToFetch.length === 0) return {};

                // Fetch all keys at once
                const url = new URL("/api/kv/get", window.location.origin);
                url.searchParams.set("keys", keysToFetch.join(","));
                if (currentConversationId) {
                  url.searchParams.set("conversation_id", currentConversationId);
                }
                const response = await fetch(url.toString());
                const result = await response.json();

                const tableData: Record<string, any> = {};
                if (result.keys) {
                  // Add user data if requested
                  if (
                    include_user &&
                    result.keys[`${key}-user`] !== undefined
                  ) {
                    tableData["You"] = result.keys[`${key}-user`];
                  }

                  // Add persona data
                  if (activePersonas) {
                    for (const persona of activePersonas) {
                      const normalized = persona.name
                        .trim()
                        .toLowerCase()
                        .split(/\s+/)
                        .join("-");
                      const personaKey = `${key}-${normalized}`;
                      if (result.keys[personaKey] !== undefined) {
                        tableData[persona.name] = result.keys[personaKey];
                      }
                    }
                  }
                }

                return tableData;
              }
            : undefined;

        return (
          <TableDisplay
            ref={ref as React.Ref<TableDisplayRef>}
            loadData={loadData}
            props={props}
            value={getValueById ? { [id]: getValueById(id) } : undefined}
            onChange={(value) => onValueChange?.(id, JSON.stringify(value))}
          />
        );
      }

      case "persona_selector":
        return (
          <PersonaSelector
            id={id}
            props={props}
            value={getValueById ? getValueById(id) : ""}
            onChange={(value) => onValueChange?.(id, value)}
            personas={activePersonas || []}
          />
        );

      case "number_input":
        return (
          <NumberInput
            id={id}
            props={props}
            value={getValueById ? Number(getValueById(id)) || 0 : 0}
            onChange={(value) => onValueChange?.(id, String(value))}
          />
        );

      case "modal":
        return (
          <Modal
            id={id}
            props={props}
            onOpenChange={(open) => {
              // Modal open/close state should be managed by parent
              onValueChange?.(id, String(open));
            }}
          >
            {/* Modal content would be handled by child components */}
          </Modal>
        );

      case "library_loader":
        if (!data_source) {
          return <div>Error: library_loader requires data_source</div>;
        }
        return (
          <LibraryLoader
            id={id}
            data_source={data_source}
            props={props}
            onAction={onAction}
          />
        );

      case "library_saver":
        if (!data_source) {
          return <div>Error: library_saver requires data_source</div>;
        }
        return (
          <LibrarySaver
            id={id}
            data_source={data_source}
            props={props}
            getValueById={getValueById}
            onAction={onAction}
          />
        );

      case "library_manager":
        if (!data_source) {
          return <div>Error: library_manager requires data_source</div>;
        }
        return (
          <LibraryManager
            id={id}
            data_source={data_source}
            props={props}
            getValueById={getValueById}
            onValueChange={onValueChange}
          />
        );

      default:
        return (
          <div className="p-4 border border-dashed border-gray-300 rounded">
            <div className="text-sm text-muted-foreground">
              Unsupported component type: {type}
            </div>
            <div className="text-xs text-muted-foreground mt-1">
              Component ID: {id}
            </div>
          </div>
        );
    }
  }
);
