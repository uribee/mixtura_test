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
from datetime import datetime
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


    
class odoosv_category(models.Model):
    _inherit='product.category'
    code=fields.Integer("Codigo",select=True)

class odoosv_user(models.Model):
    _inherit='res.users'
    code=fields.Integer("Codigo",select=True)

class odoosv_partner(models.Model):
    _inherit='res.partner'
    _sql_constraints = [
        ('NIT_Unico', 'unique (company_id,nit)', 'NIT debe ser unico por Compania'),
        ('NRC_Unico', 'unique (company_id,nrc)', 'NRC debe ser unico por Compania'),
        ('DUI_Unico', 'unique (company_id,dui)', 'DUI/CEDULA debe ser unico por Compania')
    ]
    nrc=fields.Char("NRC",copy=False)
    nit=fields.Char("NIT",select=True,required=True,copy=False)
    giro=fields.Char("Giro")
    dui=fields.Char("DUI/Cedula",copy=False)
    nombres=fields.Char("Nombres")
    apellidos=fields.Char("Apellidos")
    razon_social=fields.Char("Razón social")
    referencia_ids=fields.One2many(comodel_name='odoosv.partner.referencia',inverse_name='partner_id',string='Referencias')

class odoosv_move(models.Model):
    _inherit='account.move'
    nit=fields.Char("NIT",related='partner_id.nit',store=True)

class odoosv_referencia(models.Model):
    _name='odoosv.partner.referencia'
    _description='Referencia crediticia'

    name=fields.Char("Nombre")
    telefono=fields.Char("Telefono")
    email=fields.Char("Email")
    comentario=fields.Char("Comentario")
    partner_id=fields.Many2one('res.partner',string="Contacto")

