import { memo, useMemo, ReactNode } from 'react';
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Pencil, Check, X, RotateCcw, Trash2 } from "lucide-react";
import ReactMarkdown, { Components } from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { ChatMessage } from "@/types";

interface MessageItemProps {
  message: ChatMessage;
  editingMessageId: number | null;
  editingMessageContent: string;
  regeneratingMessageId: number | null;
  setEditingMessageContent: (content: string) => void;
  startEditingMessage: (message: ChatMessage) => void;
  cancelEditingMessage: () => void;
  saveEditedMessage: () => void;
  regenerateMessage: (message: ChatMessage) => void;
  deleteMessage: (message: ChatMessage) => void;
  deleteMessageAndAfter: (message: ChatMessage) => void;
}

export const MessageItem = memo(function MessageItem({
  message,
  editingMessageId,
  editingMessageContent,
  regeneratingMessageId,
  setEditingMessageContent,
  startEditingMessage,
  cancelEditingMessage,
  saveEditedMessage,
  regenerateMessage,
  deleteMessage,
  deleteMessageAndAfter,
}: MessageItemProps) {
  const getMessageClass = (role: string): string => {
    const baseClass = "max-w-[85%] sm:max-w-xs lg:max-w-md w-full px-4 py-2 rounded-2xl";
    
    switch (role) {
      case "user":
        return `${baseClass} bg-blue-500 text-white rounded-br-md`;
      case "system":
        return `${baseClass} bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200 border border-yellow-300 dark:border-yellow-700`;
      default:
        return `${baseClass} bg-muted text-foreground rounded-bl-md`;
    }
  };

  const markdownComponents = useMemo((): Components => ({
    code({ node, className, children, style, ref, ...props }) {
      const match = /language-(\w+)/.exec(className || '');
      return match ? (
        <SyntaxHighlighter
          language={match[1]}
          PreTag="div"
          className="rounded-md"
          style={tomorrow}
          {...props}
        >
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={`${className || ''} bg-muted px-1 py-0.5 rounded text-xs`} {...props}>
          {children}
        </code>
      );
    },
    p: ({ children }: { children?: ReactNode }) => <p className="mb-2 last:mb-0">{children}</p>,
    ul: ({ children }: { children?: ReactNode }) => <ul className="list-disc list-inside mb-2">{children}</ul>,
    ol: ({ children }: { children?: ReactNode }) => <ol className="list-decimal list-inside mb-2">{children}</ol>,
    li: ({ children }: { children?: ReactNode }) => <li className="mb-1">{children}</li>,
    h1: ({ children }: { children?: ReactNode }) => <h1 className="text-lg font-bold mb-2">{children}</h1>,
    h2: ({ children }: { children?: ReactNode }) => <h2 className="text-base font-bold mb-2">{children}</h2>,
    h3: ({ children }: { children?: ReactNode }) => <h3 className="text-sm font-bold mb-2">{children}</h3>,
    strong: ({ children }: { children?: ReactNode }) => <strong className="font-bold">{children}</strong>,
    em: ({ children }: { children?: ReactNode }) => <em className="italic">{children}</em>,
  }), []);
  return (
    <div className="group flex">
      <div
        className={`relative flex items-start gap-1 w-full ${
          message.role === "user" ? "justify-between" : "justify-start"
        }`}
      >
        <div className="w-16 flex flex-col items-center justify-start mt-1">
          {regeneratingMessageId === message.id ? (
            <div className="h-6 w-6 flex items-center justify-center">
              <RotateCcw className="h-3 w-3 animate-spin text-muted-foreground" />
            </div>
          ) : (
            <div className="flex flex-col items-center gap-1">
              {editingMessageId !== message.id && (
                <>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => startEditingMessage(message)}
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 hover:bg-muted/50"
                    title="Edit message"
                  >
                    <Pencil className="h-3 w-3" />
                  </Button>

                  {message.role === "assistant" && (
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => regenerateMessage(message)}
                      className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 hover:bg-muted/50"
                      title="Regenerate response"
                    >
                      <RotateCcw className="h-3 w-3" />
                    </Button>
                  )}

                  <Button
                    variant="ghost"
                    size="sm"
                    onMouseDown={(e) => {
                      if (e.shiftKey) {
                        e.preventDefault();
                        deleteMessageAndAfter(message);
                      } else {
                        deleteMessage(message);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 transition-opacity h-6 w-6 p-0 hover:bg-destructive/20 hover:text-destructive"
                    title="Delete message (Shift+click to delete this and all subsequent messages)"
                  >
                    <Trash2 className="h-3 w-3" />
                  </Button>
                </>
              )}
            </div>
          )}
        </div>

        <div className={getMessageClass(message.role)}>
          {editingMessageId === message.id ? (
            <div className="space-y-2">
              <Textarea
                rows={5}
                value={editingMessageContent}
                onChange={(e) => setEditingMessageContent(e.target.value)}
                className="min-h-16 text-sm resize-none"
                autoFocus
              />
              <div className="flex gap-2 justify-end">
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={cancelEditingMessage}
                  className="h-6 px-2"
                >
                  <X className="h-3 w-3 mr-1" />
                  Cancel
                </Button>
                <Button
                  variant="default"
                  size="sm"
                  onClick={saveEditedMessage}
                  className="h-6 px-2"
                >
                  <Check className="h-3 w-3 mr-1" />
                  Save
                </Button>
              </div>
            </div>
          ) : (
            <div className="text-sm prose prose-sm max-w-none prose-invert">
              {message.content.trim() ? (
                <ReactMarkdown components={markdownComponents}>
                  {message.content.trim()}
                </ReactMarkdown>
              ) : (
                <div className="flex items-center justify-center py-2">
                  <div className="loading-dots">
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                    <div className="loading-dot"></div>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
});
