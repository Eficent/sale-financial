# -*- coding: utf-8 -*-
# Copyright 2011 Camptocamp SA
# Copyright 2017 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


def _prec(obj, mode=None):
    # This function use orm cache it should be efficient
    mode = mode or 'Sale Price'
    return self.env['decimal.precision'].precision_get(mode)


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.multi
    def _compute_markup_rate(self):
        """Calculate the markup rate based on sums"""
        for sale_order in self:
            cost_sum = 0.0
            sale_sum = 0.0
            for line in sale_order.order_line:
                cost_sum += line.product_uom_qty * line.cost_price
                sale_sum += line.product_uom_qty * \
                    (line.price_unit * (100 - line.discount) / 100.0)
            markup_rate = ((sale_sum - cost_sum) / sale_sum * 100 if sale_sum
                           else 0.0)
            sale_order.markup_rate = markup_rate
        return True

    @api.multi
    @api.depends('order_line', 'order_line.price_unit', 'order_line.tax_id',
                 'order_line.discount', 'order_line.product_uom_qty',
                 'order_line.product_id', 'order_line.order_id',
                 'order_line.commercial_margin', 'order_line.markup_rate')
    def _get_order(self, sale_order_lines):
        for line in sale_order_lines:
            result.add(line.order_id.id)
        return list(result)


    markup_rate = fields.Float(
            compute=_compute_markup_rate,
            string='Markup (%)',
            digits=dp.get_precision('Sale Price'))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    commercial_margin = fields.Float(
            'Margin',
            digits=dp.get_precision('Sale Price'),
            help='Margin is [ sale_price - cost_price ], changing it will '
                 'update the discount', readonly=True, states={'draft': [(
                    'readonly', False)]})
    markup_rate = fields.Float(
            'Markup (%)',
            digits=dp.get_precision('Sale Price'),
            help='Markup is [ margin / sale_price ], changing it will '
                 'update the discount', readonly=True, states={'draft': [(
                    'readonly', False)]})
    cost_price = fields.Float(
            'Cost Price',
            digits=dp.get_precision('Sale Price'),
            help='The cost of the product. The product cost price at the '
                 'time of creating the sales order is proposed, '
                 'but can be changed by the user.', readonly=True,
                states={'draft': [('readonly', False)]})
        # boolean fields to skip onchange loop

    pricelist_id = fields.Many2one(related='order_id.pricelist_id',
                                   string='Pricelist', readonly=True)
    date_order = fields.Datetime(related='order_id.date_order',
                                 string='Date', readonly=True)

    @api.multi
    @api.onchange('price_unit', 'product_id', 'order_id.discount',
                  'product_uom_qty', 'pricelist_id')
    def onchange_price_unit(self):
        '''
        If price unit change, compute the new markup rate.
        '''
        self.ensure_one()
        if self.product_id:
            sale_price = self.price_unit * (100 - self.discount) / 100.0
            markup_res = self.compute_markup(product_id,
                                                    product_uom,
                                                    pricelist,
                                                    sale_price)[product_id]


            self.commercial_margin = round(
                markup_res['commercial_margin'], self._prec)
            self.markup_rate = round(markup_res['markup_rate'], self._prec)

    @api.multi
    @api.onchange('discount')
    def onchange_discount(self):
        '''
        If discount change, compute the new markup rate
        '''
        self.ensure_one()
        if product_id:
            product_obj = self.env['product.product']
            if res['value'].has_key('price_unit'):
                price_unit = res['value']['price_unit']
            if res['value'].has_key('discount'):
                discount = res['value']['discount']
            sale_price = price_unit * (100 - discount) / 100.0
            markup_res = self.product_id.compute_markup(
                pricelist, sale_price, cost_price)

            self.commercial_margin = round(
                markup_res['commercial_margin'], self._prec())
            self.markup_rate = round(markup_res['markup_rate'], self._prec())
        return res

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        '''
        Overload method
        If product change, compute the new markup.
        Added params : - price_unit,
                       - discount
        '''
        discount = discount or 0.0
        price_unit = price_unit or 0.0

        if self.product_id:
            if res['value'].has_key('price_unit'):
                price_unit = res['value']['price_unit']
            #sale_price = price_unit * (100 - discount) / 100.0
            markup_res = self.product_id.compute_markup()[product]

            self.commercial_margin = round(
                markup_res['commercial_margin'],  self._prec())
            self.markup_rate = round(
                int(markup_res['markup_rate'] * 100) / 100.0, self._prec())
            self.bom_standard_cost = round(
                markup_res['cost_price'],  self._prec())

    @api.multi
    @api.onchange('markup_rate')
    def onchange_markup_rate(self):
        ''' If markup rate change compute the discount '''
        self.ensure_one()
        markup = markup / 100.0
        if not price_unit or markup == 1: return {'value': {}}
        discount = 1 + cost_price / (markup - 1) / price_unit
        self.sale_price = price_unit * (1 - discount)
        self.discount =  round(discount * 100, self._prec())
        self.commercial_margin = round(sale_price - cost_price, self._prec())

    @api.multi
    @api.onchange('commercial_margin')
    def onchange_commercial_margin(self):
        ''' If markup rate change compute the discount '''
        self.ensure_one()
        if not self.price_unit: return False
        discount = 1 - ((cost_price + margin) / price_unit)
        sale_price = price_unit * (1 - discount)
        self.discount = round(discount * 100, self._prec())
        self.markup_rate = round(
            margin / (sale_price or 1.0) * 100, self._prec())
