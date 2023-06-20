/*filter.vue created by Christian Deuschle 20.06.2023/*
<script setup>

</script>

<template>
  <br>

        <div class="text-center table-secondary">Filter</div>



                        <label for="customRange2" class="form-label">Earliest Birthdate</label>
                    <div class="d-flex">
                        <input type="range" class="form-range" min="0" max="2023" value="0">
                        <input type="number" class="input"/>
                    </div>
                        <label for="customRange2" class="form-label">Latest Birthdate</label>
                    <div class="d-flex">
                        <input type="range" class="form-range" min="0" max="2023" value="2023">
                        <input type="number" class="input"/>
                    </div>


            <div>
                <div>
                        <label for="customRange2" class="form-label">Earliest Deathdate</label>
                    <div class="d-flex">
                        <input type="range" class="form-range" min="0" max="2023" value="0">
                        <input type="number" class="input"/>
                    </div>

                        <label for="customRange2" class="form-label">Latest Deathdate</label>
                    <div class="d-flex">
                        <input type="range" class="form-range" min="0" max="2023" value="2023">
                        <input type="number" class="input"/>
                    </div>
                </div>
            </div>
                <div>
                <div>
                    <select class="form-select" >
                        {% for data in ordered_dataset %}
                        {% for item in data %}
                        {%if "Birthlocation" in item  %}
                        <option value="{{ item | safe}}">{{ item | safe}}</option>
                        {% endif %}
                        {% endfor %}
                        {% endfor %}
                    </select>
                </div>
            </div>
              <div>
                <div>
                    <select class="form-select" >
                        {% for data in ordered_dataset %}
                        {% for item in data %}
                        {%if "Deathlocation" in item  %}
                        <option value="{{ item | safe}}">{{ item | safe}}</option>
                        {% endif %}
                        {% endfor %}
                        {% endfor %}
                    </select>
                </div>
            </div>

</template>

<style scoped>

</style>