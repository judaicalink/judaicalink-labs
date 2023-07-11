

<script setup>
import { ref } from 'vue';

export default {
  setup() {
    const selectedOption = ref('');
    const options = ref([
      { label: 'Deathlocation A', value: 'dla' },
      { label: 'Deathlocation B', value: 'dlb' },
      { label: 'Deathlocation C', value: 'dlc' }
    ]);

    return {
      selectedOption,
      options
    };
  }
};
</script>



<template>




    <div class="row">
                  <div class="col-10">
                 <label for="birthloc" class="form-label">Birthlocation
                 </label>
                  <div>
                    <select v-model="selectedOption">
                      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
                    </select>
                  <p>Ausgewählte Option: {{ selectedOption }}</p>
                  </div>
                 </div>
                  <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>










  <!-- <div>
    <select v-model="selectedOption">
      <option v-for="option in options" :key="option.value" :value="option.value">{{ option.label }}</option>
    </select>
    <p>Ausgewählte Option: {{ selectedOption }}</p>
  </div> -->
</template>