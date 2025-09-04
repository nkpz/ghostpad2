import React from "react";

interface NumberInputProps {
  id?: string;
  props?: {
    placeholder?: string;
    disabled?: boolean;
    min?: number;
    max?: number;
    step?: number;
    width?: string;
  };
  value?: number;
  onChange?: (value: number) => void;
}

export function NumberInput({
  props,
  value,
  onChange,
}: Readonly<NumberInputProps>) {
  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const numValue = Number(e.target.value);
    onChange?.(numValue);
  };

  return (
    <input
      type="number"
      placeholder={props?.placeholder}
      value={value ?? ""}
      onChange={handleChange}
      disabled={props?.disabled}
      min={props?.min}
      max={props?.max}
      step={props?.step}
      className="rounded border p-2 bg-muted/30"
      style={{ width: props?.width }}
    />
  );
}
