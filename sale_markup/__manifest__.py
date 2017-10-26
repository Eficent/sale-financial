# -*- coding: utf-8 -*-
# Copyright 2011 Camptocamp SA
# Copyright 2017 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

{
    'name': 'Markup rate on product and sales',
    'version': '10.0.1.0.1',
    'author': "Camptocamp, "
              "Eficent, "
              "Odoo Community Association (OCA)",
    'license': 'AGPL-3',
    'website': 'https://www.github.com/sale-finantial',
    'depends': [
        'base',
        'mrp',
        'sale',
        'product_bom_standard_cost',
    ],
    'summary': """
       Display the product and sale markup in the appropriate views
       """,
    'data': [
        'views/sale_view.xml',
        'views/product_view.xml',
    ],
}
