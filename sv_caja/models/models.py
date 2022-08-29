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
    _name='odoosv.caja'
    _description='Definicion de caja'
    _inherit= ['mail.thread']
    name=fields.Char('Caja')
    location_id=fields.Many2one(comodel_name='stock.location', string="Ubicacion")
    warehouse_id=fields.Many2one(comodel_name='stock.warehouse', string="Almacen")
    picking_type_id=fields.Many2one(comodel_name='stock.picking.type', string="Transferencia de cliente")
    analytic_account_id=fields.Many2one(comodel_name='account.analytic.account', string="Cuenta analitica")
    serie_ids=fields.One2many(comodel_name='odoosv.serie',inverse_name='caja_id',string="Series")
    header=fields.Text("Header")
    footer=fields.Text("Footer")
    


class sucursales_series(models.Model):
    _name='odoosv.serie'
    _description='Series por documento'
    name=fields.Char('tipo documento')
    tipo_documento_id=fields.Many2one('odoosv.fiscal.document',string="Tipo de Documento",ondelete="restrict")
    sv_sequence_id=fields.Many2one('ir.sequence',string="Numeracion",ondelete="restrict")
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja")
    serie=fields.Char('Serie')

    
class sucursales_user(models.Model):
    _inherit='res.users'
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja")
    caja_ids=fields.Many2many(comodel_name='odoosv.caja',string="Rutass")

    
    
class sucursales_sale_order(models.Model):
    _inherit='sale.order'
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja",default=lambda self: self.env.user.caja_id)
    able_to_modify_caja = fields.Boolean(compute='set_access_for_caja', string='puede modificar caja')

    def set_access_for_caja(self):
        self.ensure_one()
        self.able_to_modify_caja = self.env['res.users'].has_group('sv_caja.odoosv_cambia_caja')

    @api.onchange('caja_id')
    def get_warehouse_id(self):
        for r in self:
            if r.caja_id:
                if r.caja_id.warehouse_id:
                    r.warehouse_id=r.caja_id.warehouse_id.id
    
class sucursales_account_move(models.Model):
    _inherit='account.move'
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja", default=lambda self: self.env.user.caja_id)
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")
    serie=fields.Char('Serie')
    
    
    def _fecha_actual(self):
        fecha_actual = fields.Date.context_today(self)
        return  fecha_actual

    invoice_date = fields.Date( string="obtener fecha actual", default=_fecha_actual)
    
    def set_access_for_caja(self):
        self.ensure_one()
        self.able_to_modify_caja = self.env['res.users'].has_group('sv_caja.odoosv_cambia_caja')

    able_to_modify_caja = fields.Boolean(compute=set_access_for_caja, string='puede modificar caja')

class sucursales_account_move_line(models.Model):
    _inherit='account.move.line'
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja", related='move_id.caja_id',store=True)


    def set_analityc(self):
        for r in self:
            if not r.analytic_account_id:
                if r.caja_id:
                    if r.caja_id.analytic_account_id:
                        r.analytic_account_id=r.caja_id.analytic_account_id.id

class sucursales_account_payment(models.Model):
    _inherit='account.payment'
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja", default=lambda self: self.env.user.caja_id)
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")
    facturas=fields.Char("Facturas",compute='calcular_facturas',store=False)


    def calcular_facturas(self):
        for r in self:
            text=''
            for l in r.reconciled_invoice_ids:
                if l.tipo_documento_id:
                    text=text+' '+l.tipo_documento_id.name
                    if l.doc_numero:
                        text=text+':'+l.doc_numero+ '  '
            r.facturas=text
        
    def set_access_for_caja(self):
        self.ensure_one()
        self.able_to_modify_caja = self.env['res.users'].has_group('sv_caja.odoosv_cambia_caja')

    able_to_modify_caja = fields.Boolean(compute=set_access_for_caja, string='puede modificar caja')
    

    
