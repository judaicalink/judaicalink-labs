

<script>
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
          <!-- <div class="row">
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
              </div>-->

<!--Deathlocation-->

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

<!--Datebase-->

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

<!--Entity-->

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

<!--Keyword-->

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

</template>