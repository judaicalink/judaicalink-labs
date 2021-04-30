document.addEventListener("DOMContentLoaded", function(){
    //console.log(availableTags);
    
    $( function() {
    $( "#entities" ).autocomplete({
      source: availableTags,
      minLength: 2
    });
  } );
});