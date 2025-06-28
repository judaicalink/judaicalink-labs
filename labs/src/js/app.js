import '@fortawesome/fontawesome-free/js/all'; // FontAwesome Free
import * as bootstrap from 'bootstrap';
import {createApp} from "vue";

import SearchApp from '../vue/search.vue';
import AutocompleteApp from '../vue/autocomplete.vue';
//import FilterApp from '../vue/filter.vue';

// Vuetify
import 'vuetify/styles'
import '@mdi/font/css/materialdesignicons.css'

import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
});

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

    //Autocomplete-App
    const autocompleteEl = document.querySelector('#autocomplete-search');
    if (autocompleteEl) {
        const app = createApp(AutocompleteApp);
        app.use(vuetify);
        app.mount('#autocomplete-search');
    } else {
        console.warn('#autocomplete-app not found in DOM – Vue not mounted');
    }

    // Filter-App
    //const filterEl = document.querySelector('#filter-app');
    //if (filterEl) {
    //    const fapp = createApp(FilterApp);
    //    fapp.use(vuetify);
    //    fapp.mount('#filter-app');
    //}
});



// 2) create the Vuetify instance

// 3) when DOM is ready, mount your app with Vuetify
document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('search-app');
  if (!el) {
    console.warn('#search-app not found – skipping Vue mount');
    return;
  }

  const app = createApp(SearchApp);
  app.use(vuetify);           // ← here’s the critical bit
  app.mount('#search-app');
});
