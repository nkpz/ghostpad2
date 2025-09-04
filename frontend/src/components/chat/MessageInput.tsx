import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { WandSparkles } from "lucide-react";
import { useEffect, useRef, memo, useState } from "react";

interface MessageInputProps {
  newMessage: string;
  isLoading: boolean;
  isStreaming?: boolean;
  isUserTurn?: boolean;
  handleSendMessage: (messageContent?: string) => void;
  handleStopGeneration?: () => void;
  handleSuggestPrompt?: () => void;
  isGeneratingSuggestion?: boolean;
}

export const MessageInput = memo(function MessageInput({
  newMessage,
  isLoading,
  isStreaming = false,
  isUserTurn = false,
  handleSendMessage,
  handleStopGeneration,
  handleSuggestPrompt,
  isGeneratingSuggestion = false,
}: MessageInputProps) {
  const [localMessage, setLocalMessage] = useState<string>(newMessage);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    setLocalMessage(newMessage);
  }, [newMessage]);

  const autoResize = () => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";

    const styles = window.getComputedStyle(el);
    const lineHeight = parseFloat(styles.lineHeight || "0");
    const paddingY =
      parseFloat(styles.paddingTop || "0") + parseFloat(styles.paddingBottom || "0");
    const borderY =
      parseFloat(styles.borderTopWidth || "0") +
      parseFloat(styles.borderBottomWidth || "0");

    const maxRows = 4;
    const maxHeight = lineHeight * maxRows + paddingY + borderY;
    const nextHeight = Math.min(el.scrollHeight, maxHeight);

    el.style.height = `${nextHeight}px`;
    el.style.overflowY = el.scrollHeight > maxHeight ? "auto" : "hidden";
  };

  useEffect(() => {
    autoResize();
  }, [localMessage]);

  const handleLocalSendMessage = () => {
    if ((localMessage.trim() || isUserTurn) && !isLoading) {
      const messageContent = localMessage;
      setLocalMessage("");
      handleSendMessage(messageContent);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault(); // Prevent default newline behavior
      handleLocalSendMessage();
    }
  };

  return (
    <div className="flex-shrink-0 p-4 pb-0 border-t">
      <div className="flex gap-2 items-end">
        <Button
          variant="ghost"
          size="icon"
          onClick={handleSuggestPrompt}
          disabled={isLoading || isStreaming || isGeneratingSuggestion}
          className="h-[44px] w-[44px] border-0 p-0 hover:bg-muted"
          title="Generate prompt suggestion"
        >
          <WandSparkles className="h-4 w-4" />
        </Button>
        <Textarea
          ref={textareaRef}
          value={localMessage}
          onChange={(e) => {
            setLocalMessage(e.target.value);
          }}
          onKeyDown={handleKeyDown}
          placeholder="Type your message... (Shift+Enter for new line)"
          className="flex-1 resize-none min-h-[44px] rounded-lg overflow-hidden"
          rows={1}
          disabled={isGeneratingSuggestion}
        />
        <Button
          onClick={isStreaming ? handleStopGeneration : handleLocalSendMessage}
          disabled={!isStreaming && ((!localMessage.trim() && !isUserTurn) || isLoading || isGeneratingSuggestion)}
          className="rounded-lg px-6"
        >
          {isStreaming ? "Stop" : "Send"}
        </Button>
      </div>
    </div>
  );
});
