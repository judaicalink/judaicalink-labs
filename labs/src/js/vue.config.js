// config for vue
import Vue from 'vue';
import { createApp } from 'vue';
import search  from "../vue/search.vue";
import filter  from "../vue/filter.vue";

const search_app = createApp(search);
search_app.mount('#search-app');

const filter_app = createApp(filter);
filter_app.mount('#filter-app');