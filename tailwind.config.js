
/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    './templates/**/*.html',
  ],
  theme: {
    extend: {
      colors: {
        'primary': '#2060B9',
        'primary-dark': '#193966',
        'primary-hover': '#1c55a4',
        'primary-active': '#184a90',
        'primary-disabled': '#9BB6DD',
        'muted': '#5D6970',
        'light-gray': '#F9F9F9',
        'dark-gray': '#111827',
        'border-light': '#D1D5DB',
        'placeholder-gray': '#949AA6',
        'error-red': '#FF1F1F',
        'bg-light-alt': '#E5E7EB',
        'border-subtle': '#BEC1C6',
      },
      fontFamily: {
        'kulim-park': ['"Kulim Park"', 'sans-serif'],
        'inter': ['"Inter"', 'sans-serif'],
      },
    },
  },
  plugins: [
    require('daisyui'),
  ],
  daisyui: {
    themes: false, // Disable default themes if we are using our own
    darkTheme: "light", // set light as default to avoid auto dark mode
  },
}
