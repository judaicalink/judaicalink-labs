<template>
  <div>
    <v-text-field
      v-model="searchQuery"
      label="Search"
      outlined
      clearable
      @input="debouncedFetchResults"
    />
    <div v-if="results.length === 0 && !loading" class="mt-3">
      No results found.
    </div>
    <v-virtual-scroller
      v-else
      :items="results"
      item-height="48"
      class="mt-3"
    >
      <template #default="{ item }">
        <v-list-item>
          <v-list-item-content>
            <!-- Accessing the name property directly -->
            <v-list-item-title>{{ item.name || 'Unknown' }}</v-list-item-title>
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
      results: [], // Array to hold results
      start: 0,
      rows: 20, // Number of results per request
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
          `https://labs.judaicalink.org/cm_e_search/api/get_names?query=${encodeURIComponent(this.searchQuery)}&start=${this.start}&rows=${this.rows}`
        );
        const data = await response.json();

        if (Array.isArray(data.results)) {
          if (this.start === 0) {
            this.results = data.results; // Set results to the array directly
          } else {
            this.results = [...this.results, ...data.results]; // Append new results for lazy loading
          }

          if (data.results.length < this.rows) {
            this.noMoreResults = true; // No more results to fetch
          }
        } else {
          console.error("Invalid API response format:", data);
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
      this.start = 0;
      this.noMoreResults = false;
      this.fetchResults();
    }, 300),
    async loadMoreResults() {
      if (this.noMoreResults || this.loading) return;

      this.start += this.rows;
      await this.fetchResults();
    },
  },
};
</script>

<style scoped>
/* Add custom styles as needed */
</style>
