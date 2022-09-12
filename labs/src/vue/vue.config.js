module.exports = {
  filenameHashing: false,
  pages: {
    'search-form': {
      entry: <code>${__dirname}/src/modules/search-form/main.ts</code>,
      template: <code>${__dirname}/public/search-form.html</code>,
      filename: 'search-form.html',
      title: 'Demo - Search Form',
    },
  },
};