odoo.define('b_custom_pos.models', function (require) {
 "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', ['dui', 'nit', 'nrc', 'nitex', 'website']);

});
