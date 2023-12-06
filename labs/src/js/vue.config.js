// config for vue
import Vue from 'vue';
import { createApp } from 'vue';
import search  from "../vue/search.vue";
import filter  from "../vue/filter.vue";

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
})

const search_app = createApp(search);
search_app.mount('#search-app');

const filter_app = createApp(filter);
filter_app.use(vuetify);
filter_app.mount('#filter-app');
filter_app.config.


module.exports = {
  chainWebpack: config => {
    config.module
      .rule('vue')
      .use('vue-loader')
      .tap(options => {
        options.compilerOptions = {
          delimiters: ['[[', ']]']  // Set the delimiters to [[ and ]]
        };
        return options;
      });
  }
};


export default createVuetify()