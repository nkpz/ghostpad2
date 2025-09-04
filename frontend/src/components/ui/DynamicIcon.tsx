import React, { useState, useEffect } from 'react';
import * as LucideIcons from 'lucide-react';

interface DynamicIconProps {
  name: string;
  className?: string;
  size?: number;
  fallback?: React.ComponentType<any>;
}

export function DynamicIcon({ name, className, size, fallback: Fallback = LucideIcons.HelpCircle }: Readonly<DynamicIconProps>) {
  const [IconComponent, setIconComponent] = useState<React.ComponentType<any> | null>(null);

  useEffect(() => {
    // Try to get the icon from lucide-react
    const icon = (LucideIcons as any)[name];
    if (icon) {
      setIconComponent(() => icon);
    } else {
      console.warn(`Icon "${name}" not found in lucide-react, using fallback`);
      setIconComponent(() => Fallback);
    }
  }, [name, Fallback]);

  if (!IconComponent) {
    return <Fallback className={className} size={size} />;
  }

  return <IconComponent className={className} size={size} />;
}