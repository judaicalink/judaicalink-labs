/*
autocomplete.vue
This file handles the autocomplete dropdown for CM Entity Search.
Using vuetify components.
https://vuetifyjs.com/en/components/autocompletes/#usage
created by Benjamin Schnabel
b.schnabel@hs-mannheim.de
*/
<script setup>
</script>

<script>
// here comes the Javascript code

export default {
  name: 'AutocompleteApp',
  delimiters: ['[[', ']]'],
  data() {
    return {
      data: [],
    };
  },
  methods: {
    mounted() {
      data = availableTags
      console.log('Autocomplete component mounted.')
    },
  }
};

</script>

<template>
    <v-app>
    <v-container>
    <v-autocomplete
  clearable
  label="Autocomplete"
  :items=data
></v-autocomplete>
    </v-container>
  </v-app>
</template>

<style scoped>


</style>