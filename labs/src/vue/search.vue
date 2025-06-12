<template>
  <v-form @submit.prevent="submitSearch">
    <div v-for="(row, index) in rows" :key="index" class="mb-4">
      <v-row align="center">
        <v-col cols="12" md="2" v-if="index !== 0">
          <v-select
              :items="operatorItems"
              item-value="value"
              item-title="text"
              v-model="row.selected_operator"
              label="Operator"
              dense
              hide-details="auto"
          />

        </v-col>

        <v-col cols="12" md="3">
          <v-select
              :items="optionItems"
              item-value="value"
              item-title="text"
              v-model="row.selected_option"
              label="Field"
              dense
              hide-details="auto"
          />

        </v-col>

        <v-col cols="12" md="6">
          <v-text-field
              v-model="row.submitted_input"
              label="Search term"
              placeholder="e.g. Einstein"
              dense
              hide-details="auto"
          />
        </v-col>

        <v-col cols="12" md="1" v-if="index !== 0">
          <v-btn icon color="error" @click="removeRow(index)">
            <v-icon>mdi-delete</v-icon>
          </v-btn>
        </v-col>
      </v-row>
    </div>

    <v-btn color="primary" @click="addRow">Add field</v-btn>
    <v-btn color="success" type="submit" class="ml-2">Search</v-btn>
  </v-form>
</template>

<script>
export default {
  name: 'SearchApp',
  data() {
    return {
      rows: [],
      operatorItems: [
        {text: 'AND', value: ' AND '},
        {text: 'OR', value: ' OR '},
        {text: 'NOT', value: ' NOT '}
      ],
      optionItems: [
        {text: 'Name', value: 'name:'},
        {text: 'Alternatives', value: 'alternatives:'},
        {text: 'Publication', value: 'publication:'},
        {text: 'Birth Date', value: 'birthDate:'},
        {text: 'Death Date', value: 'deathDate:'},
        {text: 'Birth Location', value: 'birthLocation:'},
        {text: 'Death Location', value: 'deathLocation:'}
      ]
    };
  },
  mounted() {
    // 1. Try to parse Django-injected data
    try {
      const raw = this.$el.dataset.rows || 'null';
      const loadedRows = JSON.parse(raw);

      if (Array.isArray(loadedRows) && loadedRows.length > 0) {
        this.rows = loadedRows.map((r, i) => ({
          selected_operator: typeof r.selected_operator === 'string' ? r.selected_operator : (i === 0 ? '' : ' AND '),
          selected_option: typeof r.selected_option === 'string' ? r.selected_option : 'name:',
          submitted_input: r.submitted_input || ''
        }));

        return;
      }
    } catch (e) {
      console.warn('Failed to parse rows from backend:', e);
    }

    // 2. If nothing loaded, try to parse q param
    const q = new URLSearchParams(window.location.search).get('q');
    if (q) {
      const parsed = this.parseQueryToRows(q);
      if (parsed.length > 0) {
        this.rows = parsed;
        return;
      }
    }

    // 3. Default fallback
    this.initializeDefaultRows();
  },
  methods: {
    initializeDefaultRows() {
      this.rows = [
        {selected_operator: '', selected_option: 'name:', submitted_input: ''},
        {selected_operator: ' AND ', selected_option: 'name:', submitted_input: ''}
      ];
    },
    addRow() {
      this.rows.push({
        selected_operator: ' AND ',
        selected_option: 'name:',
        submitted_input: ''
      });
    },
    removeRow(index) {
      if (index > 0) this.rows.splice(index, 1);
    },
    parseQueryToRows(qstring) {
      const parts = qstring.split(/( AND | OR | NOT )/);
      const rows = [];

      for (let i = 0; i < parts.length; i++) {
        const part = parts[i].trim();
        if (['AND', 'OR', 'NOT'].includes(part)) continue;

        const match = part.match(/^(\w+):(.+)$/);
        if (!match) continue;

        const field = match[1] + ':';
        const value = match[2].trim();
        const operator = i > 0 ? parts[i - 1].trim() : '';

        rows.push({
          selected_operator: operator ? ` ${operator} ` : '',
          selected_option: field,
          submitted_input: value
        });
      }

      return rows;
    },
    submitSearch() {
      const validRows = this.rows.filter(row => row.submitted_input?.trim());

      if (validRows.length === 0) {
        alert('Please enter at least one search term.');
        return;
      }

      const queryParts = validRows.map((row, index) => {
        const prefix = index === 0 ? '' : row.selected_operator || ' AND ';
        return `${prefix}${row.selected_option}${row.submitted_input.trim()}`;
      });

      const q = encodeURIComponent(queryParts.join(' '));
      window.location.href = `/search/search?page=1&q=${q}`;
    }
  }
};
</script>
