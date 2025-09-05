import { useState, useEffect } from 'react'
import { Input } from "@/components/ui/input"

interface AutocompleteOption {
  id: string
  label: string
  sublabel?: string
}

interface AutocompleteInputProps {
  value: string
  onChange: (value: string) => void
  options: AutocompleteOption[]
  placeholder?: string
  id?: string
  className?: string
}

export function AutocompleteInput({
  value,
  onChange,
  options,
  placeholder = "Type or select an option...",
  id,
  className
}: Readonly<AutocompleteInputProps>) {
  const [isOpen, setIsOpen] = useState(false)
  const [filteredOptions, setFilteredOptions] = useState<AutocompleteOption[]>([])
  const [highlightedIndex, setHighlightedIndex] = useState(-1)

  useEffect(() => {
    filterOptions(value)
  }, [value, options])

  const filterOptions = (searchValue: string) => {
    if (!searchValue) {
      setFilteredOptions(options)
      setHighlightedIndex(-1)
      return
    }
    
    const filtered = options.filter(option =>
      option.label.toLowerCase().includes(searchValue.toLowerCase()) ||
      option.sublabel?.toLowerCase().includes(searchValue.toLowerCase())
    )
    setFilteredOptions(filtered)
    setHighlightedIndex(-1)
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (!isOpen || filteredOptions.length === 0) return

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev < filteredOptions.length - 1 ? prev + 1 : 0
        )
        break
      case 'ArrowUp':
        e.preventDefault()
        setHighlightedIndex(prev => 
          prev > 0 ? prev - 1 : filteredOptions.length - 1
        )
        break
      case 'Enter':
        e.preventDefault()
        if (highlightedIndex >= 0 && highlightedIndex < filteredOptions.length) {
          onChange(filteredOptions[highlightedIndex].label)
          setIsOpen(false)
        }
        break
      case 'Escape':
        e.preventDefault()
        setIsOpen(false)
        setHighlightedIndex(-1)
        break
    }
  }

  const handleSelect = (option: AutocompleteOption) => {
    onChange(option.label)
    setIsOpen(false)
    setHighlightedIndex(-1)
  }

  return (
    <div className={`relative ${className}`}>
      <Input
        id={id}
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => {
          onChange(e.target.value)
          setIsOpen(true)
        }}
        onFocus={() => setIsOpen(true)}
        onBlur={() => setTimeout(() => {
          setIsOpen(false)
          setHighlightedIndex(-1)
        }, 200)}
        onKeyDown={handleKeyDown}
      />
      {isOpen && filteredOptions.length > 0 && (
        <div className="absolute z-50 w-full bg-background border border-border rounded-md shadow-lg max-h-60 overflow-auto">
          {filteredOptions.map((option, index) => (
            <div
              key={option.id}
              className={`px-3 py-2 cursor-pointer border-b border-border last:border-b-0 ${
                index === highlightedIndex 
                  ? 'bg-accent text-accent-foreground' 
                  : 'hover:bg-accent/50'
              }`}
              onMouseDown={(e) => {
                e.preventDefault()
                handleSelect(option)
              }}
              onMouseEnter={() => setHighlightedIndex(index)}
            >
              <div className="font-medium text-sm text-foreground">{option.label}</div>
              {option.sublabel && (
                <div className="text-xs text-muted-foreground">
                  {option.sublabel}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
      {isOpen && filteredOptions.length === 0 && options.length > 0 && (
        <div className="absolute z-50 w-full bg-background border border-border rounded-md shadow-lg px-3 py-2">
          <div className="text-sm text-muted-foreground">No options found</div>
        </div>
      )}
      {isOpen && options.length === 0 && (
        <div className="absolute z-50 w-full bg-background border border-border rounded-md shadow-lg px-3 py-2">
          <div className="text-sm text-muted-foreground">No options available</div>
        </div>
      )}
    </div>
  )
}