const path = require('path');

module.exports = {
  mode: 'development',
  resolve: {
    modules: [path.resolve(__dirname, 'InvenTree/InvenTree/vendor/node_modules')]
  },
    entry: {
      // index: './src/index.js',
      vendor: './InvenTree/InvenTree/vendor/vendor.js',
    },
    output: {
      filename: '[name].js',
      path: path.resolve(__dirname, 'InvenTree', 'InvenTree', 'static', 'script', 'dist'),
    },
   optimization: {
     splitChunks: {
       chunks: 'all',
     },
   },
};
