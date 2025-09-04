import * as React from "react"

import { cn } from "@/utils/cn"

const Slider = React.forwardRef<
  HTMLInputElement,
  React.ComponentProps<"input"> & {
    min?: number
    max?: number
    step?: number
    value?: number
  }
>(({ className, min = 0, max = 100, step = 1, value = 0, ...props }, ref) => {
  return (
    <div className="relative flex w-full touch-none select-none items-center">
      <input
        type="range"
        min={min}
        max={max}
        step={step}
        value={value}
        className={cn("flex-1 appearance-none cursor-pointer", className)}
        ref={ref}
        {...props}
      />

      <style>{`
        /* Ensure the native appearance is removed so custom styling works */
        input[type="range"] {
          -webkit-appearance: none;
          appearance: none;
          background: transparent;
          width: 100%;
          height: 18px;
        }

        /* Webkit track */
        input[type="range"]::-webkit-slider-runnable-track {
          height: 8px;
          border-radius: 9999px;
          background: #e5e7eb;
        }

        /* Webkit thumb */
        input[type="range"]::-webkit-slider-thumb {
          -webkit-appearance: none;
          appearance: none;
          height: 18px;
          width: 18px;
          border-radius: 50%;
          background: #fff;
          border: 3px solid #0ea5ff;
          box-shadow: 0 1px 3px rgba(0,0,0,0.15);
          margin-top: -5px;
          cursor: pointer;
        }

        /* Firefox track */
        input[type="range"]::-moz-range-track {
          height: 8px;
          border-radius: 9999px;
          background: #e5e7eb;
        }

        /* Firefox thumb */
        input[type="range"]::-moz-range-thumb {
          height: 18px;
          width: 18px;
          border-radius: 50%;
          background: #fff;
          border: 3px solid #0ea5ff;
          box-shadow: 0 1px 3px rgba(0,0,0,0.15);
          cursor: pointer;
        }
      `}</style>
    </div>
  )
})

Slider.displayName = "Slider"

export { Slider }

