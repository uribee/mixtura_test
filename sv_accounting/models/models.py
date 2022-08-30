# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import json
import requests
import logging
import time
from datetime import datetime, timedelta
from functools import partial
from itertools import groupby
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


    
class odoofiscalsv_prodcut(models.Model):
    _inherit='product.template'
    fiscal_type=fields.Selection(selection=[('Servicio','Servicio'),('Tangible','Tangible')],string="Tipo Fiscal del producto")
    bloquear_costo=fields.Boolean("Bloquear venta por debajo del costo")


class odoofiscalsv_taxgroup(models.Model):
    _inherit='account.tax.group'
    code=fields.Char("Codigo")
    company_id=fields.Many2one('res.company',string="Company")

class odoosv_user(models.Model):
    _inherit='res.company'

    sv=fields.Boolean("Localizacion de El Salvador")

    contador=fields.Char("Contador")
    dividir_facturas=fields.Boolean("Dividir facturas")
    lineas_factura=fields.Integer("Lineas por factura")
    
    #Cuentas
    account_iva_consumidor_id=fields.Many2one('account.account',string="Cuenta de IVA consumidor (Venta)")
    account_iva_contribuyente_id=fields.Many2one('account.account',string="Cuenta de IVA contribuyente (Venta)")
    account_iva_compras_id=fields.Many2one('account.account',string="Cuenta de IVA Compras (Compra)")
    account_retencion_id=fields.Many2one('account.account',string="Cuenta de Retencion (Venta)")
    account_perceccion_id=fields.Many2one('account.account',string="Cuenta de Perseccion (Compras)")
    account_isr_id=fields.Many2one('account.account',string="Cuenta de ISR (Compras)")

    #impuestos
    tax_iva_consumidor_id=fields.Many2one('account.tax',string="Impuesto de IVA consumidor (Venta)")
    tax_iva_contribuyente_id=fields.Many2one('account.tax',string="Impuesto de IVA contribuyente (Venta)")
    tax_iva_compras_id=fields.Many2one('account.tax',string="Impuesto de IVA Compras (Compra)")
    tax_retencion_id=fields.Many2one('account.tax',string="Impuesto de Retencion (Venta)")
    tax_perceccion_id=fields.Many2one('account.tax',string="Impuesto de Perseccion (Compras)")
    tax_isr_id=fields.Many2one('account.tax',string="Impuesto de ISR (Compras)")
    tax_exento_compra_id=fields.Many2one('account.tax',string="Impuesto de Exento (Compra)")
    tax_exento_venta_id=fields.Many2one('account.tax',string="Impuesto de Exento (Venta)")
    tax_nosujeto_compra_id=fields.Many2one('account.tax',string="Impuesto No Sujeto (Compras)")
    tax_nosujeto_venta_id=fields.Many2one('account.tax',string="Impuesto No Sujeto (Venta)")
    tax_base_tangible_compra=fields.Many2one('account.tax',string="Impuesto de base tangible (Compra)")
    tax_base_tangible_venta=fields.Many2one('account.tax',string="Impuesto de base tangible (Venta)")
    tax_base_servicio_compra=fields.Many2one('account.tax',string="Impuesto de base servicio (Compra)")
    tax_base_servicio_venta=fields.Many2one('account.tax',string="Impuesto de base servicio (Venta)")

    #grupos de impuestos
    tax_group_iva_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos IVA")
    tax_group_retencion_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos Retencion")
    tax_group_persecion_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos Precepcion")
    tax_group_isr_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos ISR")
    tax_group_exento_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos Exento")
    tax_group_nosujeto_id=fields.Many2one('account.tax.group',string=" Grupo de impuestos No Sujeto")

    #posiciones fiscales
    fiscal_position_no_contribuyente_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal no contribuyente")
    fiscal_position_pyme_natural_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal pyme natural")
    fiscal_position_pyme_juridico_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal pyme juridico")
    fiscal_position_grande_natural_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal grande natural")
    fiscal_position_grande_juridico_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal grande juridico")
    fiscal_position_exento_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal exento")
    fiscal_position_extrangero_id=fields.Many2one('account.fiscal.position',string="Posicion fiscal extranjero")

    #formatos de reportes
    formato_ccf=fields.Char("formato de CCF")
    formato_factura=fields.Char("formato de Factura")
    formato_exportacion=fields.Char("formato de Exportacion")
    formato_notacredito=fields.Char("formato de Nota de Credito")


    def create_tax_groups(self):
        for r in self:
            if not r.tax_group_iva_id:
                g=self.env['account.tax.group'].create({'name':'IVA'+'-'+r.name,'code':'iva','company_id':r.id})
                r.tax_group_iva_id=g.id
            if not r.tax_group_retencion_id:
                g=self.env['account.tax.group'].create({'name':'Retencion'+'-'+r.name,'code':'retencion','company_id':r.id})
                r.tax_group_retencion_id=g.id
            if not r.tax_group_persecion_id:
                g=self.env['account.tax.group'].create({'name':'Percepcion'+'-'+r.name,'code':'Percepcion','company_id':r.id})
                r.tax_group_persecion_id=g.id
            if not r.tax_group_isr_id:
                g=self.env['account.tax.group'].create({'name':'ISR'+'-'+r.name,'code':'ISR','company_id':r.id})
                r.tax_group_isr_id=g.id
            if not r.tax_group_exento_id:
                g=self.env['account.tax.group'].create({'name':'Exento'+'-'+r.name,'code':'Exento','company_id':r.id})
                r.tax_group_exento_id=g.id
            if not r.tax_group_nosujeto_id:
                g=self.env['account.tax.group'].create({'name':'No Sujeto'+'-'+r.name,'code':'No Sujeto','company_id':r.id})
                r.tax_group_nosujeto_id=g.id

    def create_tax(self):
        for r in self:
            #Iva Consumidor            
            dic={}
            dic['name']='IVA Consumidor.'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=13
            dic['description']='Iva'
            dic['tax_group_id']=r.tax_group_iva_id.id
            dic['company_id']=r.id
            tax=r.tax_iva_consumidor_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_iva_consumidor_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_consumidor_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_consumidor_id.id,'refund_tax_id':tax.id})

            #Iva contribuyente            
            dic={}
            dic['name']='IVA Contribuyente.'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=13
            dic['description']='Iva'
            dic['tax_group_id']=r.tax_group_iva_id.id
            dic['company_id']=r.id
            tax=r.tax_iva_contribuyente_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_iva_contribuyente_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_contribuyente_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_contribuyente_id.id,'refund_tax_id':tax.id})


            #Iva Compras            
            dic={}
            dic['name']='IVA Compras.'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=13
            dic['description']='Iva'
            dic['tax_group_id']=r.tax_group_iva_id.id
            dic['company_id']=r.id
            tax=r.tax_iva_compras_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_iva_compras_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_compras_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_iva_compras_id.id,'refund_tax_id':tax.id})


            #Iva retencion            
            dic={}
            dic['name']='Retencion 1%'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=1
            dic['description']='Retencion'
            dic['tax_group_id']=r.tax_group_retencion_id.id
            dic['company_id']=r.id
            tax=r.tax_retencion_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_retencion_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_retencion_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_retencion_id.id,'refund_tax_id':tax.id})

            #IVA percepcion            
            dic={}
            dic['name']='Percepcion 1%'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=1
            dic['description']='Percepcion'
            dic['tax_group_id']=r.tax_group_persecion_id.id
            dic['company_id']=r.id
            tax=r.tax_perceccion_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_perceccion_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_perceccion_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_perceccion_id.id,'refund_tax_id':tax.id})

            #ISR            
            dic={}
            dic['name']='ISR 10%'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=-10
            dic['description']='ISR'
            dic['tax_group_id']=r.tax_group_isr_id.id
            dic['company_id']=r.id
            tax=r.tax_isr_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_isr_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_isr_id.id,'invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'tax','account_id':r.account_isr_id.id,'refund_tax_id':tax.id})

            #exento compra           
            dic={}
            dic['name']='Exento compra'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=0
            dic['description']='Exento'
            dic['tax_group_id']=r.tax_group_exento_id.id
            dic['company_id']=r.id
            tax=r.tax_exento_compra_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_exento_compra_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})

            #exento venta           
            dic={}
            dic['name']='Exento venta'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=0
            dic['description']='Exento'
            dic['tax_group_id']=r.tax_group_exento_id.id
            dic['company_id']=r.id
            tax=r.tax_exento_venta_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_exento_venta_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})


            #no sujeto compra           
            dic={}
            dic['name']='No Sujeto Compra'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=0
            dic['description']='No Sujeto'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_nosujeto_compra_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_nosujeto_compra_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})

            #no sujeto venta           
            dic={}
            dic['name']='No Sujeto Venta'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=0
            dic['description']='No Sujeto'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_nosujeto_venta_id
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_nosujeto_venta_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})

            #base tangible compra           
            dic={}
            dic['name']='Base Tangible Compra'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=0
            dic['description']='Base T'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_base_tangible_compra
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_base_tangible_compra':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})

            #base Tangible venta           
            dic={}
            dic['name']='Base Tangible Venta'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=0
            dic['description']='Base T'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_base_tangible_venta
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_base_tangible_venta':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})


            #base servicio compra           
            dic={}
            dic['name']='Base Servicio Compra'
            dic['amount_type']='percent'
            dic['type_tax_use']='purchase'
            dic['amount']=0
            dic['description']='Base T'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_base_servicio_compra
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_base_servicio_compra':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})

            #base Servicio venta           
            dic={}
            dic['name']='Base Servicio Venta'
            dic['amount_type']='percent'
            dic['type_tax_use']='sale'
            dic['amount']=0
            dic['description']='Base T'
            dic['tax_group_id']=r.tax_group_nosujeto_id.id
            dic['company_id']=r.id
            tax=r.tax_base_servicio_venta
            if tax:
                tax.write(dic)
            else:
                tax=self.env['account.tax'].create(dic)
                r.write({'tax_base_servicio_venta':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','invoice_tax_id':tax.id})
                self.env['account.tax.repartition.line'].create({'factor_percent':100,'repartition_type':'base','refund_tax_id':tax.id})


    def create_fiscal_position(self):
        for r in self:
            #no contribuyente:
            dic={}
            dic['name']='No Contribuyente'
            dic['company_id']=r.id
            fp=r.fiscal_position_no_contribuyente_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_no_contribuyente_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_nosujeto_compra_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_iva_consumidor_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_isr_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_iva_consumidor_id.id})
            
            #Pyme Natura:
            dic={}
            dic['name']='Pyme Natural'
            dic['company_id']=r.id
            fp=r.fiscal_position_pyme_natural_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_pyme_natural_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_isr_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            
            #Pyme Juridico:
            dic={}
            dic['name']='Pyme Juridico'
            dic['company_id']=r.id
            fp=r.fiscal_position_pyme_juridico_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_pyme_juridico_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            
            #Grande Natural:
            dic={}
            dic['name']='Grande Natural'
            dic['company_id']=r.id
            fp=r.fiscal_position_grande_natural_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_grande_natural_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_perceccion_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_retencion_id.id})
            
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_retencion_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_isr_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_perceccion_id.id})
            



            #Grande Juridico:
            dic={}
            dic['name']='Grande Juridico'
            dic['company_id']=r.id
            fp=r.fiscal_position_grande_juridico_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_grande_juridico_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_perceccion_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_retencion_id.id})
            
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_retencion_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_iva_contribuyente_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_perceccion_id.id})
            


            #Exento:
            dic={}
            dic['name']='Exento'
            dic['company_id']=r.id
            fp=r.fiscal_position_exento_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_exento_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_exento_venta_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_iva_compras_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_exento_venta_id.id})
            

            #Exento:
            dic={}
            dic['name']='Extrangero'
            dic['company_id']=r.id
            fp=r.fiscal_position_extrangero_id
            if fp:
                fp.write(dic)
            else:
                fp=self.env['account.fiscal.position'].create(dic)
                r.write({'fiscal_position_extrangero_id':fp.id})
            fp.tax_ids.unlink()
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_compra.id,'tax_dest_id':r.tax_exento_compra_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_tangible_venta.id,'tax_dest_id':r.tax_exento_venta_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_compra.id,'tax_dest_id':r.tax_exento_compra_id.id})
            self.env['account.fiscal.position.tax'].create({'position_id':fp.id,'company_id':r.id,'tax_src_id':r.tax_base_servicio_venta.id,'tax_dest_id':r.tax_exento_venta_id.id})
            
    def configure_settings(self):
        for r in self:
            settings=self.env['res.config.settings'].search([('company_id','=',r.id)],limit=1)
            if settings:
                dic={}
                dic['sale_tax_id']=r.tax_base_tangible_venta.id
                dic['purchase_tax_id']=r.tax_base_tangible_compra.id
                settings.write(dic)

    def create_docs(self):
        for r in self:

            #DOCUMENTOS DE VENTA
            #factura
            dic={}
            factura=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Factura'),('tipo_movimiento','=','out_invoice')],limit=1)
            if not factura:
                dic['name']='Factura'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_invoice'
                dic['formato']='Factura'
                dic['contribuyente']=False
                self.env['odoosv.fiscal.document'].create(dic)
            #ccf
            dic={}
            ccf=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','CCF'),('tipo_movimiento','=','out_invoice')],limit=1)
            if not ccf:
                dic['name']='CCF'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_invoice'
                dic['formato']='CCF'
                dic['contribuyente']=True
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El cliente debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)
            dic={}
            exportacion=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Exportacion'),('tipo_movimiento','=','out_invoice')],limit=1)
            if not exportacion:
                dic['name']='Exportacion'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_invoice'
                dic['formato']='Exportacion'
                dic['contribuyente']=False
                dic['validacion']="""
if not partner.tipo_localidad=='NoDomiciliado':
    raise ValidationError('El cliente no debe ser local')
                """
                self.env['odoosv.fiscal.document'].create(dic)
            #Nota de Credito    
            dic={}
            notacredito=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Nota de Credito'),('tipo_movimiento','=','out_refund')],limit=1)
            if not notacredito:
                dic['name']='Nota de Credito'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_refund'
                dic['formato']='NotaCredito'
                dic['contribuyente']=True
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El cliente debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)
            #Nota de Credito    
            dic={}
            notacredito=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Nota de Debito'),('tipo_movimiento','=','out_invoice')],limit=1)
            if not notacredito:
                dic['name']='Nota de Debito'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_invoice'
                dic['contribuyente']=True
                dic['formato']='NotaDebito'
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El cliente debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)    
            dic={}
            devolucion=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Devolucion'),('tipo_movimiento','=','out_refund')],limit=1)
            if not devolucion:
                dic['name']='Devolucion'
                dic['company_id']=r.id
                dic['tipo_movimiento']='out_refund'
                dic['contribuyente']=False
                dic['formato']='Devolucion'
                self.env['odoosv.fiscal.document'].create(dic)

            #DOCUMENTOS DE COMPRA
            #Recibo
            dic={}
            recibo=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Recibo'),('tipo_movimiento','=','in_invoice')],limit=1)
            if not recibo:
                dic['name']='Recibo'
                dic['company_id']=r.id
                dic['tipo_movimiento']='in_invoice'
                dic['contribuyente']=False
                dic['formato']='Recibo'
                self.env['odoosv.fiscal.document'].create(dic)
                dic['validacion']="""
if partner.contribuyente:
    raise ValidationError('El proveedor no debe ser contribuyente')
                """
            #ccf
            dic={}
            ccf=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','CCF'),('tipo_movimiento','=','in_invoice')],limit=1)
            if not ccf:
                dic['name']='CCF'
                dic['company_id']=r.id
                dic['tipo_movimiento']='in_invoice'
                dic['contribuyente']=True
                dic['formato']='CCF'
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El proveedor debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)

            dic={}
            importacion=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Importacion'),('tipo_movimiento','=','in_invoice')],limit=1)
            if not importacion:
                dic['name']='Importacion'
                dic['company_id']=r.id
                dic['tipo_movimiento']='in_invoice'
                dic['contribuyente']=True
                dic['formato']='Importacion'
                dic['validacion']="""
if not partner.tipo_localidad=='NoDomiciliado':
    raise ValidationError('El Proveedor no debe ser local')
                """
                self.env['odoosv.fiscal.document'].create(dic)
            #Nota de Credito    
            dic={}
            notacredito=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Nota de Credito'),('tipo_movimiento','=','in_refund')],limit=1)
            if not notacredito:
                dic['name']='Nota de Credito'
                dic['contribuyente']=True
                dic['company_id']=r.id
                dic['tipo_movimiento']='in_refund'
                dic['formato']='NotaCredito'
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El Proveedor debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)
            #Nota de Debito    
            dic={}
            notacredito=self.env['odoosv.fiscal.document'].search([('company_id','=',r.id),('name','=','Nota de Debito'),('tipo_movimiento','=','in_invoice')],limit=1)
            if not notacredito:
                dic['name']='Nota de Debito'
                dic['company_id']=r.id
                dic['tipo_movimiento']='in_invoice'
                dic['contribuyente']=True
                dic['formato']='NotaDebito'
                dic['validacion']="""
if not partner.nrc:
    raise ValidationError('El proveedor debe tener NRC')
                """
                self.env['odoosv.fiscal.document'].create(dic)    
            

    #Aplicar todas las configuraciones
    def configurar(self):
        for r in self:
            r.write({'sv':True})
            r.create_tax_groups()
            r.create_tax()
            r.create_fiscal_position()
            r.configure_settings()
            r.create_docs()

    def configurar_productos(self):
        for r in self:
            products=self.env['product.template'].search([('company_id','=',r.id)])
            for p in products:
                if p.fiscal_type=='Servicio':
                    ids=[]
                    ids.append(r.tax_base_servicio_venta.id)
                    p.write({'taxes_id':[(6,0,ids)]})
                    ids=[]
                    ids.append(r.tax_base_servicio_compra.id)
                    p.write({'supplier_taxes_id':[(6,0,ids)]})
                if p.fiscal_type=='Tangible':
                    ids=[]
                    ids.append(r.tax_base_tangible_venta.id)
                    p.write({'taxes_id':[(6,0,ids)]})
                    ids=[]
                    ids.append(r.tax_base_tangible_compra.id)
                    p.write({'supplier_taxes_id':[(6,0,ids)]})

    def configurar_partners(self):
        for r in self:
            partners=self.env['res.partner'].search([('company_id','=',r.id)])
            for p in partners:
                if p.tipo_localidad=='NoDomiciliado':
                    p.write({'property_account_position_id':r.fiscal_position_extrangero_id.id})
                else:
                    if p.contribuyente:
                        if p.tipo_fiscal=='Gravado':
                            if p.tipo_persona=='Juridico':
                                if p.tamanio_empresa=='Grande':
                                    p.write({'property_account_position_id':r.fiscal_position_grande_juridico_id.id})
                                else:
                                    p.write({'property_account_position_id':r.fiscal_position_pyme_juridico_id.id})
                            else:
                                if p.tamanio_empresa=='Grande':
                                    p.write({'property_account_position_id':r.fiscal_position_grande_natural_id.id})
                                else:
                                    p.write({'property_account_position_id':r.fiscal_position_pyme_natural_id.id})
                        else:
                            p.write({'property_account_position_id':r.fiscal_position_exento_id.id})
                    else:
                        p.write({'property_account_position_id':r.fiscal_position_no_contribuyente_id.id})



