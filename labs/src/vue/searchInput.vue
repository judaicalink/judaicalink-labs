<template>
  <div class="search-input">
    <b>Search:</b>
    <p>
      <input type="search" name="criteria" />
      <button type="submit">search</button>
    </p>
  </div>
</template>
<script lang="ts">
import { Component, Vue } from 'vue-property-decorator';
@Component
export default class SearchInput extends Vue {}
</script>