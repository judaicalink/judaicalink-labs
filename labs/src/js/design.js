/*-------------HAMBURGER-MENU-BUTTON------------------*/

$('#sidebarCollapse').click(function () {
    $('#sidebarCollapse > svg').toggleClass('fa-bars fa-xmark')
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

// read more/less button

/*
$(document).ready(function ($) {
    window.onload = function () {
        const readMoreLessButton = document.getElementById("more-less-button");

        readMoreLessButton.addEventListener("click", () => {

            if (readMoreLessButton.innerText === "More") {
                readMoreLessButton.innerText = "Less";
            } else {
                readMoreLessButton.innerText = "More";
            }
        });
    }
});
*/


$(document).ready(function ($) {
    window.onload = function () {
    $(".show-hide-btn").click(function() {
    var id = $(this).data("id");
    $("#half").toggle();//hide/show..
    $("#full").toggle();
    console.log(id);
  })
    }
});
