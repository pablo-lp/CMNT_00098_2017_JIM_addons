# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, models, fields, _


class WizardValuationHistory(models.TransientModel):
    _name = 'wzd.product.web'


    web_visible = fields.Selection([('yes', 'Visible'), ('no', 'No visible'), ('all', 'Todos')], string ="Visible en web", default='all')
    stock_available = fields.Selection([('yes', 'Disponible'), ('no', 'No disponible'), ('all', 'Todos')], string ="Available stock", default='all')
    search_text = fields.Char("Search text")
    offset = fields.Integer("Start", default=0)
    limit = fields.Integer("Limit", default=0)

    @api.multi
    def open_product_web_report(self):
        self.ensure_one()
        domain = [('type', '!=', 'service')]
        offset = 0
        limit = 50000
        if self.web_visible == 'yes':
            domain.append(['web','=',True])
        elif self.web_visible == 'no':
            domain.append(['web', '=', False])

        if self.stock_available == 'yes':
            domain.append(['web_global_stock', '>', 0])
        elif self.stock_available == 'no':
            domain.append(['web_global_stock', '<=', 0])

        if self.search_text:
            domain.append(['tag_names', 'ilike', self.search_text])
            domain.append(['display_name', 'ilike', self.search_text])

        if self.offset:
            offset = self.offset
        if self.limit:
            limit = self.limit
        else:
            limit = self.env['product.product'].search(domain, count=True)

        fields = ('display_name', 'default_code', 'tag_names', 'web', 'web_global_stock')
        read = []
        inc = 250
        print "Numero de registros a exportar: %s\nBuscando ..."%limit
        while offset <= limit:
            print "Recuperando %s de %s"%(offset, limit)
            read.extend(self.env['product.product'].search_read(domain, fields, offset=offset, limit=inc))
            offset += inc
        print "Generando XLS ..."
        #product['ids'] = self.env['product.product'].search(domain).ids

        return {'type': 'ir.actions.report.xml',
                'report_name': 'product_web_xls',
                'datas': {'form': read}}