// config file for Webpack
const path = require('path');
const CopyWebpackPlugin = require('copy-webpack-plugin');
const MiniCssExtractPlugin = require("mini-css-extract-plugin");
const CssMinimizerPlugin = require("css-minimizer-webpack-plugin");
const FixStyleOnlyEntriesPlugin = require("webpack-fix-style-only-entries");
const { CleanWebpackPlugin } = require('clean-webpack-plugin')
require('vue-loader');
require('dotenv-webpack');
require('dotenv').config();


const { Module } = require('webpack');
const mode = process.env.MODE || 'NONE';



module.exports = [
    {
        // export for JavaScript files
        entry: './src/js/app.js', //read from this file
        mode: mode, //development or production
        devtool: 'source-map', //source-map or eval-source-map
        output: {
            path: __dirname + '/search/static/js/', //output folder for javascript files
            filename: 'bundle.js' // output file, as a bundle
        },
        module: {
            rules: [
                {
                    test: require.resolve('jquery'),
                    loader: "expose-loader",
                    options: {
                      exposes: ["$", "jQuery", "jquery", "vue", "Vue", "jquery-ui"]
                    },
                }
            ]
        },
        // copy the image files
        plugins: [
            new CopyWebpackPlugin({
                patterns: [
                    { from: './src/img/', to: __dirname + '/search/static/img/'},
                ],
            }),
        ]
    },


    {
        // export for CSS files
        entry: {styles: './src/scss/app.scss'},
        mode: mode,
        devtool: 'source-map',
        //  output file and its location
        output: {
            path: __dirname + '/search/static/css/', //output folder for css files
            //assetModuleFilename: '../img/[hash][ext][query]',
        },
        plugins: [
            new FixStyleOnlyEntriesPlugin(),
            new CleanWebpackPlugin({
                cleanAfterEveryBuildPatterns: ['dist'],
            }),
            new MiniCssExtractPlugin({
                filename: '[name].css',
            }),
        ],
        module: {
            rules: [
                {
                    test: /\.(sa|sc|c)ss$/,
                    //use: [MiniCssPlugin.loader, 'css-loader', 'sass-loader'],
                    use: [MiniCssExtractPlugin.loader, 'css-loader', 'postcss-loader', 'sass-loader'],
                },
                {
                    // for vue
                    test: /\.vue$/,
                    loader: 'vue-loader',
                },
                {

                    // for images
                    test: /\.(png|svg|jpg|jpeg|gif)$/i,
                    type: 'asset/resource',
                    generator: { filename: '../img/[name][ext]' },
                },
                {
                    // for fonts, like font-awesome
                    test: /\.(woff(2)?|ttf|eot|svg)(\?v=\d+\.\d+\.\d+)?$/,
                    type: 'asset/resource',
                    generator: { filename: '../fonts/[name][ext]' },

                },
            ],
        },
        optimization: {
            minimize: true,
                minimizer: [
                  // For webpack@5 you can use the `...` syntax to extend existing minimizers (i.e. `terser-webpack-plugin`), uncomment the next line
                  // `...`,

                  new CssMinimizerPlugin({ minimizerOptions: {
                          preset: [
                              "default",
                              {
                                  discardComments: {removeAll: true},
                              },
                          ],
                      }
                  }),
            ],
        },
    },

];
