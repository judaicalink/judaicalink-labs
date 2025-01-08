import { createApp } from 'vue';
import SearchApp from '../vue/search.vue';
import FilterApp from '../vue/filter.vue';
import AutocompleteApp from '../vue/autocomplete.vue';

import 'vuetify/styles'; // Ensure Vuetify styles are included
import { createVuetify } from 'vuetify';
import * as components from 'vuetify/components';
import * as directives from 'vuetify/directives';
import { defineAsyncComponent } from 'vue';


const vuetify = createVuetify({
    components,
    directives,
});

// Dynamically load Vue components
const SearchApp = defineAsyncComponent(() =>
    import(/* webpackChunkName: "search-app" */ '../vue/search.vue')
);

const FilterApp = defineAsyncComponent(() =>
    import(/* webpackChunkName: "filter-app" */ '../vue/filter.vue')
);

const AutocompleteApp = defineAsyncComponent(() =>
    import(/* webpackChunkName: "autocomplete-app" */ '../vue/autocomplete.vue')
);

export default {
    components: {
        SearchApp,
        FilterApp,
        AutocompleteApp,
    },
};

//SearchApp.createApp(SearchApp).use(vuetify).mount('#search-app');
//FilterApp.createApp(FilterApp).use(vuetify).mount('#filter-app');
//AutocompleteApp.createApp(AutocompleteApp).use(vuetify).mount('#autocomplete-app');
