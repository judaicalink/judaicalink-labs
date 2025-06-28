/*
autocomplete.vue
This file handles the autocomplete dropdown for CM Entity Search.
Using vuetify components.
https://vuetifyjs.com/en/components/autocompletes/#usage
created by Benjamin Schnabel
b.schnabel@hs-mannheim.de
*/
<template>
  <div class="autocomplete-container position-relative">
    <div class="input-group">
      <input
        ref="inputField"
        type="text"
        class="form-control"
        v-model="query"
        name="query"
        @input="onInput"
        @focus="showSuggestions = true"
        @keydown.down.prevent="highlightNext"
        @keydown.up.prevent="highlightPrev"
        @keydown.enter.prevent="selectHighlighted"
        @keydown.esc="showSuggestions = false"
        @keyup.enter="$autocompleteEl.form.submit()"
        placeholder="Type a name..."
        autocomplete="off"
        aria-label="Entity search"
      />
      <button class="btn btn-primary" @click="submitSearch">
        <i class="fa fa-search"></i> Search
      </button>
    </div>

    <ul
      v-if="showSuggestions && suggestions.length"
      class="list-group position-absolute w-100 shadow"
      style="z-index: 1000; max-height: 300px; overflow-y: auto;"
    >
      <li
        v-for="(item, index) in suggestions"
        :key="item.value"
        class="list-group-item list-group-item-action"
        :class="{ active: index === highlightedIndex }"
        @mousedown.prevent="select(item)"
      >
        {{ item.label }}
      </li>
    </ul>

    <div v-if="error" class="text-danger mt-2">{{ error }}</div>
  </div>
</template>

<script>
export default {
  data() {
    return {
      query: '',
      selected: null,
      suggestions: [],
      highlightedIndex: -1,
      showSuggestions: false,
      loading: false,
      error: null,
    };
  },
  methods: {
    onInput() {
      this.selected = null;
      this.highlightedIndex = -1;
      if (this.query.length >= 2) {
        this.fetchSuggestions(this.query);
      } else {
        this.suggestions = [];
        this.showSuggestions = false;
      }
    },
    async fetchSuggestions(query) {
      this.loading = true;
      this.error = null;
      const BASE_URL = `${window.location.origin}/api/cm/names/`;

      try {
        const response = await fetch(`${BASE_URL}?format=json&q=name:${encodeURIComponent(query)}*&limit=20`);
        const data = await response.json();
        const docs = data?.response?.docs;

        if (!Array.isArray(docs)) throw new Error('Invalid response');

        this.suggestions = docs
          .filter(doc => Array.isArray(doc.name) && doc.name.length > 0)
          .map(doc => ({
            label: doc.name[0],
            value: doc.name[0],
          }));

        this.showSuggestions = true;

      } catch (err) {
        console.error(err);
        this.error = 'Autocomplete service unavailable (Solr might be down).';
        this.suggestions = [];
        this.showSuggestions = false;
      } finally {
        this.loading = false;
      }
    },
    select(item) {
      this.query = item.label;
      this.selected = item;
      this.showSuggestions = false;
    },
    selectHighlighted() {
      if (this.highlightedIndex >= 0 && this.highlightedIndex < this.suggestions.length) {
        this.select(this.suggestions[this.highlightedIndex]);
      } else {
        this.submitSearch();
      }
    },
    highlightNext() {
      if (this.highlightedIndex < this.suggestions.length - 1) {
        this.highlightedIndex++;
      }
    },
    highlightPrev() {
      if (this.highlightedIndex > 0) {
        this.highlightedIndex--;
      }
    },
    submitSearch() {
      const searchTerm = this.selected?.value || this.query;
      if (!searchTerm) return;
      const url = `/cm_e_search/search_result/?query=${encodeURIComponent(searchTerm)}`;
      window.location.href = url;
    }
  }
};
</script>

<style scoped>
.autocomplete-container {
  width: 100%;
}
.list-group-item.active {
  background-color: #0d6efd;
  color: white;
}
</style>
