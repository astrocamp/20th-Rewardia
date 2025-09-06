import { defineConfig } from '@tailwindcss/cli'

export default defineConfig({
  content: ["./templates/**/*.html"],
  plugins: [
    require("daisyui")
  ],
  daisyui: {
    themes: false,
    darkTheme: "light",
  },
};
