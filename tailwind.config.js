/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./book_shop_here/templates/**/*.html",
    "./templates/**/*.html",
    "./assets/**/*.{js,ts}"
  ],
  // Safelist small set of utilities used by form select chevron wrappers so
  // they are not purged. This prevents oversized inline SVG chevrons and keeps
  // consistent form rendering across pages.
  safelist: [
    'relative',
    'absolute',
    'inset-y-0',
    'right-0',
    'flex',
    'items-center',
    'px-2',
    'pointer-events-none',
    'h-4',
    'w-4',
    'appearance-none',
    'pr-8',
    'fill-current',
    'text-gray-700'
  ],
  theme: {
    extend: {},
  },
  plugins: [],
};
