// config for vue
import Vue from 'vue';
import { createApp } from 'vue';
import SearchApp  from "../vue/search.vue";
import FilterApp  from "../vue/filter.vue";
import AutocompleteApp  from "../vue/autocomplete.vue";

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
})

createApp(SearchApp).use(vuetify).mount('#search-app')
createApp(FilterApp).use(vuetify).mount('#filter-app')
createApp(AutocompleteApp).use(vuetify).mount('#autocomplete-app')