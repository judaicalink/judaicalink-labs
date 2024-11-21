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
            <v-list-item-title>{{ item?.name || 'Unknown' }}</v-list-item-title>
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
          `https://labs.judaicalink.org/cm_e_seaarch/api/get_names?query=${encodeURIComponent(this.searchQuery)}&start=${this.start}&rows=${this.rows}`
        );
        const data = await response.json();
        console.log("API response:", data); // Debugging output

        if (Array.isArray(data.results)) {
          console.log("Fetched results:", data.results); // Debugging output

          if (this.start === 0) {
            this.results = data.results; // Reset results for new queries
          } else {
            this.results = [...this.results, ...data.results]; // Append for lazy loading
          }

          if (data.results.length < this.rows) {
            this.noMoreResults = true; // Stop further loading
          }
        } else {
          console.error("API response format invalid:", data);
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
      this.start = 0; // Reset pagination for new searches
      this.noMoreResults = false;
      this.fetchResults();
    }, 300),
    async loadMoreResults() {
      if (this.noMoreResults || this.loading) return;

      this.start += this.rows; // Update starting point
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
/* Add any custom styles as needed */
</style>