class odoosv_partner(models.Model):
    _inherit='res.partner'
    contribuyente=fields.Boolean("Contribuyente")
    tipo_persona=fields.Selection(selection=[('Natural','Natural'),('Juridico','Juridico')],string="Tipo de persona")
    tamanio_empresa=fields.Selection(selection=[('PYME','PYME'),('Grande','Grande')],string="Tamaño de la empresa")
    tipo_fiscal=fields.Selection(selection=[('Gravado','Gravado'),('Exento','Exento')],string="Tipo fiscal")
    tipo_localidad=fields.Selection(selection=[('Local','Local'),('NoDomiciliado','NoDomiciliado')],string="Localidad")

    @api.onchange('contribuyente','tipo_persona','tamanio_empresa','tipo_fiscal','tipo_localidad')
    def onchange_fiscal(self):
        for p in self:
            if p.company_id:
                if p.company_id.sv:
                    if p.tipo_localidad=='NoDomiciliado':
                        p.write({'property_account_position_id':p.company_id.fiscal_position_extrangero_id.id})
                    else:
                        if p.contribuyente:
                            if p.tipo_fiscal=='Gravado':
                                if p.tipo_persona=='Juridico':
                                    if p.tamanio_empresa=='Grande':
                                        p.write({'property_account_position_id':p.company_id.fiscal_position_grande_juridico_id.id})
                                    else:
                                        p.write({'property_account_position_id':p.company_id.fiscal_position_pyme_juridico_id.id})
                                else:
                                    if p.tamanio_empresa=='Grande':
                                        p.write({'property_account_position_id':p.company_id.fiscal_position_grande_natural_id.id})
                                    else:
                                        p.write({'property_account_position_id':p.company_id.fiscal_position_pyme_natural_id.id})
                            else:
                                p.write({'property_account_position_id':p.company_id.fiscal_position_exento_id.id})
                        else:
                            p.write({'property_account_position_id':p.company_id.fiscal_position_no_contribuyente_id.id})



