/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx,ts,tsx}'],
  theme: {
    extend: {
      colors: {
        bg:        '#111315',
        surface:   '#1A1D21',
        card:      '#1A1D21',
        border:    '#2D3139',
        dim:       '#252A32',
        accent:    '#10B981',
        danger:    '#EF4444',
        warn:      '#F59E0B',
        success:   '#10B981',
        muted:     '#9CA3AF',
        subtle:    '#6B7280',
        ink:       '#F3F4F6',
        emerald: {
          950: '#064E3B',
          600: '#10B981',
          500: '#34D399',
        },
        cyan: {
          500: '#06B6D4',
        },
      },
      fontFamily: {
        mono: ['"Courier New"', 'Courier', 'monospace'],
      },
      animation: {
        blink: 'blink 0.8s step-end infinite',
        fadeSlide: 'fadeSlide 0.2s ease forwards',
        fadeIn: 'fadeIn 0.3s ease forwards',
        pulse2: 'pulse2 2s ease-in-out infinite',
      },
      keyframes: {
        blink:     { '0%,100%': { opacity: 1 }, '50%': { opacity: 0 } },
        fadeSlide: { from: { opacity: 0, transform: 'translateX(16px)' }, to: { opacity: 1, transform: 'none' } },
        fadeIn:    { from: { opacity: 0, transform: 'translateY(8px)' },  to: { opacity: 1, transform: 'none' } },
        pulse2:    { '0%,100%': { opacity: 0.4 }, '50%': { opacity: 1 } },
      },
    },
  },
  plugins: [],
}
