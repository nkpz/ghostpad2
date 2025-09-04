import React from "react";
import { Card, CardContent } from "@/components/ui/card";

interface PercentWidgetProps {
  label: string;
  value: number;
  max_value?: number;
  kv_key?: string;
  onValueChange?: (v: number) => void;
  formatOptions?: {
    showValue?: boolean;
    colorScheme?: "default" | "health" | "custom";
  };
}

export function PercentWidget({
  label,
  value,
  max_value,
  onValueChange,
  formatOptions,
}: Readonly<PercentWidgetProps>) {
  const { showValue = true, colorScheme = "default" } = formatOptions || {};

  // Calculate percentage based on max_value if provided
  let percentValue;
  if (max_value && max_value > 0) {
    percentValue = Math.max(0, Math.min(100, ((value || 0) / max_value) * 100));
  } else {
    percentValue = Math.max(0, Math.min(100, value || 0));
  }

  const clampedValue = percentValue;

  // Determine color based on scheme
  const getColorClasses = (percent: number) => {
    if (colorScheme === "health") {
      if (percent >= 70) return "bg-green-500";
      if (percent >= 40) return "bg-yellow-500";
      return "bg-red-500";
    }
    return "bg-blue-500";
  };

  const barRef = React.useRef<HTMLDivElement | null>(null);

  const handleClick = (e: React.MouseEvent) => {
    const el = barRef.current;
    if (!el) return;
    const rect = el.getBoundingClientRect();
    const clickX = e.clientX - rect.left;
    const pct = Math.round((clickX / rect.width) * 100);
    const newVal = Math.max(0, Math.min(100, pct));
    if (onValueChange) onValueChange(newVal);
  };

  return (
    <Card className="h-20">
      <CardContent className="p-3 flex flex-col justify-center h-full">
        <div className="text-xs font-medium text-muted-foreground mb-1">
          {label}
        </div>
        <div className="flex items-center gap-2">
          <div
            ref={barRef}
            onClick={handleClick}
            className="flex-1 bg-muted rounded-full h-2 overflow-hidden cursor-pointer"
            role="slider"
            aria-valuemin={0}
            aria-valuemax={100}
            aria-valuenow={clampedValue}
            aria-label={label}
          >
            <div
              className={`h-full transition-all duration-150 ${getColorClasses(
                clampedValue
              )}`}
              style={{ width: `${clampedValue}%` }}
            />
          </div>
          {showValue && (
            <div
              className="text-sm font-semibold text-foreground min-w-[3rem] text-right cursor-pointer"
              onClick={(e) => {
                // clicking the numeric value should set by x position relative to the bar
                // forward the click to the bar element
                if (barRef.current) {
                  const rect = barRef.current.getBoundingClientRect();
                  const offsetX = rect.width * (clampedValue / 100);
                  const simulatedX =
                    rect.left + Math.max(0, Math.min(rect.width, offsetX));
                  // compute similar percentage as handleClick using simulatedX
                  const pct = Math.round(
                    ((simulatedX - rect.left) / rect.width) * 100
                  );
                  const newVal = Math.max(0, Math.min(100, pct));
                  if (onValueChange) onValueChange(newVal);
                }
                e.stopPropagation();
              }}
              title={`${Math.round(clampedValue)}%`}
            >
              {Math.round(clampedValue)}%
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
