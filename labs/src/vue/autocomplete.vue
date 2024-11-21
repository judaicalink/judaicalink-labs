/*
autocomplete.vue
This file handles the autocomplete dropdown for CM Entity Search.
Using vuetify components.
https://vuetifyjs.com/en/components/autocompletes/#usage
created by Benjamin Schnabel
b.schnabel@hs-mannheim.de
*/

<template>
  <div>
    <v-text-field
      v-model="searchQuery"
      label="Search"
      @input="debouncedFetchResults"
      outlined
    />
    <div v-if="results.length === 0" class="mt-3">
      No results found.
    </div>
<v-virtual-scroller
  :items="results"
  item-height="48"
>
  <template #default="{ item }">
    <v-list-item>
      <v-list-item-content>
        <v-list-item-title>{{ item.name }}</v-list-item-title>
      </v-list-item-content>
    </v-list-item>
  </template>
</v-virtual-scroller>

  </div>
</template>

<script>
import { debounce } from "lodash";

export default {
  data() {
    return {
      results: [], // Ensure this is properly initialized
      searchQuery: '',
      loading: false,
    };
  },
  methods: {
    async fetchResults() {
  this.loading = true;
  try {
    const response = await fetch(`/api/get_names?query=${encodeURIComponent(this.searchQuery)}`);
    const data = await response.json();

    if (Array.isArray(data.results)) {
      this.results = data.results;
    } else {
      console.error("API did not return an array:", data);
      this.results = [];
    }
  } catch (error) {
    console.error("Error fetching results:", error);
    this.results = [];
  } finally {
    this.loading = false;
  }
},
    debouncedFetchResults: debounce(function () {
      this.start = 0; // Reset to the beginning for new searches
      this.noMoreResults = false;
      this.fetchResults();
    }, 300),
    async loadMoreResults() {
      if (this.noMoreResults || this.loading) return;

      this.start += this.rows; // Update the starting point
      await this.fetchResults();
    },
  },
  mounted() {
    // Add infinite scroll listener
    const observer = new IntersectionObserver(
      (entries) => {
        const lastEntry = entries[0];
        if (lastEntry.isIntersecting) {
          this.loadMoreResults();
        }
      },
      {
        root: null,
        rootMargin: "0px",
        threshold: 1.0,
      }
    );

    const sentinel = document.createElement("div");
    sentinel.setAttribute("id", "scroll-sentinel");
    document.body.appendChild(sentinel);

    observer.observe(sentinel);
  },
};
</script>

<style scoped>
/* Customize styles as needed */
</style>