#Cierre
class sucursales_cierre(models.Model):
    _name='odoosv.cierre'
    _description='Cierre'
    _inherit= ['mail.thread']
    name=fields.Char("Cierre de Caja", compute='compute_nombre')
    caja_id=fields.Many2one(comodel_name='odoosv.caja', string="Caja", default=lambda self: self.env.user.caja_id)
    comentario=fields.Text("Comentario")
    total_facturado=fields.Float("Total Facturado")
    total_pagado=fields.Float("Total Pagado")
    inicio=fields.Datetime("Hora de inicio")
    final=fields.Datetime("Hora de apertura")
    cierrepago_ids=fields.One2many(comodel_name='odoosv.cierre.pago',inverse_name='cierre_id',string="Formas de pago")
    factura_ids=fields.One2many(comodel_name='account.move',inverse_name='cierre_id',string="Facturas")
    pago_ids=fields.One2many(comodel_name='account.payment',inverse_name='cierre_id',string="Pagos")
    documento_ids=fields.One2many(comodel_name='odoosv.cierre.documento',inverse_name='cierre_id',string="Documentos")
    line_ids = fields.One2many(comodel_name='odoosv.cierre.linea', inverse_name='cierre_id')
    remesa_ids=fields.One2many(comodel_name='odoosv.cierre.remesa',inverse_name='cierre_id',string="Remesas")
    estado=fields.Selection(selection=[('Creado', 'Creado')
                                    ,('Confirmado', 'Confirmado')]
                                    , string='Estado',required=True,default='Creado')
    able_to_modify_caja = fields.Boolean(compute='set_access_for_caja', string='puede modificar caja')
    fecha_cierre = fields.Date(required=True, default=lambda self: fields.datetime.now())

    apertura_id=fields.Many2one(comodel_name='odoosv.apertura.caja', string="Apertura")

    efectivo_inicial=fields.Float("Efectivo inicial")
    efectivo_ingresado=fields.Float("Efectivo Ingresado")
    efectivo_egresado=fields.Float("Efectivo Egresado")
    efectivo_final=fields.Float("Efectivo Final")
    efectivo_diferencia=fields.Float("Diferencia")

    @api.depends('fecha_cierre','caja_id')
    def compute_nombre(self):
        for r in self:
            name=''
            if r.fecha_cierre:
                name=str(r.fecha_cierre)[0:10]+' '
            name += r.caja_id.name if r.caja_id else ''
            r.name = name

    #campo de filtrar caja
    def set_access_for_caja(self):
        self.ensure_one()
        self.able_to_modify_caja = self.env['res.users'].has_group('sv_caja.odoosv_cambia_caja')
    
    def liberar(self):
        for record in self:
            facturas=self.env['account.move'].search([('cierre_id','=',record.id)])
            for factura in facturas:
                factura.write({'cierre_id':False})
            pagos=self.env['account.payment'].search([('cierre_id','=',record.id)])
            for pago in pagos:
                pago.write({'cierre_id':False})
            cierres=self.env['odoosv.cierre.pago'].search([('cierre_id','=',record.id)])
            for cierre in cierres:
                cierre.unlink()
            record.write({'total_facturado':0})
            record.write({'total_pagado':0})
    
    def cerrar(self):
        for record in self:
            record.write({'estado':'Confirmado'})
            
    
    def calcular(self):
        for record in self:
            
            current=record.fecha_cierre
            dia=int(datetime.strftime(current, '%d'))
            mes=int(datetime.strftime(current, '%m'))
            anio=int(datetime.strftime(current, '%Y'))
            #resetenado los valores
            total_facturado=0
            total_pagado=0
            cash_sacado=0
            #liberando
            facturas=self.env['account.move'].search([('cierre_id','=',record.id)])
            for factura in facturas:
                factura.write({'cierre_id':False})
            pagos=self.env['account.payment'].search([('cierre_id','=',record.id)])
            for pago in pagos:
                pago.write({'cierre_id':False})
            cierres=self.env['odoosv.cierre.pago'].search([('cierre_id','=',record.id)])
            for cierre in cierres:
                cierre.unlink()
            remesas=self.env['odoosv.cierre.remesa'].search([('cierre_id','=',record.id)])
            for remesa in remesas:
                remesa.unlink()
            documentos=self.env['odoosv.cierre.documento'].search([('cierre_id','=',record.id)])
            for documento in documentos:
                documento.unlink()
            
            efectivo_inicial=0.0
            efectivo_ingresado=0.0
            efectivo_egresado=0.0
            efectivo_final=0.0



            
            #listando las ordenes de este diari
            hoy_1=datetime(anio,mes,dia,0,0,1)
            hoy_2=datetime(anio,mes,dia,23,59,59)
            hoy_1=hoy_1+timedelta(hours=6)
            hoy_2=hoy_2+timedelta(hours=6)


            #apertura de caja
            apertura=self.env['odoosv.apertura.caja'].search([('caja_id','=',record.caja_id.id),('fecha_apertura','=',current)],limit=1)
            if apertura:
                record.apertura_id=apertura.id
                efectivo_inicial=apertura.total

            #facturas=env['account.move'].search([('invoice_date','>=',hoy_1),('invoice_date','<=',hoy_2),('type','=','out_invoice'),('state','!=','draft'),('state','!=','cancel')])
            facturas=self.env['account.move'].search([('invoice_date','=',current),('caja_id','=',record.caja_id.id),('move_type','in',['out_invoice','out_refund']),('state','!=','draft'),('state','!=','cancel')])
            for factura in facturas:
                if not factura.cierre_id:
                    factura.write({'cierre_id':record.id})
                    total_facturado=total_facturado+factura.amount_total
            #pagos=env['account.payment'].search([('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('payment_type','=','inbound'),('state','!=','draft'),('state','!=','cancelled')])
            pagos=self.env['account.payment'].search([('date','=',current),('caja_id','=',record.caja_id.id),('payment_type','=','inbound'),('state','!=','draft'),('state','!=','cancelled')])
            for pago in pagos:
                if not pago.cierre_id:
                    pago.write({'cierre_id':record.id})
                    total_pagado=total_pagado+pago.amount
                    if pago.journal_id.type=='cash':
                        efectivo_ingresado+=pago.amount
            #pagos2=env['account.payment'].search(['&',('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('payment_type','=','outbound'),('state','!=','draft'),('state','!=','cancelled')])
            pagos2=self.env['account.payment'].search([('date','=',current),('caja_id','=',record.caja_id.id),('payment_type','=','outbound'),('state','!=','draft'),('state','!=','cancelled')])
            for pago in pagos2:
                if not pago.cierre_id:
                    if pago.journal_id.type=='cash':
                        pago.write({'cierre_id':record.id})
                        total_pagado=total_pagado-pago.amount
                        cash_sacado=cash_sacado+pago.amount
                        efectivo_egresado+=pago.amount
            #remesas=env['account.payment'].search(['&',('payment_date','>=',hoy_1),('payment_date','<=',hoy_2),('payment_type','=','transfer'),('state','!=','draft'),('state','!=','cancelled')])
            remesas=self.env['account.payment'].search([('date','=',current),('caja_id','=',record.caja_id.id),('payment_type','=','transfer'),('state','!=','draft'),('state','!=','cancelled')])
            for remesa in remesas:
                dic={}
                dic['origen']=remesa.journal_id.id
                dic['destino']=remesa.destination_journal_id.id
                dic['monto']=remesa.amount
                dic['cierre_id']=record.id
                env['odoosv.cierre.remesa'].create(dic)
                if remesa.journal_id.type=='cash':
                    efectivo_egresado+=remesa.amount
                if remesa.destination_journal_id.type=='cash':
                    efectivo_ingresado+=remesa.amount
            diarios=self.env['account.journal'].search([('id','>',0)])
            for diario in diarios:
                total_diario=0.0
                pagos3=self.env['account.payment'].search(['&',('cierre_id','=',record.id),('payment_type','=','inbound'),('journal_id','=',diario.id)])
                for pago2 in pagos3:
                    total_diario=total_diario+pago2.amount
                #if diario.type=='cash':
                #  pagos4=env['account.payment'].search(['&',('cierre_id','=',record.id),('payment_type','=','outbound'),('journal_id','=',diario.id)])
                #  for pago2 in pagos4:
                #    total_diario=total_diario-pago2.amount
                if total_diario!=0:
                    self.env['odoosv.cierre.pago'].create({'name':diario.name,'cierre_id':record.id,'journal_id':diario.id,'monto':total_diario})
                    #raise ValidationError("hay ordenes: %s" %total_venta)
            groups=self.env['account.move'].read_group([('invoice_date','=',current),('caja_id','=',record.caja_id.id),('move_type','in',['out_invoice','out_refund']),('state','!=','draft'),('state','!=','cancel')],['tipo_documento_id.name','min_doc:min(doc_numero)','max_doc:max(doc_numero)','count_doc:count(doc_numero)','total:sum(amount_total_signed)'],['tipo_documento_id'])
            #query='''
            #    select d.name, min(m.doc_numero) as minimo, max(m.doc_numero) as maximo,count(m.id) as cantidad
            #    from odoosv_fiscal_document d 
            #    inner join account_move m on m.tipo_documento_id=d.id
            #    where m.move_type in ('out_invoice','out_refund') 
            #        and m.state<>'draft'
            #        and m.cierre_id='''+str(record.id)+'''
            #    group by d.name;
            #'''
            #print(query)
            print('__________________________________________________')            
            #self._cr.execute(query)
            #query_results = self._cr.dictfetchall()
            print(str(groups))
            print('___________________________________________________')            
            #print(str(query_results))
            for r in groups:                
                doc={}
                tipo=self.env['odoosv.fiscal.document'].browse(r['tipo_documento_id'][0])
                
                doc['name']=tipo.codigo if tipo.codigo else tipo.name
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
                group=self.env['account.move.line'].read_group([('move_id.invoice_date','=',current),('move_id.caja_id','=',record.caja_id.id),('move_id.move_type','in',['out_invoice','out_refund']),('move_id.state','!=','draft'),('move_id.state','!=','cancel'),('move_id.tipo_documento_id','=',tipo.id),('exclude_from_invoice_tab','=',False),('tax_ids','in',tax)],['total:sum(price_total)'],[])
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
                group=self.env['account.move.line'].read_group([('move_id.invoice_date','=',current),('move_id.caja_id','=',record.caja_id.id),('move_id.move_type','in',['out_invoice','out_refund']),('move_id.state','!=','draft'),('move_id.state','!=','cancel'),('move_id.tipo_documento_id','=',tipo.id),('exclude_from_invoice_tab','=',False),('tax_ids','in',tax)],['total:sum(price_total)'],[])
                nosujeto=0
                print(str(group))
                if group:
                    for g in group:
                        if g['total']:
                            nosujeto+=g['total']
                doc['nosujeto']=nosujeto

                doc['gravado']=r['total']-exento-nosujeto
                self.env['odoosv.cierre.documento'].create(doc)
            
            #total del monto
            for l in record.line_ids:
                efectivo_final+=l.valor
            

            record.efectivo_inicial=efectivo_inicial
            record.efectivo_ingresado=efectivo_ingresado
            record.efectivo_egresado=efectivo_egresado
            record.efectivo_final=efectivo_final
            record.efectivo_diferencia=efectivo_final-(efectivo_inicial+efectivo_ingresado-efectivo_egresado)
            record.write({'total_facturado':total_facturado,'total_pagado':total_pagado,'inicio':hoy_1,'final':hoy_2})
    

