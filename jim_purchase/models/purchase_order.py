# -*- coding: utf-8 -*-
# © 2016 Comunitea
# License AGPL-3 - See http://www.gnu.org/licenses/agpl-3.0.html
from odoo.exceptions import AccessError, except_orm
from odoo import api, fields, models, _
import odoo.addons.decimal_precision as dp

class PurchaseOrderLine(models.Model):

    _inherit = 'purchase.order.line'

    @api.depends ('product_id', 'product_qty')
    def _get_line_dimension(self):
        for line in self:
            line.line_volume = 0.00
            line.line_weight = 0.00
            if line.product_id:
                line.line_volume = line.product_id.volume * line.product_qty
                line.line_weight = line.product_id.weight * line.product_qty

    line_volume = fields.Float("Volume", compute="_get_line_dimension")
    line_weight = fields.Float("Weight", compute="_get_line_dimension")
    line_info = fields.Char("Line info")
    web_global_stock = fields.Float(related="product_id.web_global_stock")


    @api.depends('order_id.state', 'move_ids.state')
    def _compute_qty_received(self):

        for line in self:
            if line.order_id.state not in ['purchase', 'done']:
                line.qty_received = 0.0
                continue
            if line.product_id.type not in ['consu', 'product']:
                line.qty_received = line.product_qty
                continue
            total = 0.0
            returns = line.move_ids.filtered(lambda x: x.origin_returned_move_id)
            for move in line.move_ids - returns:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total += move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total += move.product_uom_qty

            for move in returns:
                if move.state == 'done':
                    if move.product_uom != line.product_uom:
                        total -= move.product_uom._compute_quantity(move.product_uom_qty, line.product_uom)
                    else:
                        total -= move.product_uom_qty
            line.qty_received = total

    @api.multi
    def show_line_info(self):
        #Comentado por si no vale la solucion
        #view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            #'views': [(view_id, 'form')],
            #'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }


class PurchaseOrder(models.Model):

    _inherit = 'purchase.order'

    order_volume = fields.Float("Volume", compute="_compute_dimensions")
    order_weight = fields.Float("Weight", compute="_compute_dimensions")
    expediente = fields.Char("Expediente")


    @api.depends('order_line.line_volume', 'order_line.line_weight')
    def _compute_dimensions(self):
        for order in self:
            order_volume = 0.00
            order_weight = 0.00
            for line in order.order_line:
                order_volume += line.line_volume
                order_weight += line.line_weight
            order.update({
                'order_volume': order_volume,
                'order_weight': order_weight,
            })

    @api.multi
    def show_line_info(self):
        view_id = self.env.ref('jim_purchase.purchase_order_form_line_info').id

        return {
            'name': _('Show info line Details'),
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'purchase.order.line',
            'views': [(view_id, 'form')],
            'view_id': view_id,
            'target': 'new',
            'res_id': self.ids[0],
            'context': self.env.context
        }

    @api.multi
    def _add_supplier_to_product(self):
        res = super(PurchaseOrder, self)._add_supplier_to_product()
        for line in self.order_line:
            partner = self.partner_id if not self.partner_id.parent_id else \
                self.partner_id.parent_id
            if line.product_id.seller_ids.filtered(lambda x: x.name == partner):
                seller_id = line.product_id.seller_ids.filtered(lambda x: x.name == partner)
                currency = partner.property_purchase_currency_id or self.env.user.company_id.currency_id

                try:
                    seller_id.write({'price': self.currency_id.compute(line.price_unit, currency)})
                except AccessError:  # no write access rights -> just ignore
                    break

class AccountInvoice(models.Model):

    _inherit = 'account.invoice'

    def action_add_purchase_invoice_wzd(self):

        if not self:
            return
        if not self.id:
            return
        if not self.partner_id:
            return
        ctx = dict(self._context.copy())
        ctx.update({'partner_id': self.partner_id.id})
        wizard_obj = self.env['purchase.invoice.wzd'].with_context(ctx)
        res_id = wizard_obj.create({'partner_id': self.partner_id.id,
                                    'account_invoice_id': self.id})
        return {
            'name': wizard_obj._description,
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': wizard_obj._name,
            'domain': [],
            'context': ctx,
            'type': 'ir.actions.act_window',
            'target': 'new',
            'res_id': res_id.id,
            'nodestroy': True,
        }

    @api.one
    def compute_amount(self):
        self._compute_amount()