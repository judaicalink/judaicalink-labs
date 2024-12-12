const path = require('path');
const { VueLoaderPlugin } = require('vue-loader');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const webpack = require('webpack');

module.exports = {
    entry: {
        app: './src/js/app.js',
        styles: './src/scss/app.scss',
    },
    output: {
        path: path.resolve(__dirname, 'search/static'),
        filename: 'js/[name].js',
    },
    mode: 'production',
    module: {
        rules: [
            {
                test: /\.js$/,
                exclude: /node_modules/,
                use: 'babel-loader',
            },
            {
                test: /\.vue$/,
                loader: 'vue-loader',
            },
            {
                test: /\.s[ac]ss$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader',
                    'sass-loader', // Add this for SCSS support
                ],
            },
            {
                test: /\.css$/i,
                use: [
                    MiniCssExtractPlugin.loader,
                    'css-loader', // Ensure this handles Vuetify CSS
                ],
            },
            {
                test: /\.(png|jpe?g|gif|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'img/[name][hash][ext]',
                },
            },
            {
                test: /\.(woff(2)?|eot|ttf|otf|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'fonts/[name][hash][ext]',
                },
            },
        ],
    },
    plugins: [
        new VueLoaderPlugin(),
        new MiniCssExtractPlugin({
            filename: 'css/[name].css',
        }),
        new CompressionPlugin({
            test: /\.(js|css|html|svg)$/,
            algorithm: 'gzip',
            threshold: 10240,
            minRatio: 0.8,
        }),
        new CopyWebpackPlugin({
            patterns: [
                { from: './src/img/', to: 'img/' },
            ],
        }),
        new webpack.ProvidePlugin({
            bootstrap: 'bootstrap', // Make Bootstrap globally available
            $: 'jquery', // Ensure jQuery is available if required by Bootstrap
            jQuery: 'jquery',
            Popper: ['@popperjs/core', 'default'], // Include Popper.js
        }),
    ],
    optimization: {
        minimize: true,
        minimizer: [
            new TerserPlugin(),
            new CssMinimizerPlugin(),
        ],
    },
};
