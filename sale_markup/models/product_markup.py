# -*- coding: utf-8 -*-
# Copyright 2011 Camptocamp SA
# Copyright 2017 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class ProductProduct(models.Model):
    _inherit = 'product.product'

    commercial_margin = fields.Float(
            related='product_tmpl_id.commercial_margin')
    markup_rate = fields.Float(
            related='product_tmpl_id.commercial_margin')

    @api.multi
    @api.depends('uom_id',
                 'bom_standard_cost',
                 'list_price', 'standard_price')
    def _compute_markup_rate(self):
        """
        method for product function field on multi 'markup'
        """
        for pr in self:
            pr.product_tmpl_id._compute_markup_rate()
        return True


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    @staticmethod
    def _compute_markup(sale_price, purchase_price):
        """
        Return markup as a rate

        Markup = SP - PP / SP

        Where SP = Sale price
              PP = Purchase price
        """
        if not sale_price:
            if not purchase_price:
                return 0.0
            else:
                return -9999.0
        return (sale_price - purchase_price) / sale_price * 100

    @api.multi
    def _compute_markup_rate(self):
        """
        method for product function field on multi 'markup'
        """
        for pr in self:
            catalog_price = pr.list_price
            purchase_price = pr.bom_standard_cost
            pr.commercial_margin = catalog_price - purchase_price
            pr.markup_rate = self._compute_markup(catalog_price,
                                                  purchase_price)
            pr.cost_price = purchase_price
        return True

    commercial_margin = fields.Float(
            compute='_compute_markup_rate',
            string='Margin',
            digits=dp.get_precision('Product Price'),
            help='Margin is [ sale_price - cost_price ] (not based on '
                 'historical values)')
    markup_rate = fields.Float(
            compute='_compute_markup_rate',
            string='Markup',
            digits=dp.get_precision('Product Price'),
            help='Markup is [ margin / sale_price ] (not based on '
                 'historical values)')
