require('dotenv').config();
const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { VueLoaderPlugin } = require('vue-loader');
const webpack = require('webpack');
const BundleTracker = require('webpack-bundle-tracker');


module.exports = {
    productionSourceMap: false,
    entry: {
        app: './src/js/app.js',
        bootstrap: './src/js/bootstrap.js', // Adding Bootstrap entry point
        styles: './src/scss/app.scss',
    },
    output: {
        path: path.resolve(__dirname, 'static'), // Output to Django's static folder
        filename: 'js/[name].[contenthash].js', // Output JS files to static/js/
        chunkFilename: 'js/[name].[contenthash].js', // Dynamic chunks in static/js/
        publicPath: '/static/', // Base path for assets
        sourceMapFilename: 'js/[name].[contenthash].js.map',
    },
    mode: 'development',
    devtool: process.env.NODE_ENV === 'development' ? 'eval-source-map' : 'source-map',
    module: {
        rules: [
            {
                test: /\.vue$/,
                loader: 'vue-loader',
            },
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: 'babel-loader',
            },
            {
                test: /\.s[ac]ss$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader',
                ],
            },
            {
                test: /\.css$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                ],
            },
            {
                test: /\.(png|jpe?g|gif|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'img/[name].[contenthash][ext]', // Output images to static/img/
                },
            },
            {
                test: /\.(woff(2)?|eot|ttf|otf|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'fonts/[name].[contenthash][ext]', // Output fonts to static/fonts/
                },
            },
        ],
    },
    plugins: [
        new BundleTracker({ path: __dirname, filename: 'webpack-stats.json' }),
        new MiniCssExtractPlugin({
            filename: 'css/[name].[contenthash].css', // Output CSS to static/css/
        }),
        new VueLoaderPlugin(),
        new CompressionPlugin({
            test: /\.(js|css|html|svg)$/,
            algorithm: 'gzip',
            threshold: 10240,
            minRatio: 0.8,
        }),
        new webpack.ProvidePlugin({
            $: 'jquery',
            jQuery: 'jquery',
            Popper: ['@popperjs/core', 'default'],
            bootstrap: 'bootstrap',
        }),
    ],
    resolve: {
        alias: {
            vue: 'vue/dist/vue.esm-bundler.js',
        },
        extensions: ['.js', '.vue'],
    },
    optimization: {
        minimize: true,
        splitChunks: {
            chunks: 'all', // Enable code splitting
            maxSize: 244000, // Split chunks larger than 244 KiB
        },
        minimizer: [
            new TerserPlugin(),
            new CssMinimizerPlugin(),
        ],
    },
};
