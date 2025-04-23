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
    entry: {
        app: './src/js/app.js',
        bootstrap: './src/js/bootstrap.js',
        styles: './src/scss/app.scss',
        autocomplete: './src/js/autocomplete.js', // for autocomplete
    },
    output: {
        path: path.resolve(__dirname, 'build'), // Webpack compiles into `build/`
        filename: 'js/[name].[contenthash].js',
        chunkFilename: 'js/[name].[contenthash].js', // Dynamic chunks in static/js/
        publicPath: '/static/', // Django serves files from /static/
        sourceMapFilename: 'js/[name].[contenthash].js.map',
    },
    mode: process.env.NODE_ENV === 'development' ? 'development' : 'production',
    //devtool: process.env.NODE_ENV === 'development' ? 'eval-source-map' : false,
    devtool: false,
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
        new webpack.DefinePlugin({
            __VUE_OPTIONS_API__: true, // or false if you're not using `options` API
            __VUE_PROD_DEVTOOLS__: false,
            __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: false, // usually fine
        }),
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
            'window.jQuery': 'jquery',
            'window.$': 'jquery',
            Popper: ['@popperjs/core', 'default'],
        }),
    ],
    resolve: {
        alias: {
            vue: 'vue/dist/vue.esm-bundler.js',
        },
        extensions: ['.js', '.vue', '.json'],
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