class odoosv_journal(models.Model):
    _inherit='account.journal'
    sv_sequence_id=fields.Many2one('ir.sequence',string="Numeracion",ondelete="restrict")

class odoosv_move(models.Model):
    _inherit='account.move'
    tipo_documento_id=fields.Many2one('odoosv.fiscal.document',string="Tipo de Documento",ondelete="restrict")
    numeracion_automatica=fields.Boolean("Numeracion automatica",related='tipo_documento_id.numeracion_automatica',store=False)
    razon_notacredito_id=fields.Many2one('odoosv.razon_notacredito',string="Razon de la nota de credito",ondelete="restrict")
    nofiscal=fields.Boolean("Fuera del ambito fiscal")
    sv_numerado=fields.Boolean("Numerado",copy=False)
    sv_numerado_doc=fields.Boolean("Numerado en documento",copy=False)
    doc_numero=fields.Char("Numero de documento",copy=False)
    requiere_poliza=fields.Boolean("Requiere Poliza",related='tipo_documento_id.requiere_poliza')
    poliza=fields.Char("Poliza")
    #caja_id=fields.Many2one('odoosv.caja',string="Caja",default=lambda self: self.env.user.caja_id.id)

    @api.constrains('tipo_documento_id','partner_id','amount_total','state')
    def _check_restriciones(self):
        for r in self:
            if r.move_type in ('in_invoice','in_refund','out_invoice','out_refund'):
                if r.state!='draft':
                    if not r.tipo_documento_id:
                        r.write({'tipo_documento_id':1})#raise ValidationError('Debe especificare un tipo de documento')
                    else:
                        dic={}
                        dic['move']=r
                        dic['partner']=r.partner_id
                        dic['ValidationError']=ValidationError
                        if r.tipo_documento_id.validacion:
                            safe_eval(r.tipo_documento_id.validacion,dic, mode='exec')
