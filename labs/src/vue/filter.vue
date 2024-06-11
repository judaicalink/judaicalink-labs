/*
filter.vue
This file creates and handles the filter component for the search results.
created by Christian Deuschle
cd60@hdm-stuttgart.de
20.06.2023
*/
<script setup>
import {ref} from 'vue'
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
      counter: 0,
      valueBD: [0, 2023],
      valueDD: [0, 2023],
    };
  },

  methods: {
    mounted() {
      console.log('Filter component mounted.')
    },
  }
};

</script>

<template>

  <div class="card mt-4 rounded-3 shadow-sm">
    <div class="accordion" id="accordionPanelsStayOpenExample">
      <div class="accordion-item">
        <h2 class="accordion-header">
          <button class="accordion-button" type="button" data-bs-toggle="collapse"
                  data-bs-target="#panelsStayOpen-collapseOne" aria-expanded="true"
                  aria-controls="panelsStayOpen-collapseOne">
            Filter
          </button>
        </h2>

        <div id="panelsStayOpen-collapseOne" class="accordion-collapse collapse show">
          <div class="accordion-body">


            <!--Birthdate-->

            <form name="py_facetFilter1" id="py_facetFilter1">
              <label for="py_facetFilter1" class="form-label">Birthdate</label>
              <div class="row">
                <div class="col-sm-5">
                  <label for="py_facetfrom">
                    from:
                  </label>
                  <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" v-model="valueBD[0]"
                         maxlength="4"/>
                </div>
                <div class="col-sm-5">
                  <label for="py_facetto">
                    to:
                  </label>
                  <input type="text" class="form-control" name="py_facetto" id="py_facetto" v-model="valueBD[1]"
                         maxlength="4"/>
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
                  <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" v-model="valueDD[0]"
                         maxlength="4"/>
                </div>
                <div class="col-sm-5">
                  <label for="py_facetto">
                    to:
                  </label>
                  <input type="text" class="form-control" name="py_facetto" id="py_facetto" v-model="valueDD[1]"
                         maxlength="4"/>
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
            <filterSelect/>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>


</style>