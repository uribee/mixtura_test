# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
from dataclasses import field
import json
from operator import mod
import requests
import logging
import time
from datetime import datetime, timedelta,date
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
_logger = logging.getLogger(__name__)


#Sucursales
class sucursales_sucursal(models.Model):
    _inherit= ['odoosv.caja']
    pos_config_id=fields.Many2one(comodel_name='pos.config', string="Punto de Venta")


class sucursales_pos_order(models.Model):
    _inherit=['pos.order']
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")

class sucursales_pos_payment(models.Model):
    _inherit=['pos.payment']
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")
    




    
#Cierre
class sucursales_cierre_pos(models.Model):
    _inherit= ['odoosv.cierre']
    
    pos_order_ids=fields.One2many(comodel_name='pos.order',inverse_name='cierre_id',string="Ticket Pos")
    pos_payment_ids=fields.One2many(comodel_name='pos.payment',inverse_name='cierre_id',string="Pagos Pos")
    
    def liberar(self):
        super(sucursales_cierre_pos,self).liberar()
        for record in self:
            orders=self.env['pos.order'].search([('cierre_id','=',record.id)])
            for factura in orders:
                factura.write({'cierre_id':False})
            pagos=self.env['pos.payment'].search([('cierre_id','=',record.id)])
            for pago in pagos:
                pago.write({'cierre_id':False})
           

    def calcular(self):
        super(sucursales_cierre_pos,self).calcular()
        for record in self:
            
            current=record.fecha_cierre
            dia=int(datetime.strftime(current, '%d'))
            mes=int(datetime.strftime(current, '%m'))
            anio=int(datetime.strftime(current, '%Y'))
           
            orders=self.env['pos.order'].search([('cierre_id','=',record.id)])
            for factura in orders:
                factura.write({'cierre_id':False})
            pagos=self.env['pos.payment'].search([('cierre_id','=',record.id)])
            for pago in pagos:
                pago.write({'cierre_id':False})


            efectivo_inicial=record.efectivo_inicial
            efectivo_ingresado=record.efectivo_ingresado
            efectivo_egresado=record.efectivo_egresado
            efectivo_final=record.efectivo_final

            hoy_1=datetime(anio,mes,dia,0,0,1)
            hoy_2=datetime(anio,mes,dia,23,59,59)
            hoy_1=hoy_1+timedelta(hours=6)
            hoy_2=hoy_2+timedelta(hours=6)


            #facturas=env['account.move'].search([('invoice_date','>=',hoy_1),('invoice_date','<=',hoy_2),('type','=','out_invoice'),('state','!=','draft'),('state','!=','cancel')])
            ordenes=self.env['pos.order'].search([('date_order','>=',hoy_1),('date_order','<=',hoy_2),('config_id','=',record.caja_id.pos_config_id.id),('state','in',['paid','done'])])
            print("------------------------------------------------*****")
            print(str(record.caja_id.pos_config_id.id))
            print("------------------------------------------------*****")
            for orden in ordenes:
                if not ordenes.cierre_id:
                    ordenes.write({'cierre_id':record.id})

            #pagos=env['account.payment'].search([('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('payment_type','=','inbound'),('state','!=','draft'),('state','!=','cancelled')])
            pagos=self.env['pos.payment'].search([('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('pos_order_id.config_id','=',record.caja_id.pos_config_id.id)])
            for pago in pagos:
                if not pago.cierre_id:
                    pago.write({'cierre_id':record.id})
                    if pago.payment_method_id.journal_id.type=='cash':
                        efectivo_ingresado+=pago.amount

            
            


            pagos_agrupagos=self.env['pos.payment'].read_group([('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('pos_order_id.config_id','=',record.caja_id.pos_config_id.id)],['payment_method_id.id','total:sum(amount)'],['payment_method_id'])
            print('__________________________________________________')            
            print(str(pagos_agrupagos))
            print('____________________________________________')
            for pg in  pagos_agrupagos:
                ppm=self.env['pos.payment.method'].browse(pg['payment_method_id'][0])
                j=self.env['account.journal'].browse(ppm.journal_id.id)
                if ppm:
                    if pg['total']:
                        encontrado=False
                        for d in record.cierrepago_ids:
                            if ppm.journal_id.id==d.journal_id.id:
                                encontrado=True
                                d.monto+=pg[total]
                        if not encontrado:
                            self.env['odoosv.cierre.pago'].create({'name':j.name,'cierre_id':record.id,'journal_id':j.id,'monto':pg['total']})
                        



            groups=self.env['pos.order'].read_group([('date_order','>=',hoy_1),('date_order','<=',hoy_2),('config_id','=',record.caja_id.pos_config_id.id),('state','in',['paid','done'])],['min_doc:min(pos_reference)','max_doc:max(pos_reference)','count_doc:count(pos_reference)','total:sum(amount_total)'],[])
           
            print('__________________________________________________')            
            print(str(groups))
            print('___________________________________________________')            
            for r in groups:       
                if r['total']:         
                    doc={}
                    doc['name']='Ticket'
                    doc['min_doc']=r['min_doc']
                    doc['max_doc']=r['max_doc']
                    doc['cantidad']=r['count_doc']
                    doc['cierre_id']=record.id
                    doc['total']=r['total']
                    ##exento
                    exentos=self.env['account.tax'].search([('tax_group_id.code','=','Exento')])
                    tax=[]
                    for e in exentos:
                        tax.append(e.id)
                    group=self.env['pos.order.line'].read_group([('order_id.date_order','>=',hoy_1),('order_id.date_order','<=',hoy_2),('order_id.config_id','=',record.caja_id.pos_config_id.id),('order_id.state','in',['paid','done'])],['total:sum(price_subtotal_incl)'],[])
                    exento=0
                    print(str(group))
                    if group:
                        for g in group:
                            if g['total']:
                                exento+=g['total']
                    doc['exento']=exento

                    ##nosjuejo
                    nosujeto=self.env['account.tax'].search([('tax_group_id.code','=','	No Sujeto')])
                    tax=[]
                    for e in nosujeto:
                        tax.append(e.id)
                    group=self.env['pos.order.line'].read_group([('order_id.date_order','>=',hoy_1),('order_id.date_order','<=',hoy_2),('order_id.config_id','=',record.caja_id.pos_config_id.id),('order_id.state','in',['paid','done'])],['total:sum(price_subtotal_incl)'],[])
                    
                    nosujeto=0
                    print(str(group))
                    if group:
                        for g in group:
                            if g['total']:
                                nosujeto+=g['total']
                    doc['nosujeto']=nosujeto

                    doc['gravado']=r['total']-exento-nosujeto
                    self.env['odoosv.cierre.documento'].create(doc)
            
           

            record.efectivo_inicial=efectivo_inicial
            record.efectivo_ingresado=efectivo_ingresado
            record.efectivo_egresado=efectivo_egresado
            record.efectivo_final=efectivo_final
            record.efectivo_diferencia=efectivo_final-(efectivo_inicial+efectivo_ingresado-efectivo_egresado)
    


    