#            if r.move_type in ('in_invoice','in_refund'):
#                if not r.nofiscal:
#                    if r.invoice_date:
#                        dias=(datetime.today().date()-r.invoice_date).days
#                        if dias>90:
#                            raise ValidationError('El Documento debe tener menos de 90 dias si se aplicara fiscalmente')
    
    @api.depends('posted_before', 'state', 'journal_id', 'date')
    def _compute_name(self):
        for r in self:
            if r.state=='posted':
                if r.sv_numerado==False:
                    seq=r.journal_id.sv_sequence_id
                    r.name=seq.next_by_id(r.date)
                    r.sv_numerado=True
                if r.numeracion_automatica==True:
                    if r.sv_numerado_doc==False:
                        seq=r.tipo_documento_id.sv_sequence_id
                        r.doc_numero=seq.next_by_id()
                        r.sv_numerado_doc=True

            else:
                if not r.name:
                    r.name='/'
    
    def button_create_landed_costs(self):
        """Create a `stock.landed.cost` record associated to the account move of `self`, each
        `stock.landed.costs` lines mirroring the current `account.move.line` of self.
        """
        self.ensure_one()
        landed_costs_lines = self.line_ids.filtered(lambda line: line.is_landed_costs_line)
        transferencias=[]
        picks=self.env['stock.picking'].search([('origin','=',self.invoice_origin)])
        for p in picks:
            if p.state!='done':
                if p.state!='cancel':
                    raise ValidationError(_('Hay transferencias no compleatas'))
            if p.state=='done':
                t=(4,p.id)
                transferencias.append(t)
        landed_costs = self.env['stock.landed.cost'].create({
            'vendor_bill_id': self.id,
            'picking_ids':transferencias,
            'cost_lines': [(0, 0, {
                'product_id': l.product_id.id,
                'name': l.product_id.name,                
                'account_id': l.product_id.product_tmpl_id.get_product_accounts()['stock_input'].id,
                'price_unit': l.currency_id._convert((l.price_subtotal if self.move_type=='in_invoice' else (l.price_subtotal*-1) ), l.company_currency_id, l.company_id, l.move_id.date),
                'split_method': l.product_id.split_method_landed_cost or 'equal',
            }) for l in landed_costs_lines],
        })
        action = self.env["ir.actions.actions"]._for_xml_id("stock_landed_costs.action_stock_landed_cost")
        return dict(action, view_mode='form', res_id=landed_costs.id, views=[(False, 'form')])
        


