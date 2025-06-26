const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { VueLoaderPlugin } = require('vue-loader');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');
const CopyWebpackPlugin = require('copy-webpack-plugin');

module.exports = {
  entry: {
    app: './src/js/app.js',
    bootstrap: './src/js/bootstrap.js',
    styles: './src/scss/app.scss',
    autocomplete: './src/js/autocomplete.js',
  },
  output: {
    path: path.resolve(__dirname, 'build'),
    filename: 'js/[name].js',
    publicPath: '/static/',
    sourceMapFilename: 'js/[file].map',
  },
  mode: process.env.NODE_ENV === 'development' ? 'development' : 'production',
  devtool: process.env.NODE_ENV === 'development' ? 'eval-source-map' : 'source-map',
  module: {
    rules: [
      { enforce: 'pre', test: /\.js$/, use: ['source-map-loader'] },
      { test: /\.vue$/, loader: 'vue-loader' },
      { test: /\.js$/, exclude: /node_modules/, use: 'babel-loader' },
      {
        test: /\.s[ac]ss$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader', 'sass-loader'],
      },
      {
        test: /\.css$/i,
        use: [MiniCssExtractPlugin.loader, 'css-loader'],
      },
      {
        test: /\.(png|jpe?g|gif|svg|ico)$/i,
        type: 'asset/resource',
        generator: { filename: 'img/[name][ext]' },
      },
      {
        test: /\.(woff(2)?|eot|ttf|otf)$/i,
        type: 'asset/resource',
        generator: { filename: 'fonts/[name][ext]' },
      },
    ],
  },
  plugins: [
    new webpack.DefinePlugin({
      __VUE_OPTIONS_API__: true,
      __VUE_PROD_DEVTOOLS__: false,
      __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false,
    }),
    new BundleTracker({ path: __dirname, filename: 'webpack-stats.json' }),
    new MiniCssExtractPlugin({ filename: 'css/[name].css' }),
    new VueLoaderPlugin(),
    new CompressionPlugin({ test: /\.(js|css|html|svg)$/, algorithm: 'gzip', threshold: 10240, minRatio: 0.8 }),
    new webpack.ProvidePlugin({
      $: 'jquery',
      jQuery: 'jquery',
      'window.jQuery': 'jquery',
      'window.$': 'jquery',
      Popper: ['@popperjs/core', 'default'],
    }),
    new CopyWebpackPlugin({
      patterns: [
        {
          from: path.resolve(__dirname, 'node_modules/@popperjs/core/dist/umd/popper.min.js.map'),
          to: 'core/js',
        },
        {
          from: path.resolve(__dirname, 'node_modules/bootstrap/dist/js/bootstrap.min.js.map'),
          to: 'core/js',
        },
        {
          from: path.resolve(__dirname, 'node_modules/bootstrap/dist/css/bootstrap.min.css.map'),
          to: 'core/css',
        },
        {
          from: path.resolve(__dirname, 'src/img/**/*'),
          to: 'img',
        },
      ],
    }),
  ],
  resolve: {
    alias: { vue: 'vue/dist/vue.esm-bundler.js' },
    extensions: ['.js', '.vue', '.json'],
  },
  optimization: {
    minimize: true,
    minimizer: [
      new TerserPlugin({ extractComments: false }),
      new CssMinimizerPlugin(),
    ],
  },
};
