import { defineConfig } from '@tailwindcss/cli'

export default defineConfig({
  content: ["./templates/**/*.html"],
  theme: {
    colors: {
      // Custom brand colors
      primary: "#2060B9",
      "primary-dark": "#193966", 
      "primary-hover": "#1c55a4",
      "primary-active": "#184a90",
      "primary-disabled": "#9BB6DD",
      "dark-charcoal": "#111827", // 深色按鈕顏色
      // Custom semantic colors
      "custom-muted": "#5D6970",
      "custom-light-gray": "#F9F9F9", 
      "custom-border-light": "#D1D5DB",
      "custom-placeholder": "#949AA6",
      "custom-error": "#FF1F1F",
      "custom-bg-alt": "#E5E7EB",
      "custom-border-subtle": "#BEC1C6",
      // List view specific colors
      "list-title": "#374151",
      "list-bank": "#6b7280", 
      "list-highlight-bg": "#eff6ff",
      "list-rate": "#1d4ed8",
      "list-limit": "#6b7280",
      "list-divider": "#e5e7eb",
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
