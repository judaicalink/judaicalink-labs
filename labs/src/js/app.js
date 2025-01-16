import 'jquery'; // jQuery for Bootstrap
import 'bootstrap'; // Bootstrap JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'; // Bootstrap CSS
import '@popperjs/core'; // Popper.js for Bootstrap
import '@fortawesome/fontawesome-free/js/all'; // FontAwesome Free

// Vue imports
import { createApp } from 'vue';

// Lazy load large modules
//import(/* webpackChunkName: "large-module" */ './largeModule')
//    .then(({ default: largeModule }) => {
//         largeModule.init();
//     })
//     .catch((err) => {
//         console.error('Error loading large module:', err);
//     });
//
// import(/* webpackChunkName: "styles" */ '../scss/largeStyles.scss')
//         .then(() => {
//             console.log('Styles loaded dynamically');
//         })
//         .catch((err) => {
//             console.error('Error loading styles:', err);
//         });

// Initialize Vue
createApp(App).mount('#search-app');

require('bootstrap');
require('malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.js')
require('./design.js')


//require('./vue.config.js')