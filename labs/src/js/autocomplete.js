document.addEventListener("DOMContentLoaded", function(){
    if (typeof(availableTags) !== 'undefined') {
            console.log(availableTags);

            $( function() {
            $( "#entities" ).autocomplete({
              source: availableTags,
              minLength: 2
            });
          } );
    }

});