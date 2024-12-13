import { createApp } from 'vue';
import SearchApp from '../vue/search.vue';
import FilterApp from '../vue/filter.vue';
import AutocompleteApp from '../vue/autocomplete.vue';

import 'vuetify/styles'; // Ensure Vuetify styles are included
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';

const vuetify = createVuetify({
    components,
    directives,
});

if (document.querySelector('#search-app')) {
    createApp(SearchApp).use(vuetify).mount('#search-app');
}

if (document.querySelector('#filter-app')) {
    createApp(FilterApp).use(vuetify).mount('#filter-app');
}

//if (document.querySelector('#autocomplete-app')) {
    createApp(AutocompleteApp).use(vuetify).mount('#autocomplete-app');
//}
