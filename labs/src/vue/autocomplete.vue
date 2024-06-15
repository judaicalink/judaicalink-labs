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
      names: []
    };
  },
  created() {
    this.fetchNames();
  },
  methods: {
    async fetchNames() {
      try {
        let response = await fetch('/cm_e_search/get-names');
        if (response.ok) {
          let data = await response.json();
          this.names = data.names;
        } else {
          console.error('Failed to fetch names:', response.statusText);
        }
      } catch (error) {
        console.error('Failed to fetch names:', error);
      }
    },
    submit() {
      this.$emit('submit', this.names)
    }
  }
};

</script>

<template>
    <v-app>
    <v-container>
    <v-autocomplete
        clearable="true"
  label="Search"
  :items="names"
  variant="outlined"
></v-autocomplete>
     <v-btn prepend-icon="$mdi-magnify"
     class="mt-2"
        text="Search"
        type="submit">
</v-btn>
    </v-container>
  </v-app>
</template>

<style scoped>


</style>