# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import api, fields, models
import time


class SaleOrder(models.Model):
    _inherit = "sale.order"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('proforma', 'Proforma'),
        ('lqdr', 'Pending LQDR'),
        ('progress_lqdr', 'Progress LQDR'),
        ('pending', 'Revision Pending '),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    @api.multi
    def action_proforma(self):
        for order in self:
            order.state = 'proforma'
        return True

    @api.multi
    def action_lqdr_option(self):
        for order in self:
            if order.order_line.filtered('product_id.lqdr'):
                order.state = 'lqdr'
            else:
               order.state = 'pending'
        return True

    @api.multi
    def action_lqdr_ok(self):
        for order in self:
            order.state = 'pending'
        return True

    @api.multi
    def action_pending_ok(self):
        for order in self:
            order.action_sale()
        return True

    @api.multi
    def action_sale(self):
        for order in self:
            order.action_confirm()
            picking_out = order.picking_ids.filtered(lambda x: x.picking_type_id.code == 'outgoing')
            picking_out.write({'ready': True})
        return True

    @api.onchange('warehouse_id')
    def _onchange_warehouse_id(self):
        """
        Avoid change warehouse_company_id
        """
        return


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    state = fields.Selection([
        ('draft', 'Quotation'),
        ('sent', 'Quotation Sent'),
        ('lqdr', 'LQDR'),
        ('pending', 'Pending Approval'),
        ('sale', 'Sales Order'),
        ('done', 'Locked'),
        ('cancel', 'Cancelled'),
    ])

    lqdr = fields.Boolean(related="product_id.lqdr", store=False)

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        res = super(SaleOrderLine, self).product_id_change()
        if self.product_id.route_ids:
            self.route_id = self.product_id.route_ids[0]
        return res

    @api.multi
    def _get_display_price(self, product):
        res = super(SaleOrderLine, self)._get_display_price(product)
        # Search for specific prices in variants
        qty = product._context.get('quantity', 1.0)
        vals = {}

        today = self.order_id.date_order or time.strftime('%Y-%m-%d')
        domain = [('partner_id', '=', self.order_id.partner_id.id),
                  ('product_id', '=', self.product_id.id),
                  ('min_qty', '<=', qty),
                  '|',
                  ('date_start', '=', False),
                  ('date_start', '<=', today),
                  '|',
                  ('date_end', '=', False),
                  ('date_end', '>=', today),
        ]
        customer_prices = self.env['customer.price'].\
            search(domain, limit=1, order='min_qty desc')
         # Search for specific prices in templates
        if not customer_prices:
            domain = [
                ('partner_id', '=', self.order_id.partner_id.id),
                ('product_tmpl_id', '=', self.product_id.product_tmpl_id.id),
                ('min_qty', '<=', qty),
                '|',
                ('date_start', '=', False),
                ('date_start', '<=', today),
                '|',
                ('date_end', '=', False),
                ('date_end', '>=', today),
            ]
            customer_prices = self.env['customer.price'].\
                search(domain, limit=1, order='min_qty desc')
        if customer_prices:
            return customer_prices.price
        return res
