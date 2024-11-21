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
    <v-virtual-scroller
      :items="results"
      item-height="48"
      class="mt-3"
    >
      <template #default="{ item }">
        <v-list-item>
          <v-list-item-content>
            <v-list-item-title>{{ item.name }}</v-list-item-title>
          </v-list-item-content>
        </v-list-item>
      </template>
    </v-virtual-scroller>
    <v-btn
      v-if="loading"
      block
      disabled
      outlined
      class="mt-3"
    >
      Loading...
    </v-btn>
  </div>
</template>

<script>
import { debounce } from "lodash";

export default {
  data() {
    return {
      searchQuery: "",
      results: [],
      start: 0,
      rows: 20, // Number of results to fetch per request
      loading: false,
      noMoreResults: false,
    };
  },
  methods: {
    async fetchResults() {
      if (this.searchQuery.length < 2) {
        this.results = [];
        return;
      }

      this.loading = true;

      try {
        const response = await fetch(
          `/api/get_names?query=${encodeURIComponent(this.searchQuery)}&start=${this.start}&rows=${this.rows}`
        );
        const data = await response.json();

        if (data.results.length < this.rows) {
          this.noMoreResults = true; // Stop loading more if fewer results returned
        }

        if (this.start === 0) {
          this.results = data.results; // Initial fetch
        } else {
          this.results = [...this.results, ...data.results]; // Append new results
        }
      } catch (error) {
        console.error("Error fetching results:", error);
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