class sucursales_cierre_pago(models.Model):
    _name='odoosv.cierre.pago'
    _description='Pagos en el cierre'
    name=fields.Char("Cierre")
    monto=fields.Float("Monto")
    journal_id=fields.Many2one(comodel_name='account.journal', string="Metodo de pago")
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")

class sucursales_cierre_documento(models.Model):
    _name='odoosv.cierre.documento'
    _description='Pagos en el cierre'
    name=fields.Char("Documento")
    cantidad=fields.Integer("Cantidad")
    min_doc=fields.Char("Doc. Inicial")
    max_doc=fields.Char("Doc. Final")
    gravado=fields.Float("Gravado")
    exento=fields.Float("Exento")
    nosujeto=fields.Float("No Sujeto")
    total=fields.Float("Total")
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")



class sucursales_cierre_Remesa(models.Model):
    _name='odoosv.cierre.remesa'
    _description='Remesas en el cierre'
    name=fields.Char("Remesa")
    origen_id=fields.Many2one(comodel_name='account.journal', string="Origen")
    destino_id=fields.Many2one(comodel_name='account.journal', string="Destino")
    cierre_id=fields.Many2one(comodel_name='odoosv.cierre', string="Cierre")
    monto=fields.Float("Monto")

class linea_de_apertura_caja(models.Model):
    _name = 'odoosv.aperturacaja.linea'
    _description='Aperturar monedas y billetes de una caja'
    name = fields.Char(string="Líneas de apertura de caja", related='billete_moneda_id.name')
    billete_moneda_id = fields.Many2one(comodel_name="pos.bill", string="Monedas/Billetes")
    cantidad = fields.Integer(string="Cantidad")
    valor = fields.Float(string="Valor", compute='compute_valor')
    apertura_id = fields.Many2one(comodel_name='odoosv.apertura.caja', string='Apertura de Caja')

    @api.depends('billete_moneda_id','cantidad')
    def compute_valor(self):
        for r in self:
            if r.billete_moneda_id:
                r.valor = r.cantidad*r.billete_moneda_id.value
            else:
                r.valor = 0