class odoosv_moveline(models.Model):
    _inherit='account.move.line'

    @api.constrains('account_id','partner_id','account_analytic_id')
    def _check_restriciones(self):
        for r in self:
            if r.account_id.partner_requerido:
                if not r.partner_id:
                    raise ValidationError('Debe especificar un asociado')
            if r.account_id.analytic_requerido:
                if not r.analytic_account_id:
                    raise ValidationError('Debe especificar una cuenta analitica')
            if r.product_id:
                if r.move_id.move_type=='out_invoice':
                    if r.exclude_from_invoice_tab==False:
                        if r.product_id.bloquear_costo:
                            if r.price_unit<r.product_id.standard_price:
                                raise ValidationError('El precio esta por debajo del costo:'+r.product_id.name)




class odoosv_documento(models.Model):
    _name='odoosv.fiscal.document'
    _description='Tipos de documentos de la localizacion'
    name=fields.Char('Nombre del documento')
    formato=fields.Char('Formato del documento')
    tipo_movimiento=fields.Selection(selection=[('in_invoice','Factura Proveedor'),('out_invoice','Factura Cliente'),('in_refund','Nota Credito Proveedor'),('out_refund','Nota Credito Cliente'),('entry','Entry')],string="Tipo Documento")
    validacion=fields.Text("Codigo de Validacion")
    company_id=fields.Many2one('res.company',string="Company")
    numeracion_automatica=fields.Boolean("Numeracion automatica")
    sv_sequence_id=fields.Many2one('ir.sequence',string="Numeracion",ondelete="restrict")
    contribuyente=fields.Boolean("Documento de contribuyente")
    requiere_poliza=fields.Boolean("Requiere Poliza")
    codigo=fields.Char('Codigo')


