import React from "react";

interface WidgetGridProps {
  children: React.ReactNode;
  className?: string;
}

export function WidgetGrid({
  children,
  className = "",
}: Readonly<WidgetGridProps>) {
  return (
    <div
      className={`grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-3 ${className}`}
    >
      {children}
    </div>
  );
}
