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


    
class odoosv_user(models.Model):
    _inherit='res.company'

    def configure_db(self):
        for r in self:
            r._create_cuentas_view()
            r._create_num2letras_function()
            r._create_facturasagrupadas_funcion()

    def _create_cuentas_view(self):
        self.env.cr.execute("""CREATE OR REPLACE VIEW public.cuentas
AS SELECT s.id,
    s.code,
    s.name,
    s.tipo AS internal_type,
    s.company_id
   FROM ( SELECT aa.id,
            aa.code,
            aa.name,
            aa.internal_type AS tipo,
            aa.company_id
           FROM account_account aa
        UNION ALL
         SELECT 10000000 + ag.id AS id,
            ag.code_prefix_start AS code,
            ag.name,
            'view_type'::character varying AS tipo,
            ag.company_id
           FROM account_group ag) s
  ORDER BY s.code;""")

    def _create_num2letras_function(self):
        self.env.cr.execute("""CREATE OR REPLACE FUNCTION public.fu_numero_letras(numero numeric)
 RETURNS text
 LANGUAGE plpgsql
AS $function$
DECLARE
     lnEntero INTEGER;
     lcRetorno TEXT;
     lnTerna INTEGER;
     lcMiles TEXT;
     lcCadena TEXT;
     lnUnidades INTEGER;
     lnDecenas INTEGER;
     lnCentenas INTEGER;
     lnFraccion INTEGER;
     lnSw INTEGER;
BEGIN
     lnEntero := FLOOR(numero)::INTEGER;--Obtenemos la parte Entera
     lnFraccion := FLOOR(((numero - lnEntero) * 100))::INTEGER;--Obtenemos la Fraccion del Monto
     lcRetorno := '';
     lnTerna := 1;
     IF lnEntero > 0 THEN
     lnSw := LENGTH(lnEntero);
     WHILE lnTerna <= lnSw LOOP
        -- Recorro terna por terna
        lcCadena = '';
        lnUnidades = lnEntero % 10;
        lnEntero = CAST(lnEntero/10 AS INTEGER);
        lnDecenas = lnEntero % 10;
        lnEntero = CAST(lnEntero/10 AS INTEGER);
        lnCentenas = lnEntero % 10;
        lnEntero = CAST(lnEntero/10 AS INTEGER);
    -- Analizo las unidades
       SELECT
         CASE /* UNIDADES */
           WHEN lnUnidades = 1 AND lnTerna = 1 THEN 'UNO ' || lcCadena
           WHEN lnUnidades = 1 AND lnTerna <> 1 THEN 'UN ' || lcCadena
           WHEN lnUnidades = 2 THEN 'DOS ' || lcCadena
           WHEN lnUnidades = 3 THEN 'TRES ' || lcCadena
           WHEN lnUnidades = 4 THEN 'CUATRO ' || lcCadena
           WHEN lnUnidades = 5 THEN 'CINCO ' || lcCadena
           WHEN lnUnidades = 6 THEN 'SEIS ' || lcCadena
           WHEN lnUnidades = 7 THEN 'SIETE ' || lcCadena
           WHEN lnUnidades = 8 THEN 'OCHO ' || lcCadena
           WHEN lnUnidades = 9 THEN 'NUEVE ' || lcCadena
           ELSE lcCadena
          END INTO lcCadena;
          /* UNIDADES */
    -- Analizo las decenas
    SELECT
    CASE /* DECENAS */
      WHEN lnDecenas = 1 THEN
        CASE lnUnidades
          WHEN 0 THEN 'DIEZ '
          WHEN 1 THEN 'ONCE '
          WHEN 2 THEN 'DOCE '
          WHEN 3 THEN 'TRECE '
          WHEN 4 THEN 'CATORCE '
          WHEN 5 THEN 'QUINCE '
          ELSE 'DIECI' || lcCadena
        END
      WHEN lnDecenas = 2 AND lnUnidades = 0 THEN 'VEINTE ' || lcCadena
      WHEN lnDecenas = 2 AND lnUnidades <> 0 THEN 'VEINTI' || lcCadena
      WHEN lnDecenas = 3 AND lnUnidades = 0 THEN 'TREINTA ' || lcCadena
      WHEN lnDecenas = 3 AND lnUnidades <> 0 THEN 'TREINTA Y ' || lcCadena
      WHEN lnDecenas = 4 AND lnUnidades = 0 THEN 'CUARENTA ' || lcCadena
      WHEN lnDecenas = 4 AND lnUnidades <> 0 THEN 'CUARENTA Y ' || lcCadena
      WHEN lnDecenas = 5 AND lnUnidades = 0 THEN 'CINCUENTA ' || lcCadena
      WHEN lnDecenas = 5 AND lnUnidades <> 0 THEN 'CINCUENTA Y ' || lcCadena
      WHEN lnDecenas = 6 AND lnUnidades = 0 THEN 'SESENTA ' || lcCadena
      WHEN lnDecenas = 6 AND lnUnidades <> 0 THEN 'SESENTA Y ' || lcCadena
      WHEN lnDecenas = 7 AND lnUnidades = 0 THEN 'SETENTA ' || lcCadena
      WHEN lnDecenas = 7 AND lnUnidades <> 0 THEN 'SETENTA Y ' || lcCadena
      WHEN lnDecenas = 8 AND lnUnidades = 0 THEN 'OCHENTA ' || lcCadena
      WHEN lnDecenas = 8 AND lnUnidades <> 0 THEN 'OCHENTA Y ' || lcCadena
      WHEN lnDecenas = 9 AND lnUnidades = 0 THEN 'NOVENTA ' || lcCadena
      WHEN lnDecenas = 9 AND lnUnidades <> 0 THEN 'NOVENTA Y ' || lcCadena
      ELSE lcCadena
    END INTO lcCadena; /* DECENAS */
    -- Analizo las centenas
    SELECT
    CASE /* CENTENAS */
      WHEN lnCentenas = 1 AND lnUnidades = 0 AND lnDecenas = 0 THEN 'CIEN ' || lcCadena
      WHEN lnCentenas = 1 AND NOT(lnUnidades = 0 AND lnDecenas = 0) THEN 'CIENTO ' || lcCadena
      WHEN lnCentenas = 2 THEN 'DOSCIENTOS ' || lcCadena
      WHEN lnCentenas = 3 THEN 'TRESCIENTOS ' || lcCadena
      WHEN lnCentenas = 4 THEN 'CUATROCIENTOS ' || lcCadena
      WHEN lnCentenas = 5 THEN 'QUINIENTOS ' || lcCadena
      WHEN lnCentenas = 6 THEN 'SEISCIENTOS ' || lcCadena
      WHEN lnCentenas = 7 THEN 'SETECIENTOS ' || lcCadena
      WHEN lnCentenas = 8 THEN 'OCHOCIENTOS ' || lcCadena
      WHEN lnCentenas = 9 THEN 'NOVECIENTOS ' || lcCadena
      ELSE lcCadena
    END INTO lcCadena;/* CENTENAS */
    -- Analizo la terna
    SELECT
    CASE /* TERNA */
      WHEN lnTerna = 1 THEN lcCadena
      WHEN lnTerna = 2 AND (lnUnidades + lnDecenas + lnCentenas <> 0) THEN lcCadena || ' MIL '
      WHEN lnTerna = 3 AND (lnUnidades + lnDecenas + lnCentenas <> 0) AND
        lnUnidades = 1 AND lnDecenas = 0 AND lnCentenas = 0 THEN lcCadena || ' MILLON '
      WHEN lnTerna = 3 AND (lnUnidades + lnDecenas + lnCentenas <> 0) AND
        NOT (lnUnidades = 1 AND lnDecenas = 0 AND lnCentenas = 0) THEN lcCadena || ' MILLONES '
      WHEN lnTerna = 4 AND (lnUnidades + lnDecenas + lnCentenas <> 0) THEN lcCadena || ' MIL MILLONES '
      ELSE ''
    END INTO lcCadena;/* TERNA */

    --Retornamos los Valores Obtenidos
    lcRetorno = lcCadena  || lcRetorno;
    lnTerna = lnTerna + 1;
    END LOOP;
  END IF;
  IF lnTerna = 1 THEN
    lcRetorno := 'CERO';
  END IF;
  lcRetorno := RTRIM(lcRetorno) || ' CON ' || LTRIM(lnFraccion) || '/100 ';
RETURN lcRetorno;
END;
$function$
;""")

    def _create_facturasagrupadas_funcion(self):
        self.env.cr.execute("""CREATE OR REPLACE FUNCTION public.facturasagrupadas(p_company_id integer, month_number integer, year_number integer, p_series_lenght integer)
 RETURNS TABLE(invoice_id integer, factura_number character varying, factura_status character varying, grupo integer)
 LANGUAGE plpgsql
AS $function$
DECLARE 
    var_r record;
	var_serie varchar;
	var_fecha date;
	var_correlativo int;
	var_estado varchar;	
	var_grupo int;
BEGIN
 var_grupo :=0;
 FOR var_r IN (select ROW_NUMBER () OVER (ORDER BY f.invoice_date,coalesce(F.doc_numero,cast(F.id as varchar) ))  as Registro
					,left(coalesce(F.ref,cast(F.id as varchar)),p_series_lenght) as Serie
					,CAST((COALESCE(NULLIF(REGEXP_REPLACE( right(coalesce(F.doc_numero,cast(F.id as varchar)),(length(coalesce(F.doc_numero,cast(F.id as varchar)))-p_series_lenght)) , '[^0-9]+', '', 'g'), ''), '0')) AS INTEGER) as correlativo  
					,F.invoice_date as fecha
					,case 
						when F.state='cancel' then 'ANULADA'
					    else 'Valida' end as estado
					,coalesce(F.doc_numero,cast(F.id as varchar)) as factura,F.id
				from Account_move F 
					inner join odoosv_fiscal_document doc on F.tipo_documento_id =doc.id
				where date_part('year',COALESCE(F.date,F.invoice_date))= year_number 
					  and date_part('month',COALESCE(F.date,F.invoice_date))= month_number
				      and F.state<>'draft' and F.company_id=p_company_id
					  and F.move_type in ('out_invoice')
				      and doc.codigo in ('Factura','Exportacion')
				order by fecha,factura )  
 LOOP
 		invoice_id := var_r.id; 
		factura_number := var_r.Factura;
		factura_status := var_r.estado;
 		if ((var_r.Serie=var_serie) and (var_r.fecha=var_Fecha) and (var_r.estado=var_estado) and (var_r.correlativo=(var_correlativo+1))) then
			grupo := var_grupo;
		else
			var_grupo := var_grupo+1;
			grupo := var_grupo;			
		end if;
        var_serie := var_r.Serie;
		var_fecha := var_r.fecha;
		var_estado := var_r.estado;
		var_correlativo := var_r.correlativo;
 		
        RETURN NEXT;
 END LOOP;
END; 
$function$
;
""")
        self.env.cr.execute("""CREATE OR REPLACE FUNCTION public.facturasagrupadas(p_company_id integer, month_number integer, year_number integer, p_series_lenght integer, p_sucursal integer)
 RETURNS TABLE(invoice_id integer, factura_number character varying, factura_status character varying, grupo integer)
 LANGUAGE plpgsql
AS $function$
DECLARE 
    var_r record;
	var_serie varchar;
	var_fecha date;
	var_correlativo int;
	var_estado varchar;	
	var_grupo int;
BEGIN
 var_grupo :=0;
 FOR var_r IN (select ROW_NUMBER () OVER (ORDER BY f.invoice_date,coalesce(F.doc_numero,cast(F.id as varchar) ))  as Registro
					,left(coalesce(F.ref,cast(F.id as varchar)),p_series_lenght) as Serie
					,CAST((COALESCE(NULLIF(REGEXP_REPLACE( right(coalesce(F.doc_numero,cast(F.id as varchar)),(length(coalesce(F.doc_numero,cast(F.id as varchar)))-p_series_lenght)) , '[^0-9]+', '', 'g'), ''), '0')) AS INTEGER) as correlativo  
					,F.invoice_date as fecha
					,case 
						when F.state='cancel' then 'Valida'
					    else 'Valida' end as estado
					,coalesce(F.doc_numero,cast(F.id as varchar)) as factura,F.id
				from Account_move F 
					inner join odoosv_fiscal_document doc on F.tipo_documento_id =doc.id
				where date_part('year',COALESCE(F.date,F.invoice_date))= year_number 
					  and date_part('month',COALESCE(F.date,F.invoice_date))= month_number
				      and F.state<>'draft' and F.company_id=p_company_id
					  and F.move_type in ('out_invoice') and F.caja_id=p_sucursal
				      and doc.codigo in ('Factura','Exportacion')
				      and ((F.nofiscal is not null and F.nofiscal=false) or (F.nofiscal is null))
				order by fecha,factura )  
 LOOP
 		invoice_id := var_r.id; 
		factura_number := var_r.Factura;
		factura_status := var_r.estado;
 		if ((var_r.Serie=var_serie) and (var_r.fecha=var_Fecha) and (var_r.estado=var_estado) and (var_r.correlativo=(var_correlativo+1))) then
			grupo := var_grupo;
		else
			var_grupo := var_grupo+1;
			grupo := var_grupo;			
		end if;
        var_serie := var_r.Serie;
		var_fecha := var_r.fecha;
		var_estado := var_r.estado;
		var_correlativo := var_r.correlativo;
 		
        RETURN NEXT;
 END LOOP;
END; 
$function$
;
""")