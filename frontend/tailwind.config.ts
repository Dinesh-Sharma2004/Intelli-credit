import type { Config } from 'tailwindcss'

const config: Config = {
  darkMode: 'class',
  content: [
    './src/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './src/components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/app/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  theme: {
    extend: {
      colors: {
        'brand-blue': '#0066CC',
        'brand-dark': '#001a40',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'slate-dark': '#1f2937',
      },
      gradient: {
        'brand': 'linear-gradient(135deg, #0066CC 0%, #0052a3 100%)',
      },
    },
  },
  plugins: [],
}
export default config
