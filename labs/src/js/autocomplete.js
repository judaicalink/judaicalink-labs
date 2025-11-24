// static/js/autocomplete.js
import { createApp } from 'vue'
import Autocomplete from '../vue/autocomplete.vue'

document.addEventListener('DOMContentLoaded', () => {
  const el = document.getElementById('autocomplete-search')
  if (el) {
    createApp(Autocomplete).mount(el)
  }
})