class linea_de_apertura_caja(models.Model):
    _name = 'odoosv.cierre.linea'
    _description='Aperturar monedas y billetes de una caja'
    name = fields.Char(string="Líneas de apertura de caja", related='billete_moneda_id.name')
    billete_moneda_id = fields.Many2one(comodel_name="pos.bill", string="Monedas/Billetes")
    cantidad = fields.Integer(string="Cantidad")
    valor = fields.Float(string="Valor", compute='compute_valor')
    cierre_id = fields.Many2one(comodel_name='odoosv.cierre', string='Cierre de Caja')

    @api.depends('billete_moneda_id','cantidad')
    def compute_valor(self):
        for r in self:
            if r.billete_moneda_id:
                r.valor = r.cantidad*r.billete_moneda_id.value
            else:
                r.valor = 0

class apertura_caja(models.Model):
    _name = 'odoosv.apertura.caja'
    _description = 'Apertura de Caja'
    _inherit = ['mail.thread']
    name = fields.Char(string='Apertura de Caja', compute='compute_nombre')
    fecha_apertura = fields.Date(string="Fecha de apertura de caja",required=True,readonly=True,select=True, default=lambda self: fields.datetime.now())
    caja_id = fields.Many2one(comodel_name='odoosv.caja', string='Caja',default=lambda self: self.env.user.caja_id)
    line_ids = fields.One2many(comodel_name='odoosv.aperturacaja.linea', inverse_name='apertura_id')
    total = fields.Float(string='Total', compute='compute_total')
    able_to_modify_caja = fields.Boolean(compute='set_access_for_caja', string='puede modificar caja')

    @api.depends('fecha_apertura','caja_id')
    def compute_nombre(self):
        for r in self:
            name=''
            if r.fecha_apertura:
                name=str(r.fecha_apertura)[0:10]+' '
            name += r.caja_id.name if r.caja_id else ''
            r.name = name

    @api.depends('line_ids')
    def compute_total(self):
        for r in self:
            total = 0
            for l in r.line_ids:
                total += l.valor
            r.total = total
    
    def set_access_for_caja(self):
        self.ensure_one()
        self.able_to_modify_caja = self.env['res.users'].has_group('sv_caja.odoosv_cambia_caja')

class pos_config_caja(models.Model):
    _inherit = ['pos.config']
    analytic_account_id = fields.Many2one(comodel_name='account.analytic.account', string="Cuentas analíticas")

class orden_venta_caja(models.Model):
    _inherit = ['sale.order']
    
    @api.model
    def create(self,vals):
        if self.env.user.caja_id:
            vals['analytic_account_id']=self.env.user.caja_id.analytic_account_id.id
        res = super(orden_venta_caja, self).create(vals)
        return res

class relacion_caja_tipo_documento(models.Model):
    _inherit = ['odoosv.fiscal.document']

    caja_id = fields.Many2one(
        string='Caja',
        comodel_name='odoosv.caja'
    )

class relacion_caja_diario(models.Model):
    _inherit = ['account.journal']

    caja_id = fields.Many2one(
        string='Caja',
        comodel_name='odoosv.caja'
    )
    
    
