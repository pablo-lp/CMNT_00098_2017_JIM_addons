#!/usr/bin/env python
# -*- coding: utf-8 -*-

import sys
import xmlrpclib
import socket

class FixTemplateProduct(object):
    def __init__(self, dbname, user, passwd, port):
        """método incial"""

        try:
            self.url_template = "http://%s:%s/xmlrpc/%s"
            self.server = "localhost"
            self.port = int(port)
            self.dbname = dbname
            self.user_name = user
            self.user_passwd = passwd

            #
            # Conectamos con OpenERP
            #
            login_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'common'))
            self.user_id = login_facade.login(self.dbname, self.user_name, self.user_passwd)
            self.object_facade = xmlrpclib.ServerProxy(self.url_template % (self.server, self.port, 'object'))

            res = self.fix_templates()
            #con exito
            if res:
                print ("All set")
        except Exception, e:
            print ("ERROR: ", (e))
            sys.exit(1)

        #Métodos Xml-rpc

    def exception_handler(self, exception):
        """Manejador de Excepciones"""
        print "HANDLER: ", (exception)
        return True

    def create(self, model, data, context={}):
        """
        Wrapper del metodo create.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                            model, 'create', data, context)
            return res
        except socket.error, err:
            raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en create: %s' % (err.faultCode, err.faultString))


    def search(self, model, query, offset=0, limit=False, order=False, context={}, count=False, obj=1):
        """
        Wrapper del metodo search.
        """
        try:
            ids = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                    model, 'search', query, offset, limit, order, context, count)
            return ids
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en search: %s' % (err.faultCode, err.faultString))


    def read(self, model, ids, fields, context={}):
        """
        Wrapper del metodo read.
        """
        try:
            data = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                            model, 'read', ids, fields, context)
            return data
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en read: %s' % (err.faultCode, err.faultString))


    def write(self, model, ids, field_values,context={}):
        """
        Wrapper del metodo write.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'write', ids, field_values, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception(u'Error %s en write: %s' % (err.faultCode, err.faultString))


    def unlink(self, model, ids, context={}):
        """
        Wrapper del metodo unlink.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                    model, 'unlink', ids, context)
            return res
        except socket.error, err:
                raise Exception(u'Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                    raise Exception(u'Error %s en unlink: %s' % (err.faultCode, err.faultString))

    def default_get(self, model, fields_list=[], context={}):
        """
        Wrapper del metodo default_get.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                        model, 'default_get', fields_list, context)
            return res
        except socket.error, err:
                raise Exception('Conexion rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en default_get: %s' % (err.faultCode, err.faultString))

    def execute(self, model, method, *args, **kw):
        """
        Wrapper del método execute.
        """
        try:
            res = self.object_facade.execute(self.dbname, self.user_id, self.user_passwd,
                                                                model, method, *args, **kw)
            return res
        except socket.error, err:
                raise Exception('Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
                raise Exception('Error %s en execute: %s' % (err.faultCode, err.faultString))

    def exec_workflow(self, model, signal, ids):
        """ejecuta un workflow por xml rpc"""
        try:
            res = self.object_facade.exec_workflow(self.dbname, self.user_id, self.user_passwd, model, signal, ids)
            return res
        except socket.error, err:
            raise Exception(u'Conexión rechazada: %s!' % err)
        except xmlrpclib.Fault, err:
            raise Exception(u'Error %s en exec_workflow: %s' % (err.faultCode, err.faultString))


    def fix_templates(self):
        template_ids = self.search('product.template', [('attribute_line_ids', '!=', [])])
        print "templates no: ", len(template_ids)
        cont = 1
        for templ_id in template_ids:
            tmpl_data = self.read("product.template", templ_id, ['attribute_line_ids', 'product_variant_ids', 'name'])
            templ_attributes = {}
            att_data = self.read('product.attribute.line',
                                 tmpl_data[0]['attribute_line_ids'],
                                ['attribute_id', 'value_ids'])
            for att in att_data:
                if not templ_attributes.get(att['attribute_id']):
                    templ_attributes[att['attribute_id']] = [att['value_ids'], att['id']]
            try:
                for prod in tmpl_data[0]['product_variant_ids']:
                    prod_data = self.read('product.product', prod, ['attribute_value_ids'])
                    if not prod_data[0]['attribute_value_ids']:
                        if len(tmpl_data[0]['product_variant_ids']) > 1:
                            self.unlink('product.product', prod)
                    else:
                        for val in prod_data[0]['attribute_value_ids']:
                            att_data = self.read('product.attribute.value',
                                                 val, ['attribute_id'])
                            if att_data[0]['attribute_id'] in templ_attributes and val not in templ_attributes[att_data[0]['attribute_id']][0]:
                                templ_attributes[att_data[0]['attribute_id']][0].append(val)

                for att in templ_attributes:
                    self.write('product.attribute.line',
                               templ_attributes[att][1],
                               {'value_ids':
                                [(6, 0, templ_attributes[att][0])]})

                print "%s de %s" % (cont, len(template_ids))
                cont += 1
            except Exception, e:
                print "EXCEPTION: Prod:", tmpl_data[0]['name'], repr(e)
                raise e

        return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print u"Uso: %s <dbname> <user> <password> <port>" % sys.argv[0]
    else:
        FixTemplateProduct(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