class odoosv_account_account(models.Model):
    _inherit='account.account'
    partner_requerido=fields.Boolean('Tercero requerido')
    analytic_requerido=fields.Boolean('Cuenta analitica requerida')


class odoosv_notacredito_razon(models.Model):
    _name='odoosv.razon_notacredito'
    _description='Razon de notas de credito'
    name=fields.Char('Razon de la nota de credito')


#class odoosv_ajuste_razon(models.Model):
#    _name='odoosv.razon_inventario'
#    _description='Razon de ajuste de inventario'
#    name=fields.Char('Razon de ajuste de inventario')

#class odoosv_ajuste_inventario_line(models.Model):
#    _inherit='stock.quant'
#    razon_id=fields.Many2one('odoosv.razon_inventario',string="Razón")


class odoosv_sale_order(models.Model):
    _inherit='sale.order'

    def _create_invoices(self, grouped=False, final=False, date=None):
        """
        Create the invoice associated to the SO.
        :param grouped: if True, invoices are grouped by SO id. If False, invoices are grouped by
                        (partner_invoice_id, currency)
        :param final: if True, refunds will be generated if necessary
        :returns: list of created invoices
        """
        dividir_facturas=False
        lineas_factura=100000
        if not self.env['account.move'].check_access_rights('create', False):
            try:
                self.check_access_rights('write')
                self.check_access_rule('write')
            except AccessError:
                return self.env['account.move']

        # 1) Create invoices.
        invoice_vals_list = []
        invoice_item_sequence = 0 # Incremental sequencing to keep the lines order on the invoice.
        for order in self:
            dividir_facturas=order.company_id.dividir_facturas
            if (dividir_facturas):
                lineas_factura=order.company_id.lineas_factura
            order = order.with_company(order.company_id)
            current_section_vals = None
            down_payments = order.env['sale.order.line']

            invoice_vals = order._prepare_invoice()
            invoiceable_lines = order._get_invoiceable_lines(final)

            if not any(not line.display_type for line in invoiceable_lines):
                raise self._nothing_to_invoice_error()

            invoice_line_vals = []
            down_payment_section_added = False
            for line in invoiceable_lines:
                if not down_payment_section_added and line.is_downpayment:
                    # Create a dedicated section for the down payments
                    # (put at the end of the invoiceable_lines)
                    invoice_line_vals.append(
                        (0, 0, order._prepare_down_payment_section_line(
                            sequence=invoice_item_sequence,
                        )),
                    )
                    dp_section = True
                    invoice_item_sequence += 1
                invoice_line_vals.append(
                    (0, 0, line._prepare_invoice_line(
                        sequence=invoice_item_sequence,
                    )),
                )
                invoice_item_sequence += 1

            invoice_vals['invoice_line_ids'] += invoice_line_vals
            invoice_vals_list.append(invoice_vals)

        if not invoice_vals_list:
            raise self._nothing_to_invoice_error()

        # 2) Manage 'grouped' parameter: group by (partner_id, currency_id).
        if not grouped:
            new_invoice_vals_list = []
            invoice_grouping_keys = self._get_invoice_grouping_keys()
            for grouping_keys, invoices in groupby(invoice_vals_list, key=lambda x: [x.get(grouping_key) for grouping_key in invoice_grouping_keys]):
                
                origins = set()
                payment_refs = set()
                refs = set()
                for invoice_vals in invoices:
                    items=[]
                    contador=1
                    lineasfactura=[]
                    for l in invoice_vals['invoice_line_ids']:
                        lineasfactura.append(l)
                        contador=contador+1
                        if contador>lineas_factura:
                            contador=1
                            items.append(lineasfactura)
                            lineasfactura=[]                        
                    if contador>1:
                        items.append(lineasfactura)
                    origins.add(invoice_vals['invoice_origin'])
                    payment_refs.add(invoice_vals['payment_reference'])
                    refs.add(invoice_vals['ref'])
                    for lineas in items:
                        ref_invoice_vals = invoice_vals.copy()
                        ref_invoice_vals.update({
                        'ref': ', '.join(refs)[:2000],
                        'invoice_origin': ', '.join(origins),
                        'invoice_line_ids':lineas,
                        'payment_reference': len(payment_refs) == 1 and payment_refs.pop() or False,
                        })
                        new_invoice_vals_list.append(ref_invoice_vals)
            invoice_vals_list = new_invoice_vals_list
        # 3) Create invoices.

        # As part of the invoice creation, we make sure the sequence of multiple SO do not interfere
        # in a single invoice. Example:
        # SO 1:
        # - Section A (sequence: 10)
        # - Product A (sequence: 11)
        # SO 2:
        # - Section B (sequence: 10)
        # - Product B (sequence: 11)
        #
        # If SO 1 & 2 are grouped in the same invoice, the result will be:
        # - Section A (sequence: 10)
        # - Section B (sequence: 10)
        # - Product A (sequence: 11)
        # - Product B (sequence: 11)
        #
        # Resequencing should be safe, however we resequence only if there are less invoices than
        # orders, meaning a grouping might have been done. This could also mean that only a part
        # of the selected SO are invoiceable, but resequencing in this case shouldn't be an issue.
        if len(invoice_vals_list) < len(self):
            SaleOrderLine = self.env['sale.order.line']
            for invoice in invoice_vals_list:
                sequence = 1
                for line in invoice['invoice_line_ids']:
                    line[2]['sequence'] = SaleOrderLine._get_invoice_line_sequence(new=sequence, old=line[2]['sequence'])
                    sequence += 1

        # Manage the creation of invoices in sudo because a salesperson must be able to generate an invoice from a
        # sale order without "billing" access rights. However, he should not be able to create an invoice from scratch.
        moves = self.env['account.move'].sudo().with_context(default_move_type='out_invoice').create(invoice_vals_list)

        # 4) Some moves might actually be refunds: convert them if the total amount is negative
        # We do this after the moves have been created since we need taxes, etc. to know if the total
        # is actually negative or not
        if final:
            moves.sudo().filtered(lambda m: m.amount_total < 0).action_switch_invoice_into_refund_credit_note()
        for move in moves:
            move.message_post_with_view('mail.message_origin_link',
                values={'self': move, 'origin': move.line_ids.mapped('sale_line_ids.order_id')},
                subtype_id=self.env.ref('mail.mt_note').id
            )
        return moves


class odoosv_pago_register(models.TransientModel):
    """
    Modelo transitorio para registrar el pago
    """
    _inherit='account.payment.register'
    payment_reference = fields.Char("Referencia de pago")
    
    def _create_payment_vals_from_wizard(self):
        payment_vals = super(odoosv_pago_register,self)._create_payment_vals_from_wizard()
        payment_vals['payment_reference']=self.payment_reference
        return payment_vals
    
    @api.model
    def _get_batch_communication(self, batch_result):
        ''' Helper to compute the communication based on the batch.
        :param batch_result:    A batch returned by '_get_batches'.
        :return:                A string representing a communication to be set on payment.
        '''
        labels = set((line.move_id.tipo_documento_id.name+':'+line.move_id.doc_numero if line.move_id.tipo_documento_id else line.name) or line.move_id.ref or line.move_id.name for line in batch_result['lines'])
        return ' '.join(sorted(labels))



class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res['cheque'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        res['transferencia'] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res
