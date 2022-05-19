// import all the necessary files here

import 'jquery';
import 'jquery-ui';
import 'popper.js';
import $ from 'jquery';
import autocomplete from 'jquery-ui/ui/widgets/autocomplete';

// font awesome
import '@fortawesome/fontawesome-free/js/fontawesome'
import '@fortawesome/fontawesome-free/js/solid'
import '@fortawesome/fontawesome-free/js/regular'
import '@fortawesome/fontawesome-free/js/brands'

require('./activePageHighlighting.js'); // import active page highlighting javascript files
//import('./autocomplete.js'); // import auto complete for cm_e_search
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