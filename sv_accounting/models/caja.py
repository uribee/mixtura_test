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

class odoosv_caja(models.Model):
    _name='odoosv.caja'
    _description='Caja'
    name=fields.Char('Caja')
    company_id=fields.Many2one('res.company',string="Company")
    analytic_account_id=fields.Many2one('account.analytic.account',string="Cuenta analitica")

class odoosv_user(models.Model):
    _inherit='res.users'
    caja_id=fields.Many2one('odoosv.caja',string="Caja")
