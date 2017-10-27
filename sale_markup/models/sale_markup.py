# -*- coding: utf-8 -*-
# Copyright 2011 Camptocamp SA
# Copyright 2017 Eficent
# License AGPL-3.0 or later (http://www.gnu.org/licenses/agpl).

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


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
            digits=dp.get_precision('Product Price'))


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    commercial_margin = fields.Float(
            'Margin',
            digits=dp.get_precision('Product Price'),
            help='Margin is [ sale_price - cost_price ], changing it will '
                 'update the discount', readonly=True, states={'draft': [(
                    'readonly', False)]})
    markup_rate = fields.Float(
            'Markup (%)',
            digits=dp.get_precision('Product Price'),
            help='Markup is [ margin / sale_price ], changing it will '
                 'update the discount', readonly=True, states={'draft': [(
                    'readonly', False)]})
    cost_price = fields.Float(
            'Cost Price',
            digits=dp.get_precision('Product Price'),
            help='The cost of the product. The product cost price at the '
                 'time of creating the sales order is proposed, '
                 'but can be changed by the user.', readonly=True,
                states={'draft': [('readonly', False)]})

    @api.multi
    @api.onchange('price_unit', 'product_id', 'order_id.discount',
                  'product_uom_qty', 'pricelist_id')
    def onchange_price_unit(self):
        '''
        If price unit change, compute the new markup rate.
        '''
        self.ensure_one()
        if self.product_id:
            self.product_id._compute_markup_rate()
            self.commercial_margin = self.product_id.commercial_margin
            self.markup_rate = self.product_id.markup_rate

    @api.multi
    @api.onchange('discount')
    def onchange_discount(self):
        '''
        If discount change, compute the new markup rate
        '''
        self.ensure_one()
        if self.product_id:
            self.product_id._compute_markup_rate()
            self.commercial_margin = self.product_id.commercial_margin
            self.markup_rate = self.product_id.markup_rate

    @api.multi
    @api.onchange('product_id')
    def onchange_product_id(self):
        '''
        Overload method
        If product change, compute the new markup.
        Added params : - price_unit,
                       - discount
        '''
        if self.product_id:
            self.product_id._compute_markup_rate()
            self.commercial_margin = self.product_id.commercial_margin
            self.markup_rate = int(self.product_id.markup_rate * 100) / 100.0
            self.cost_price = self.product_id.bom_standard_cost

    @api.multi
    @api.onchange('markup_rate')
    def onchange_markup_rate(self):
        ''' If markup rate change compute the discount '''
        self.ensure_one()
        markup = self.markup_rate / 100.0
        if not self.price_unit or markup == 1:
            return False
        discount = (1 + self.cost_price / (markup - 1) / self.price_unit)
        sale_price = self.price_unit * (1 - discount)
        self.discount = discount * 100
        self.commercial_margin = sale_price - self.cost_price

    @api.multi
    @api.onchange('commercial_margin')
    def onchange_commercial_margin(self):
        ''' If markup rate change compute the discount '''
        self.ensure_one()
        if not self.price_unit:
            return False
        discount = 1 - ((self.cost_price + self.margin) / self.price_unit)
        sale_price = self.price_unit * (1 - discount)
        self.discount = discount * 100
        self.markup_rate = (self.margin / (sale_price or 1.0) * 100)
