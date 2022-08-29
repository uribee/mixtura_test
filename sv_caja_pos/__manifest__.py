# -*- coding: utf-8 -*-
{
    'name': "sv_caja_pos",

    'summary': """
       Contiene adiciones a los cajas para El Salvador""",

    'description': """
        Contiene adiciones a las cajas para El Salvador
    """,

    'author': "Roberto Leonel Gracias Ramos",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['base','sv_accounting','point_of_sale'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
