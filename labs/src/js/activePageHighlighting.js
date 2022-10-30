pathName = window.location.pathname.trim();
page = pathName.split("/").filter(function (e) {return e != null;});

console.log (pathName)
console.log (page)

if (page[1] != null) {
    //console.log('Active page: ' + page[1]);
    console.log("a[href='/" + page[1] + "']");
    console.log(page[1]);
    $("a[href='/" + page[1] + "']").addClass("active");
}
else {
    console.log('no element available');
}
