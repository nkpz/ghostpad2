import React from "react";

interface PersonaSelectorProps {
  id?: string;
  props?: {
    placeholder?: string;
    disabled?: boolean;
  };
  value?: string;
  onChange?: (value: string) => void;
  personas?: Array<{ id: string; name: string }>;
}

export function PersonaSelector({
  props,
  value,
  onChange,
  personas = [],
}: Readonly<PersonaSelectorProps>) {
  const handleChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    onChange?.(e.target.value);
  };

  // Use first persona as fallback if no value is set
  const effectiveValue = value || (personas.length > 0 ? personas[0].name : "");

  return (
    <select
      value={effectiveValue}
      onChange={handleChange}
      disabled={props?.disabled}
      className="rounded border p-2 bg-muted/30 flex-1 min-w-0"
    >
      {personas.map((persona) => (
        <option key={persona.id} value={persona.name}>
          {persona.name}
        </option>
      ))}
    </select>
  );
}
