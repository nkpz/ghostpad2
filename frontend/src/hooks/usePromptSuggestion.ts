import { useState, useCallback } from "react";

interface UsePromptSuggestionOptions {
  onSuggestionUpdate: (content: string) => void;
  onError?: (error: string) => void;
}

export function usePromptSuggestion({
  onSuggestionUpdate,
  onError,
}: UsePromptSuggestionOptions) {
  const [isGenerating, setIsGenerating] = useState(false);

  const generateSuggestion = useCallback(
    async (conversationId?: string) => {
      if (isGenerating) return;

      setIsGenerating(true);
      onSuggestionUpdate(""); // Clear existing content

      try {
        const response = await fetch("/api/chat/suggest-prompt", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            conversation_id: conversationId,
          }),
        });

        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }

        const reader = response.body?.getReader();
        if (!reader) throw new Error("No response body");

        const decoder = new TextDecoder();
        let accumulatedContent = "";

        while (true) {
          const { done, value } = await reader.read();
          if (done) break;

          const chunk = decoder.decode(value);
          const lines = chunk.split("\n");

          for (const line of lines) {
            if (line.startsWith("data: ")) {
              try {
                const data = JSON.parse(line.slice(6));

                if (data.type === "chunk") {
                  accumulatedContent += data.content;
                  onSuggestionUpdate(accumulatedContent);
                } else if (data.type === "complete") {
                  accumulatedContent = data.content || accumulatedContent;
                  onSuggestionUpdate(accumulatedContent);
                } else if (data.error) {
                  throw new Error(data.error);
                }
              } catch (e) {
                console.error("Error parsing suggestion data:", e);
                if (e instanceof Error) {
                  throw e;
                }
              }
            }
          }
        }
      } catch (err) {
        console.error("Failed to generate suggestion:", err);
        const errorMessage =
          err instanceof Error
            ? err.message
            : "Failed to generate prompt suggestion";
        if (onError) {
          onError(errorMessage);
        }
      } finally {
        setIsGenerating(false);
      }
    },
    [isGenerating, onSuggestionUpdate, onError]
  );

  return {
    isGenerating,
    generateSuggestion,
  };
}
