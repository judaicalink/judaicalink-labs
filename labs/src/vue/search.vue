<template>

<form  method="get" action="search">
    <input type="hidden" name="page" value="1">
    <div v-for="(row, index) in rows" class="row">

      <!--Operator-->
      <div v-if="index <= 0" class="form-group col-2">
        <!--Placeholder for missing Operators in first row-->
      </div>

      <div v-else class="form-group col-2">
         <select v-model="row.selected_operator" class="form-select" :name="row.operator">
          <option v-for="(operator) in row.other_operators" v-bind:value="operator.fieldname">{{operator.display}}</option>
        </select>
      </div>

      <!--Option-->
      <div class="form-group col-4">
        <select v-model="row.selected_option" class="form-select" :name="row.option">
          <option v-for="(option) in row.other_options" v-bind:value="option.fieldname">{{option.display}}</option>
        </select>
      </div>
      <!--Input-->
      <div class="form-group col-5">
        <input v-model="row.submitted_input" type="text" :name="row.input" class="form-control">
      </div>
      <!--@click="removeElement(index);"-->

      <div class="form-group col-1">
          <span role="button" class="btn btn-danger text-white" @click="removeElement(index)"><i class="fas fa-trash"></i></span>
      </div>
    </div>

    <div class="row">
        <div class ="col-auto">
            <span role="button" class="btn btn-primary search_button text-white" @click="addRow()"><i class="fas fa-plus"></i> Add</span>
        </div>

         <div class ="col-auto">
             <span role="button" class="btn btn-danger text-white" @click="clearElements(); addRow(); addRow()">Clear all</span>
         </div>

        <div class ="col-md-3 ms-md-auto">
            <button type="submit" class="btn btn-primary search_button float-right text-white"><i class="fas fa-search"></i> Search</button>
        </div>
    </div>
</form>
</template>


<script>
export default {
  // export the function and name it search
  name : 'SearchApp',
  delimiter: ['[[', ']]'],

  // create empty data
  data() {
    return {
      rows: [],
      counter: 0,
    };
  },

  // define the methods
  methods: {
    returnData: function() {
      try {
        /* rows_data is defined in views.py and is passed on to search_result.html*/
        //this.rows = rows_data;
        this.rows = document.getElementById('rows').textContent;
        this.rows = JSON.parse(JSON.parse(this.rows));
        console.log(typeof this.rows);
        console.log(this.rows);
        // if the standard search is used we don't get values in rows_data
        // need to throw an error so the standard rows will be generated
        if (this.rows == null) {
            this.rows = [];
            throw new TypeError();
            /* console.log(this.rows); */
        }
        return this.rows;
      }
          /* create 2 standard rows */
      catch (error) {
        this.rows = [
          {
            operator: "operator1",
            option: "option1",
            input: "input1",
            selected_operator: " AND ",
            other_operators: [
              {
                display: "AND",
                fieldname: " AND "
              },
              {
                display: "OR",
                fieldname: " OR "
              },
              {
                display: "NOT",
                fieldname: " NOT "
              }
            ],
            selected_option: "name:",
            other_options: [
              {
                display: "Name",
                fieldname: "name:"
              },
              {
                display: "Alternatives",
                fieldname: "Alternatives:"
              },
              {
                display: "Publication",
                fieldname: "Publication:"
              },
              {
                display: "Birthdate",
                fieldname: "birthDate:"
              },
              {
                display: "Deathdate",
                fieldname: "deathDate:"
              },
              {
                display: "Birthlocation",
                fieldname: "birthLocation:"
              },
              {
                display: "Deathlocation",
                fieldname: "deathLocation:"
              }
            ],
            submitted_input: "",
          },
          {
            operator: "operator2",
            option: "option2",
            input: "input2",
            selected_operator: " AND ",
            other_operators: [
              {
                display: "AND",
                fieldname: " AND "
              },
              {
                display: "OR",
                fieldname: " OR "
              },
              {
                display: "NOT",
                fieldname: " NOT "
              }
            ],
            selected_option: "name:",
            other_options: [
              {
                display: "Name",
                fieldname: "name:"
              },
              {
                display: "Alternatives",
                fieldname: "Alternatives:"
              },
              {
                display: "Publication",
                fieldname: "Publication:"
              },
              {
                display: "Birthdate",
                fieldname: "birthDate:"
              },
              {
                display: "Deathdate",
                fieldname: "deathDate:"
              },
              {
                display: "Birthlocation",
                fieldname: "birthLocation:"
              },
              {
                display: "Deathlocation",
                fieldname: "deathLocation:"
              }
            ],
            submitted_input: "",
          }
        ];
        /* console.log(error);
        console.log("We have no data! - therefore 2 standard rows"); */
        return this.rows;
      }

    },

    // remove function addRow
    addRow: function () {
      this.elem = document.createElement('div');

      /*creating the distinct names for input and select fields
                    when the "addRow"-function is activated
                    and increasing the value of the counter accordingly*/
      this.rows.push({
        operator: `operator${++this.counter}`,
        option: `option${this.counter}`,
        input: `input${this.counter}`,
        selected_operator: " AND ",
        other_operators: [
          {
            display: "AND",
            fieldname: " AND "
          },
          {
            display: "OR",
            fieldname: " OR "
          },
          {
            display: "NOT",
            fieldname: " NOT "
          }
        ],
        selected_option: "name:",
        other_options: [
          {
            display: "Name",
            fieldname: "name:"
          },
          {
            display: "Alternatives",
            fieldname: "Alternatives:"
          },
          {
            display: "Publication",
            fieldname: "Publication:"
          },
          {
            display: "Birthdate",
            fieldname: "birthDate:"
          },
          {
            display: "Deathdate",
            fieldname: "deathDate:"
          },
          {
            display: "Birthlocation",
            fieldname: "birthLocation:"
          },
          {
            display: "Deathlocation",
            fieldname: "deathLocation:"
          }
        ],
        submitted_input: "",
      });
    },

    //create function removeElement
    removeElement: function (index) {
      this.rows.splice(index, 1);
    },

    // create function clearElements
    clearElements: function (index) {
      this.rows.splice(0);

    },

  },
  // when the app is mounted make these functions available
  mounted() {

    this.returnData();
    this.addRow();
    this.removeElement();
    this.clearElements();
    this.rows = this.returnData();
    this.counter = (typeof (this.returnData()) !== 'undefined') ? this.returnData(2).length : 0;
  }
};

</script>


<style>

</style>