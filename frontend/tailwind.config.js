/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        wine: {
          50: '#fdf2f4',
          100: '#fce7ea',
          200: '#f9d0d9',
          300: '#f4a9b8',
          400: '#ec7a93',
          500: '#df4d6f',
          600: '#cc2d58',
          700: '#ab2049',
          800: '#8f1d41',
          900: '#7a1c3c',
          950: '#440a1d',
        },
        olive: {
          50: '#f7f8ee',
          100: '#edf0d5',
          200: '#dce2ae',
          300: '#c4cf7e',
          400: '#aebb57',
          500: '#90a039',
          600: '#707e2a',
          700: '#566124',
          800: '#464e22',
          900: '#3c4321',
          950: '#1f240e',
        },
        bark: {
          50: '#f8f6f1',
          100: '#eee9dc',
          200: '#ded3bb',
          300: '#cab693',
          400: '#b99a72',
          500: '#ac855a',
          600: '#9f734e',
          700: '#845c42',
          800: '#6c4c3a',
          900: '#583f31',
          950: '#2f2019',
        }
      },
      fontFamily: {
        display: ['"Playfair Display"', 'serif'],
        body: ['"Source Sans 3"', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
