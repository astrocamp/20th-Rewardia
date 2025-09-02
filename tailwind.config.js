import { defineConfig } from '@tailwindcss/cli'

export default defineConfig({
  content: ["./templates/**/*.html"],
  theme: {
    colors: {
      primary: "#2060B9",
      "primary-dark": "#193966",
      "primary-hover": "#1c55a4",
      "primary-active": "#184a90",
      "primary-disabled": "#9BB6DD",
      muted: "#5D6970",
      "light-gray": "#F9F9F9",
      "dark-gray": "#111827",
      "border-light": "#D1D5DB",
      "placeholder-gray": "#949AA6",
      "error-red": "#FF1F1F",
      "bg-light-alt": "#E5E7EB",
      "border-subtle": "#BEC1C6",
      // Standard colors
      black: "#000000",
      white: "#ffffff",
      gray: {
        50: "#f9fafb",
        100: "#f3f4f6",
        200: "#e5e7eb",
        300: "#d1d5db",
        400: "#9ca3af",
        500: "#6b7280",
        600: "#4b5563",
        700: "#374151",
        800: "#1f2937",
        900: "#111827"
      },
      blue: {
        50: "#eff6ff",
        100: "#dbeafe",
        200: "#bfdbfe",
        300: "#93c5fd",
        400: "#60a5fa",
        500: "#3b82f6",
        600: "#2563eb",
        700: "#1d4ed8",
        800: "#1e40af",
        900: "#1e3a8a"
      },
      cyan: {
        500: "#06b6d4",
        600: "#0891b2"
      }
    },
    fontFamily: {
      "kulim-park": ['"Kulim Park"', "sans-serif"],
      inter: ['"Inter"', "sans-serif"],
    },
    lineHeight: {
      "tight-custom": "0.98",
      "normal-custom": "1.15",
      "relaxed-custom": "1.21",
    },
  },
})
