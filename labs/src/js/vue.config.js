// config for vue
import Vue from 'vue';
import { createApp } from 'vue';
import SearchApp  from "../vue/search.vue";
import FilterApp  from "../vue/filter.vue";

// Vuetify
import 'vuetify/styles'
import { createVuetify } from 'vuetify'
import * as components from 'vuetify/components'
import * as directives from 'vuetify/directives'

const vuetify = createVuetify({
  components,
  directives,
})

module =  {
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


//export default createVuetify()

createApp(SearchApp).use(vuetify).mount('#search-app').config('delimiters', ['[[', ']]'])
createApp(FilterApp).use(vuetify).mount('#filter-app').config('delimiters', ['[[', ']]'])
