module.exports = {
  content: ['./page.html'],
  darkMode: 'class',
  theme: { extend: { colors: { slate: { 850: '#111827', 950: '#030712' } } } },
  safelist: [
    { pattern: /^(text|bg|border)-(rose|sky|indigo|emerald|amber|slate|teal|cyan|blue)-(200|300|400|500|950)(\/(20|30|40|60|90))?$/ },
    'hidden', 'ring-1'
  ]
};
