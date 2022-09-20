# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González (clg@birtum.com)
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
{
	'name': 'Birtum | Custom Pos',
	'version': '15.0.1.0.0',
	'summary': 'Custom Pos Test',
	'description': 'Custom Pos Test',
	'category': 'Sales',
	'author': 'Birtum ©',
	'website': 'https://www.birtum.com',
	'license': 'LGPL-3',
	'depends': ['base', 'point_of_sale', 'contacts'],
	'data': [
		'views/inherit_res_partner_view.xml',
	],
	'assets': {
		'point_of_sale.assets': [
			'b_custom_pos/static/src/js/models.js',
		],
		'web.assets_qweb': [
			'b_custom_pos/static/src/xml/**/*',
		],
	},
	'installable': True,
	'auto_install': False
}
