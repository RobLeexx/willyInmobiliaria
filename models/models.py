from odoo import models, fields, api, _
from odoo.exceptions import UserError

class CrmLead(models.Model):
    _inherit = "crm.lead"

    test_debug_field = fields.Char(string="Test Debug Field")

    # Personal information
    contact_name = fields.Char(string="Contacto")
    email_form = fields.Char(string="Email")
    phone = fields.Char(string="Teléfono")

    # Mudanza fields
    carga = fields.Char(string="Carga")
    observaciones_carga = fields.Text(string="Observaciones de Carga")
    descarga = fields.Char(string="Descarga")
    observaciones_descarga = fields.Text(string="Observaciones de Descarga")

    # Room values
    recibidor = fields.Char(string="Recibidor")
    sala_comedor = fields.Char(string="Sala/Comedor")
    habitacion_matrimonial = fields.Char(string="Habitación Matrimonial")
    habitacion_individual = fields.Char(string="Habitación Individual")
    cocina = fields.Char(string="Cocina")
    despacho = fields.Char(string="Despacho")
    terraza_trastero = fields.Char(string="Terraza/Trastero")
    observaciones_mudanza = fields.Text(string="Observaciones")

    # carga (pickup) address fields
    streetup = fields.Char(string="Calle")
    streetup2 = fields.Char(string="Calle 2")
    cityup = fields.Char(string="Ciudad")
    zipup = fields.Char(string="Código Postal")
    state_up_id = fields.Many2one('res.country.state', string="Estado")
    country_up_id = fields.Many2one('res.country', string="País")

    # descarga (delivery) address fields
    streetdown = fields.Char(string="Calle")
    streetdown2 = fields.Char(string="Calle 2")
    citydown = fields.Char(string="Ciudad")
    zipdown = fields.Char(string="Código Postal")
    state_down_id = fields.Many2one('res.country.state', string="Estado")
    country_down_id = fields.Many2one('res.country', string="País")

    @api.model
    def create(self, vals):
        # Set default Spain for pickup address if not provided
        if 'country_up_id' not in vals or not vals['country_up_id']:
            spain = self.env.ref('base.es', raise_if_not_found=False)
            if spain:
                vals['country_up_id'] = spain.id
        if 'state_up_id' not in vals or not vals['state_up_id']:
            madrid = self.env.ref('base.state_es_m', raise_if_not_found=False)
            if madrid:
                vals['state_up_id'] = madrid.id
        return super().create(vals)
