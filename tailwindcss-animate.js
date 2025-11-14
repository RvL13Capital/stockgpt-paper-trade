const plugin = require('tailwindcss/plugin')

module.exports = plugin(function({ addUtilities, matchUtilities, theme }) {
  addUtilities({
    '.animate-pulse-subtle': {
      animation: 'pulse-subtle 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
    },
  })

  matchUtilities(
    {
      'animation-delay': (value) => ({
        animationDelay: value,
      }),
    },
    { values: theme('transitionDelay') }
  )
})