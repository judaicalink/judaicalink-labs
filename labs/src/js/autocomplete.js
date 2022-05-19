// for the autocomplete function in cm_e_search
import autocomplete from "jquery";


    if (typeof (availableTags) !== 'undefined') {
        console.log(availableTags);

        $(function () {
            $("#entities").autocomplete({
                source: availableTags,
                minLength: 2
            });
        });
    }
