
// This file is used to configure Vue.js applications in the labs/src/js directory.

// import { createApp } from 'vue';
import 'vuetify/styles';
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

// Add the necessary CSS
import bootstrap from 'bootstrap';
//const bootstrap = require('bootstrap')

//import FilterApp from '../vue/filter.vue';
//import AutocompleteApp from '../vue/autocomplete.vue';

//const FilterApp = defineAsyncComponent(() =>
//  import(/* webpackChunkName: "filter-app" */ '../vue/filter.vue')
//);

//const AutocompleteApp = defineAsyncComponent(() =>
//   import(/* webpackChunkName: "autocomplete-app" */ '../vue/autocomplete.vue')
//);


//FilterApp.createApp(FilterApp).use(vuetify).mount('#filter-app');
//AutocompleteApp.createApp(AutocompleteApp).use(vuetify).mount('#autocomplete-app');


const vuetify = createVuetify({ components, directives });
