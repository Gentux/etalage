$(function () {
    territoryAutocompleterUrl = "http://127.0.0.1:5002/api/v1/autocomplete-territory";
    $('#territory').autocomplete({
        source: function(request, response) {
            $.ajax({
                url: territoryAutocompleterUrl + '?jsonp=?',
                dataType: 'jsonp',
                data: {
                    term: request.term
                },
                success: function (data) {
                    response($.map(data.data.items, function(item) {
                        var label = item.main_postal_distribution;
                        if (item.main_postal_distribution != item.nearest_postal_distribution) {
                            label += ' (' + item.nearest_postal_distribution + ')';
                        }
                        if (item.type_name != 'Arrondissement municipal' && item.type_name != 'Commune'
                                && item.type_name != 'Commune associée') {
                            label += ' (' + item.type_name + ')';
                        }
                        return {
                            label: label,
                            value: item.main_postal_distribution
                        };
                    }));
                }
            });
        }
    });
});

