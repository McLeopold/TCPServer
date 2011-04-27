// build html table from json
/* example json table

[
    [ 'header 1', 'header 2' ],
    [ [1.1, 1.2],
      [2.1, 2.2] ]
]

*/
Table = {
    sanitize: function(text) {
        return text.toString().replace(/\&/g,'&amp;').replace(/\</g,'&lt;').replace(/\>/g,'&gt;');
    },
    json2table: function (options) {
        if (options.json_data) {
            json_data = options.json_data;
            if (options.id) {
                table = $('<table id="' + this.sanitize(options.id) + '" />');
            } else {
                table = $('<table />');
            }
            if (options.class) {
                table.addClass(options.class);
            }
            thead = $('<thead />').appendTo(table);
            json_header = json_data[0];
            json_rows = json_data[1];
            header_row = $('<tr />').appendTo(thead);
            for (var i = 0; i < json_header.length; ++i) {
                $('<th>' + this.sanitize(json_header[i]) + '</th>').appendTo(header_row);
            }
            tbody = $('<tbody />').appendTo(table);
            for (var i = 0; i < json_rows.length; ++i) {
                data_row = $('<tr />').appendTo(tbody);
                for (var j = 0; j < json_rows[i].length; ++j) {
                    $('<td>' + this.sanitize(json_rows[i][j]) + '</td>').appendTo(data_row);
                }
            }
            return table;
        }
    }
}