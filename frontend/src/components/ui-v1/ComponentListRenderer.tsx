import { useState, useCallback, useEffect, useRef } from "react";
import { ComponentRenderer } from "./ComponentRenderer";

interface ComponentListRendererProps {
  components: Array<any>;
  activePersonas?: { id: string; name: string }[];
  currentConversationId?: string | null;
  refreshMessages?: (conversationId: string) => Promise<void>;
}

export function ComponentListRenderer({
  components,
  activePersonas,
  currentConversationId,
  refreshMessages,
}: Readonly<ComponentListRendererProps>) {
  // Initialize values for persona selectors with first persona
  const getInitialValues = () => {
    const initial: Record<string, string> = {};
    components.forEach((component) => {
      if (
        component.type === "persona_selector" &&
        activePersonas &&
        activePersonas.length > 0
      ) {
        initial[component.id] = activePersonas[0].name;
      }
    });
    return initial;
  };

  // Centralized state for all components by their ID
  const [componentValues, setComponentValues] =
    useState<Record<string, string>>(getInitialValues);
  // Refs for components that support imperative actions
  const componentRefs = useRef<Record<string, any>>({});

  // Load initial values from data sources
  useEffect(() => {
    const loadInitialValues = async () => {
      // Collect all KV keys that need to be loaded
      const kvKeys: string[] = [];
      const componentKeyMap: Record<string, string> = {}; // componentId -> kvKey

      for (const component of components) {
        if (
          component.data_source &&
          component.data_source.type === "kv_store" &&
          component.data_source.key
        ) {
          const kvKey = component.data_source.key.replace(
            "{conversation_id}",
            currentConversationId
          );
          kvKeys.push(kvKey);
          componentKeyMap[component.id] = kvKey;
        }
      }

      if (kvKeys.length === 0) return;

      try {
        // Batch fetch all KV values
        const response = await fetch(
          `/api/kv/get?keys=${encodeURIComponent(kvKeys.join(","))}`
        );
        const data = await response.json();

        if (data.keys) {
          const initialValues: Record<string, string> = {};

          // Map KV values back to component IDs
          Object.entries(componentKeyMap).forEach(([componentId, kvKey]) => {
            const value = data.keys[kvKey];
            if (value !== null && value !== undefined) {
              initialValues[componentId] = String(value);
            }
          });

          if (Object.keys(initialValues).length > 0) {
            setComponentValues(initialValues);
          }
        }
      } catch (error) {
        console.error("Failed to load initial values:", error);
      }
    };

    loadInitialValues();
  }, [components]);

  const handleValueChange = useCallback((id: string, value: string) => {
    setComponentValues((prev) => ({ ...prev, [id]: value }));
  }, []);

  const getValueById = useCallback(
    (id: string) => {
      return componentValues[id] || "";
    },
    [componentValues]
  );

  const getAllValues = useCallback(() => {
    return componentValues;
  }, [componentValues]);

  const handleAction = useCallback(
    async (action: any) => {
      // Handle library load action from LibraryLoader component
      if (action.type === "library_load") {
        // Update the target component (e.g., textarea) with loaded content
        if (action.target_component_id && action.content) {
          setComponentValues((prev) => ({
            ...prev,
            [action.target_component_id]: action.content,
          }));
        }
        return;
      }

      // Handle library save success action
      if (action.type === "library_save_success") {
        return;
      }

      // Handle text input submit by finding the target button
      if (
        action.type === "submit" &&
        action.trigger === "enter" &&
        action.target
      ) {
        const targetButton = components.find((c) => c.id === action.target);
        if (targetButton?.actions?.length > 0) {
          const buttonAction = targetButton.actions[0];
          return handleAction(buttonAction);
        }
      }

      if (action.type === "tool_submit") {
        try {
          // Collect parameters from action.params, replacing any component ID references
          const resolvedParams = { ...action.params };

          // Replace any parameter values that reference component IDs with actual values
          Object.keys(resolvedParams).forEach((key) => {
            const paramValue = resolvedParams[key];
            if (
              typeof paramValue === "string" &&
              componentValues.hasOwnProperty(paramValue)
            ) {
              resolvedParams[key] = componentValues[paramValue];
            }
          });

          // Add conversation_id to resolved params
          const finalParams = {
            ...resolvedParams,
            conversation_id: currentConversationId,
          };

          const response = await fetch("/api/tool_submit", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              handler: action.target,
              params: finalParams,
            }),
          });

          if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
          }

          const result = await response.json();

          // Handle UI updates based on result
          const handlerResult = result.result || result;
          if (result.success && Array.isArray(handlerResult.clear_inputs)) {
            handlerResult.clear_inputs.forEach((inputId: string) => {
              setComponentValues((prev) => ({ ...prev, [inputId]: "" }));
            });
          }

          // Handle component refresh
          if (
            result.success &&
            Array.isArray(handlerResult.refresh_components)
          ) {
            handlerResult.refresh_components.forEach((componentId: string) => {
              const componentRef = componentRefs.current[componentId];
              componentRef?.refresh();
            });
          }

          // Refresh messages if we have a conversation and refresh function
          if (result.success && currentConversationId && refreshMessages) {
            await refreshMessages(currentConversationId);
          }
        } catch (error) {
          console.error("Tool submit error:", error);
          alert(
            `Error: ${error instanceof Error ? error.message : "Unknown error"}`
          );
        }
      }
    },
    [componentValues]
  );

  return (
    <div className="space-y-4">
      {components.map((component, index) => (
        <ComponentRenderer
          key={component.id || index}
          component={component}
          onAction={(action) => handleAction(action)}
          onValueChange={handleValueChange}
          getValueById={getValueById}
          getAllValues={getAllValues}
          activePersonas={activePersonas}
          ref={(ref) => {
            if (component.id && ref) {
              componentRefs.current[component.id] = ref;
            }
          }}
        />
      ))}
    </div>
  );
}
