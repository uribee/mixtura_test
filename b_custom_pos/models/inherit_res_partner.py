# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González
# 				(clg@birtum.com)
#
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from odoo import fields, models, api


class ResPartner(models.Model):
	_inherit = 'res.partner'

	dui = fields.Char("DUI/Cedula", copy=False)
	nit = fields.Char("NIT", select=True, required=True, copy=False)
	nrc = fields.Char("NRC", copy=False)
	nitex = fields.Char("Doc. Extranjero", copy=False)
	website = fields.Char("Website", copy=False)

	_sql_constraints = [
		('NIT_Unico', 'unique (company_id,nit)', 'NIT debe ser unico por Compania'),
		('NRC_Unico', 'unique (company_id,nrc)', 'NRC debe ser unico por Compania'),
		('DUI_Unico', 'unique (company_id,dui)', 'DUI/CEDULA debe ser unico por Compania')
	]
