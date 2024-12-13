import 'jquery'; // jQuery for Bootstrap
import 'bootstrap'; // Bootstrap JavaScript
import 'bootstrap/dist/css/bootstrap.min.css'; // Bootstrap CSS
import '@popperjs/core'; // Popper.js for Bootstrap
import '@fortawesome/fontawesome-free/js/all'; // FontAwesome Free

// Vue imports
import { createApp } from 'vue';


// Initialize Vue
createApp(App).mount('#app');

// Additional project-specific JavaScript files
require('./activePageHighlighting.js');
require('malihu-custom-scrollbar-plugin/jquery.mCustomScrollbar.js');
require('./design.js');
