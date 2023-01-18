pathName = window.location.pathname.trim();
page = pathName.split("/").filter(function (e) {return e != null;});

if (page[1] != null) {
    $("a[href='/" + page[1] + "']").addClass("active");
}