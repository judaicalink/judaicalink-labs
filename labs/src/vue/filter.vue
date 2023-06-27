/*
filter.vue
This file creates and handles the filter component for the search results.
created by Christian Deuschle
cd60@hdm-stuttgart.de
20.06.2023
*/
<script setup>
  import { ref } from 'vue'

  const value = ref([20, 40])
</script>

<script>
 // here comes the Javascript code

 export default {
   name: 'filter',
  data() {
    return {
      counter : 0,
      value: [20, 40],
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

            <form name="py_facetFilter1" id="py_facetFilter1">
              <label for="py_facetFilter1" class="form-label">Birthdate</label>
                <div class="row">
                  <div class="col-sm-5">
                    <label for="py_facetfrom">
                    from:
                    </label>
                    <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" value="1897" maxlength="4" />
                  </div>
                  <div class="col-sm-5">
                    <label for="py_facetto">
                    to:
                    </label>
                    <input type="text" class="form-control" name="py_facetto" id="py_facetto" value="1923" maxlength="4" />
                  </div>
                  <div class="col-sm-2">
                    <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
                </div>
                  <input type="range" class="form-range" min="0" max="2023" value="2023"> <!-- must be a dual range slider -->
            </form>
            <label for="py_facetFilter2" class="form-label">Deathdate</label>
            <form name="py_facetFilter2" id="py_facetFilter2">
              <div class="row">
                  <div class="col-sm-5">
                    <label for="py_facetfrom">
                    from:
                    </label>
                    <input type="text" class="form-control" name="py_facetfrom" id="py_facetfrom" value="1897" maxlength="4" />
                  </div>
                  <div class="col-sm-5">
                    <label for="py_facetto">
                    to:
                    </label>
                    <input type="text" class="form-control" name="py_facetto" id="py_facetto" value="1923" maxlength="4" />
                  </div>
                  <div class="col-sm-2">
                    <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>
                <input type="range" class="form-range" min="0" max="2023" value="2023"> <!-- must be a dual range slider -->
            </form>
              <div class="row">
                  <div class="col-10">
                 <label for="birthloc" class="form-label">Birthlocation
                 </label>
                 <select name="birthloc" class="form-select">
                      <option value="">Birthlocation A</option>
                      <option value="">Birthlocation B</option>
                      <option value="">Birthlocation C</option>
                      <option value="">...</option>
                 </select>
                 </div>
                  <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>

                  <div class="row">
                  <div class="col-10">
                  <label for="deathloc" class="form-label">Deathlocation</label>
                  <select name="deathloc" class="form-select">
                      <option value="">Deathlocation A</option>
                      <option value="">Deathlocation B</option>
                      <option value="">Deathlocation C</option>
                      <option value="">...</option>
                  </select>
              </div>
              <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>
                  <div class="row">
                  <div class="col-10">
                  <label for="language" class="form-label">Language</label>
                  <select name="language" class="form-select" >
                      <option value="">English</option>
                      <option value="">German</option>
                      <option value="">French</option>
                      <option value="">Ivrit</option>
                      <option value="">...</option>
                  </select>
              </div>
              <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>
                  <div class="row">
                  <div class="col-10">
                  <label for="database" class="form-label">Database</label>
                  <select name="database" class="form-select" > <!--does the ordered_dataset contain the
                  datebase where th e information comes from? -- than we can make this dynamic -->
                      <option value="">Gidal Image Archive</option>
                      <option value="">Soundscape Synagogue</option>
                      <option value="">Epidat - Epigraphical Database</option>
                      <option value="">Entity Pages - Judaicalink</option>
                      <option value="">Linking Compact Memory - Pages</option>
                      <option value="">Linking Compact Memory - Resources and References</option>
                      <option value="">DBpedia and Wikipedia Geographical External Links</option>
                      <option value="">Yivo Encyclopedia</option>
                      <option value="">Translations for Rujen (Google)</option>
                      <option value="">Encyclopedia of Russian Jewry</option>
                      <option value="">Enrichment of Birth- and Deathdates</option>
                      <option value="">Geographic Enrichment</option>
                      <option value="">Resources on German-Jewish Education and Religion</option>
                      <option value="">The Library of Haskala</option>
                      <option value="">Persons from NLI</option>
                      <option value="">The Library of Haskala</option>
                      <option value="">Persons from ubffm</option>
                      <option value="">Persons from NLI</option>
                      <option value="">Stolpersteine in Mainz</option>
                      <option value="">Persons from DBPedia</option>
                      <option value="">Eine Jüdische Familie aus Aschaffenburg</option>
                      <option value="">Geographical Coordinates</option>
                      <option value="">Persons from GND</option>
                      <option value="">Encyclopedia Interlinks</option>
                      <option value="">Biographisches Handbuch der Rabbiner</option>
                      <option value="">Das Jüdische Hamburg</option>
                      <option value="">Links to external sources</option>
                  </select>

              </div>
                      <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>
              <div class="row">
                  <div class="col-10">
                  <label for="entity" class="form-label">Entity</label>
                  <select name="entity" class="form-select" >
                      <option value="">Person</option>
                      <option value="">Entity A</option>
                      <option value="">Entity B</option>
                      <option value="">Entity C</option>
                      <option value="">...</option>
                  </select>
              </div>
                  <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>
              </div>
              <div class="row">
                  <div class="col-10">
                  <label for="occu" class="form-label">Occupation</label>
                  <select name="occu" class="form-select" >
                      <option value="">Rabbi</option>
                      <option value="">Lawyer</option>
                      <option value="">Occupation A</option>
                      <option value="">Occupation B</option>
                      <option value="">Occupation C</option>
                      <option value="">...</option>
                  </select>
                      </div>
                      <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>

              </div>
              <div class="row">
                  <div class="col-10">
                  <label for="keyword" class="form-label">Keyword</label>
                  <select name="keyword" class="form-select" >
                      <option value="">Keyword A</option>
                      <option value="">Keyword B</option>
                      <option value="">Keyword C</option>
                      <option value="">...</option>
                  </select>
                      </div>
                      <div class="col-auto">
                       <label for="hits">
                    hits:
                    </label>
                      <br>
                    <h5><span name="hits" class="badge bg-secondary mt-3">+99</span></h5>
                  </div>

              </div>
              <br>
              <br>
              <br>
              <button type="submit" class="btn btn-primary search_button position-absolute bottom-0 end-0 m-3">Use filter</button>
            </div>
  </div>

  <!--begintest-->

  <v-card>
    <v-card-text>
      <v-range-slider
        v-model="value"
        strict
      ></v-range-slider>
    </v-card-text>
  </v-card>

  <!--endtest-->
</template>

<style scoped>


</style>