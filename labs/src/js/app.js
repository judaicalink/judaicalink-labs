// import all the necessary files here

//import 'bootstrap'; // import bootstrap javascript files
//import './design.js'; // import design javascript files
//require('jquery'); // import jquery javascript files
//global.jQuery = require('jquery');


// use jquery globally
/*
window.jQuery = $;
window.$ = $;
jquery = $;
 */
require('jquery');
require('jquery-ui'); // import bootstrap javascript files
require('popper.js'); // import popper javascript files
//require('@fortawesome/fontawesome-free')
// font awesome
import '@fortawesome/fontawesome-free/js/fontawesome'
import '@fortawesome/fontawesome-free/js/solid'
import '@fortawesome/fontawesome-free/js/regular'
import '@fortawesome/fontawesome-free/js/brands'

require('./activePageHighlighting.js'); // import active page highlighting javascript files
require('./autocomplete.js'); // import active page highlighting css files
import Vue from 'vue';

require('bootstrap');
require('malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.js')
require('./design.js')


import { createApp } from 'vue'
// import the root component App from a single-file component.
import App from '../vue/search.vue'

const app = createApp(App)
app.mount('#app')

//require('../vue/search.vue')