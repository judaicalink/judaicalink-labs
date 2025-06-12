/*-------------HAMBURGER-MENU-BUTTON------------------*/

$('#sidebarCollapse').click(function () {
    $('#sidebarCollapse > svg').toggleClass('fa-bars fa-xmark')
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


// read more/less button
$(document).ready(function ($) {
    window.onload = function () {
    $(".show-hide-btn").click(function() {
    var id = $(this).data("id");
    $("#half-" + id).toggle();
    $("#full-" + id).toggle();
    console.log(id);
  })
    }
});
