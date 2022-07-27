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
import('./autocomplete.js'); // import auto complete for cm_e_search

require('bootstrap');
require('malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.js')
require('./design.js')


//import { createApp } from 'vue'
// import the root component App from a single-file component.
//import Vue from 'vue';
//import SearchForm from './SearchForm.vue';
//Vue.config.productionTip = false;
//new Vue({
//  render: h => h(SearchForm),
//}).$mount('#searchForm');

//const app = createApp(App)
//app.mount('#app')

import {Vue} from 'vue';
import search  from "../vue/search.vue";

new Vue({
    el: '#app',
    components: {
        search
    }
} ).$mount('#app');
