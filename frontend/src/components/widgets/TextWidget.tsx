import React from 'react';
import { Card, CardContent } from '@/components/ui/card';

interface TextWidgetProps {
  label: string;
  value: string;
  kv_key?: string;
  onValueChange?: (v: string) => void;
  formatOptions?: {
    maxLength?: number;
    truncate?: boolean;
    prefix?: string;
    suffix?: string;
    color?: string;
  };
}

export function TextWidget({ label, value, onValueChange, formatOptions }: Readonly<TextWidgetProps>) {
  const { maxLength = 50, truncate = true, prefix = '', suffix = '', color } = formatOptions || {};
  const [editing, setEditing] = React.useState(false);
  const [editValue, setEditValue] = React.useState(value || '');
  const inputRef = React.useRef<HTMLInputElement | null>(null);

  React.useEffect(() => {
    setEditValue(value || '');
  }, [value]);

  React.useEffect(() => {
    if (editing && inputRef.current) {
      inputRef.current.focus();
      inputRef.current.select();
    }
  }, [editing]);

  const displayValue = truncate && editValue.length > maxLength
    ? `${editValue.substring(0, maxLength)}...`
    : editValue;
    
  const formattedValue = `${prefix}${displayValue}${suffix}`;
  
  const getColorClass = (colorName?: string) => {
    switch (colorName) {
      case 'green': return 'text-green-600';
      case 'red': return 'text-red-600';
      case 'blue': return 'text-blue-600';
      case 'yellow': return 'text-yellow-600';
      case 'purple': return 'text-purple-600';
      default: return 'text-foreground';
    }
  };

  const save = () => {
    setEditing(false);
    if (onValueChange && editValue !== value) {
      onValueChange(editValue);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      save();
    } else if (e.key === 'Escape') {
      setEditValue(value || '');
      setEditing(false);
    }
  };

  return (
    <Card className="h-20">
      <CardContent className="p-3 flex flex-col justify-center h-full space-y-1">
        <div className="text-xs font-medium text-muted-foreground mb-1">
          {label}
        </div>
        <div className={`text-sm font-semibold min-h-[1.25rem] leading-5 ${getColorClass(color)}`}>
          {editing ? (
            <input
              ref={inputRef}
              className="w-full bg-transparent outline-none"
              value={editValue}
              onChange={e => setEditValue(e.target.value)}
              onBlur={save}
              onKeyDown={handleKeyDown}
            />
          ) : (
            <div
              className="truncate cursor-text"
              onClick={() => setEditing(true)}
              title={formattedValue}
            >
              {formattedValue || '—'}
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
