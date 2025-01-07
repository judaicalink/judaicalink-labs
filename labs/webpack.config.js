const path = require('path');
const MiniCssExtractPlugin = require('mini-css-extract-plugin');
const CssMinimizerPlugin = require('css-minimizer-webpack-plugin');
const TerserPlugin = require('terser-webpack-plugin');
const CompressionPlugin = require('compression-webpack-plugin');
const { BundleAnalyzerPlugin } = require('webpack-bundle-analyzer');
const { VueLoaderPlugin } = require('vue-loader');
const webpack = require('webpack');

module.exports = {
    entry: {
        app: './src/js/app.js',
        styles: './src/scss/app.scss',
    },
    output: {
        path: path.resolve(__dirname, 'dist'),
        filename: '[name].[contenthash].js', // Use contenthash for caching
        chunkFilename: '[name].[contenthash].js', // Dynamic chunks
    },
    mode: 'production',
    devtool: process.env.NODE_ENV === 'development' ? 'source-map' : false,
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
             {
                test: /\.(png|jpe?g|gif|svg)$/i,
                type: 'asset',
                parser: {
                    dataUrlCondition: {
                        maxSize: 8192, // Inline files smaller than 8 KiB
                    },
                },
                generator: {
                    filename: 'img/[name].[contenthash][ext]',
                },
            },
            {
                test: /\.(woff(2)?|eot|ttf|otf|svg)$/i,
                type: 'asset/resource',
                generator: {
                    filename: 'fonts/[name].[contenthash][ext]',
                },
            },
        ],
    },
    plugins: [
        new MiniCssExtractPlugin({
            filename: '[name].css', // Avoid filename conflicts
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
        new BundleAnalyzerPlugin({
            analyzerMode: 'static', // Generates a static HTML report
            openAnalyzer: false, // Prevents auto-opening
        }),
    ],
    resolve: {
        alias: {
            vue: 'vue/dist/vue.esm-bundler.js',
        },
        extensions: ['.js', '.vue'],
    },
    optimization: {
        splitChunks: {
            chunks: 'all', // Split all chunks
            maxSize: 244000, // Set max size for chunks (244 KiB)
        },
        minimize: true,
        minimizer: [
            new TerserPlugin(),
            new CssMinimizerPlugin(),
        ],
    },
};
