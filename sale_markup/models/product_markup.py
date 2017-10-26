# -*- coding: utf-8 -*-
# Copyright 2011 Camptocamp SA
# Copyright 2017 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).
from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class Product(models.Model):
    _inherit = 'product.product'

    @api.model
    def _convert_to_foreign_currency(self, pricelist,
                                     amount_dict, context=None):
        """
        Apply purchase pricelist
        """
        if not pricelist:
            return amount_dict
        pricelist_obj = self.env['product.pricelist']
        currency_obj = self.env['res.currency']
        user_obj = self.env['res.users']
        pricelist = pricelist_obj.browse(pricelist)
        user = user_obj.browse(uid)
        company_currency_id = user.company_id.currency_id.id
        converted_prices = {}
        for product_id, amount in amount_dict.iteritems():
            converted_prices[product_id] = currency_obj.compute(
                company_currency_id, pricelist.currency_id.id, amount,
                round=False)
        return converted_prices

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
    def compute_markup(self, pricelist=None, sale_price=None, cost_price=None):
        """
        compute markup

        If pricelist and sale_price arguments are set, it
        will be used to compute all results
        """
        self.ensure_one()
        res = {}

        purchase_prices = self._convert_to_foreign_currency(
            pricelist, purchase_prices)
        for pr in self:
            res[pr.id] = {}
            if sale_price is None:
                catalog_price = pr.list_price
            else:
                catalog_price = sale_price
            if cost_price:
                purchase_prices[pr.id] = pr.bom_standard_cost

            res[pr.id].update({
                'commercial_margin': catalog_price - purchase_prices[pr.id],
                'markup_rate': self._compute_markup(catalog_price,
                                                    purchase_prices[pr.id]),
                'cost_price': purchase_prices[pr.id]
            })
        return res

    @api.multi
    def _get_bom_product(self):
        """return ids of modified product and ids of all product that use
        as sub-product one of this ids. Ex:
        BoM :
            Product A
                -   Product B
                -   Product C
        => If we change standard_price of product B, we want to update Product
        A as well..."""
        def _get_parent_bom(bom_record):
            """Recursvely find the parent bom"""
            result = []
            if bom_record.bom_id:
                result.append(bom_record.bom_id.id)
                result.extend(_get_parent_bom(bom_record.bom_id))
            return result
        res = []
        bom_obj = self.env['mrp.bom']
        bom_ids = bom_obj.search([('product_id', 'in', ids)],
                                 context=context)
        for bom in bom_obj.browse(bom_ids):
            res += _get_parent_bom(bom)
        final_bom_ids = list(set(res + bom_ids))
        return list(set(ids + self._get_product(final_bom_ids,
                                                context=context)))

    @api.multi
    def _get_product(self):
        bom_obj = self.env['mrp.bom']

        res = {}
        for bom in bom_obj.browse(ids):
            res[bom.product_id.id] = True
        return res.keys()

    @api.multi
    @api.depends('uom_id',
                 'bom_standard_cost',
                 'list_price', 'standard_price')
    def _compute_all_markup(self):
        """
        method for product function field on multi 'markup'
        """
        return self.compute_markup(ids)

    commercial_margin = fields.Float(
            compute='_compute_all_markup',
            string='Margin',
            digits=dp.get_precision('Sale Price'),
            help='Margin is [ sale_price - cost_price ] (not based on '
                 'historical values)')
    markup_rate = fields.Float(
            compute='_compute_all_markup',
            string='Markup',
            digits=dp.get_precision('Sale Price'),
            help='Markup is [ margin / sale_price ] (not based on '
                 'historical values)')
