/*
filter.vue
This file creates and handles the filter component for the search results.
created by Christian Deuschle
cd60@hdm-stuttgart.de
20.06.2023
*/
<script setup>
  import { ref } from 'vue'
  import filterSelect from "../components/filterSelect.vue";
  const valueBD = ref([0, 2023])
  const valueDD = ref([])

</script>

<script>
 // here comes the Javascript code

 export default {
   name: 'FilterApp',
   components: {
      filterSelect
   },
   delimiters: ['[[', ']]'],
  data() {
    return {
      counter : 0,
      valueBD: [0, 2023],
      valueDD: [0, 2023],
          };
  },

   methods : {
     mounted() {
       console.log('Filter component mounted.')
     },
   }
 };

</script>

<template>

  <br>
  <div class="card mb-4 rounded-3 shadow-sm">
      <div class="card-header ">Filter
      </div>
          <div class="card-body">

<!--Birthdate-->

      <form name="py_facetFilter1" id="py_facetFilter1">
              <label for="py_facetFilter1" class="form-label">Birthdate</label>
                <div class="row">
                  <div class="col-sm-5">
                    <label for="py_facetfrom">
                    from:
                    </label>
                    <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" v-model="valueBD[0]" maxlength="4" />
                  </div>
                  <div class="col-sm-5">
                    <label for="py_facetto">
                    to:
                    </label>
                    <input type="text" class="form-control" name="py_facetto" id="py_facetto" v-model="valueBD[1]" maxlength="4" />
                  </div>
                  <div class="col-sm-2">
                    <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
                </div>
        </form>

      <v-range-slider
       v-model="valueBD"
        strict
      ></v-range-slider>

<!--Deathdate-->

      <form name="py_facetFilter1" id="py_facetFilter1">
              <label for="py_facetFilter1" class="form-label">Deathdate</label>
                <div class="row">
                  <div class="col-sm-5">
                    <label for="py_facetfrom">
                    from:
                    </label>
                    <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" v-model="valueDD[0]" maxlength="4" />
                  </div>
                  <div class="col-sm-5">
                    <label for="py_facetto">
                    to:
                    </label>
                    <input type="text" class="form-control" name="py_facetto" id="py_facetto" v-model="valueDD[1]" maxlength="4" />
                  </div>
                  <div class="col-sm-2">
                    <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
                </div>
        </form>

      <v-range-slider
       v-model="valueDD"
        strict
      ></v-range-slider>

<!--Birthlocation-->
       <filterSelect />



              <br>
              <br>
              <br>
              <button type="submit" class="btn btn-primary search_button position-absolute bottom-0 end-0 m-3">Use filter</button>
            </div>
  </div>

  <!--begintest-->

  <!--endtest-->
</template>

<style scoped>


</style>