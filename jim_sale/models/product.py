# -*- coding: utf-8 -*-
# © 2016 Comunitea - Javier Colmenero <javier@comunitea.com>
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo import fields, models, api
import odoo.addons.decimal_precision as dp


class ProductTemplate(models.Model):
    _inherit = "product.template"

    @api.multi
    def _get_customer_prices_count(self):
        for tmpl in self:
            tmpl.customer_prices_count = len(tmpl.customer_tmpl_prices)

    lqdr = fields.Boolean('LQDR')
    customer_tmpl_prices = fields.One2many('customer.price', 'product_tmpl_id',
                                           'Customer Prices')
    customer_prices_count = fields.\
      Integer(compute='_get_customer_prices_count', string='#Prices')

    
class ProductPorduct(models.Model):
    _inherit = "product.product"

    @api.multi
    def _get_customer_prices_count(self):
        for prod in self:
            prod.customer_prices_count = len(prod.customer_product_prices)

    customer_product_prices = fields.One2many('customer.price', 'product_id',
                                              'Customer Prices')
    customer_prices_count = fields.\
      Integer(compute='_get_customer_prices_count', string='#Prices')

   
class CustomerPrice(models.Model):
    _name = "customer.price"

    product_tmpl_id = fields.Many2one('product.template', 'Template')
    product_id = fields.Many2one('product.product', 'Product')
    partner_id = fields.Many2one('res.partner', 'Customer', required=True)
    min_qty = fields.Float('Min Quantity', default=0.0, required=True)
    price = fields.Float(
        'Price', default=0.0, digits=dp.get_precision('Product Price'),
        required=True, help="The price to purchase a product")
    date_start = fields.Date('Start Date',
                             help="Start date for this customer price")
    date_end = fields.Date('End Date',
                           help="End date for this customer price")
