
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
        'muted': '#5D6970',
        'light-gray': '#F9F9F9',
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
