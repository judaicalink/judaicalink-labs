import '@fortawesome/fontawesome-free/js/all'; // FontAwesome Free
import * as bootstrap from 'bootstrap';
import {createApp} from "vue";

import SearchApp from '../vue/search.vue';
//import FilterApp from '../vue/filter.vue';

// Vuetify
import '@mdi/font/css/materialdesignicons.css'
import 'vuetify/styles'

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

export default createVuetify({
  components,
  directives,
})
window.bootstrap = bootstrap; // For global access in the browser console

require('./design.js')


document.addEventListener('DOMContentLoaded', () => {
    //Search-App
    const el = document.querySelector('#search-app');
    if (el) {
        const app = createApp(SearchApp);
        app.use(vuetify);
        app.mount('#search-app');
    } else {
        console.warn('#search-app not found in DOM – Vue not mounted');
    }

    // Filter-App
    //const filterEl = document.querySelector('#filter-app');
    //if (filterEl) {
    //    const fapp = createApp(FilterApp);
    //    fapp.use(vuetify);
    //    fapp.mount('#filter-app');
    //}
});
