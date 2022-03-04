/*-------------HAMBURGER-MENU-BUTTON------------------*/

$('#sidebarCollapse').click(function () {
    $('#sidebarCollapse svg').toggleClass('fa-bars fa-times')
});

/*-------------------SIDEBAR-------------------------*/
$(document).ready(function () {
    $("#sidebar").mCustomScrollbar({
        theme: "minimal"
    });

    $('#sidebarCollapse').on('click', function () {
        $('#sidebar, #content').toggleClass('active');
        $('.collapse.in').toggleClass('in');
        $('a[aria-expanded=true]').attr('aria-expanded', 'false');
    });
});

/*------------Sidebar active page highlighting---------------*/

$(document).ready(function ($) {
    var path = window.location.pathname.split("/").pop();

    if (path == '') {
        path = ''; /*das ist die Startseite von Labs http://labs.judaicalink.org/!leer!/*/
    }

    var target = $('#sidebar a[href="' + path + '"]');

    target.addClass('active');
});

/*---------------------------------------------------*/
/*$(document).on('click', 'ul li', function(){
                $(this).addClass('active').siblings().removeClass('active')
                })
/*---------------------------------------------------*/
/*let ul = document.querySelector('ul');
let li = document.querySelector('li');

li.forEach(el => {
    el.addEventListener('click',function(){
        ul.querySelector('.active').classList.
            remove('active');

        el.classList.add('active');
        });
    });*/
/*---------------------------------------------------*/
/*$(document).on('click', 'ul li', function(){
                $(this).addClass('current').siblings().removeClass('current')
                })*/
/*------------Sidebar active page highlighting---------------*/
$(document).ready(function ($) {
    window.onload = function () {
        if ($('#buttonadvancedsearch').length) {
            const buttonadvancedsearch = document.getElementById("buttonadvancedsearch");

            buttonadvancedsearch.addEventListener("click", () => {

                if (buttonadvancedsearch.innerText === "Advanced Search") {
                    buttonadvancedsearch.innerText = "Simple Search";
                } else {
                    buttonadvancedsearch.innerText = "Advanced Search";
                }
            });
        }
    }
});

/*------------Vue.js---------------*/
function returnData() {

    try {
        /* rows_data is defined in views.py and is passed on to search_result.html*/
        if (typeof(rows_data) !== 'undefined') {
            var rows = rows_data;
            /* if rows is not None or empty*/
            if (rows) {
                /*alert("We have data!");*/
                return rows;

            } else {
                throw new TypeError();
            }
        }


    }
        /* create 2 standard rows */ catch (error) {
        var rows = [
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
        console.log(error);
        /*alert("We have no data! - therefore 2 standard rows")*/
        return rows;
    }


}

$(document).ready(function ($) {
    if ($('#app').length) {
        var app = new Vue({
            el: "#app",
            data: {
                /*a counter is needed to create distinct names for inputs and select fields
                when the "addRow"-function is used*/
                rows: returnData(),
                counter: (typeof(returnData()) !== 'undefined') ? returnData(2).length : 0,

            },

            methods: {
                addRow: function () {
                    var elem = document.createElement('div');

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
                removeElement: function (index) {
                    this.rows.splice(index, 1);
                },
                clearElements: function (index) {
                    this.rows.splice(0);

                },

            }
        });
    }

});
