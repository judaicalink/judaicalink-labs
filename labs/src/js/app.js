import '@fortawesome/fontawesome-free/js/all'; // FontAwesome Free
import * as bootstrap from 'bootstrap';
import {createApp} from "vue";
import 'vuetify'

window.bootstrap = bootstrap; // Falls global erwartet

require('./design.js')

// Vue imports
require('./vue.config.js')
import SearchApp from '../vue/search.vue';

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
});
