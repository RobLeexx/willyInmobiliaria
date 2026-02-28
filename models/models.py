from odoo import models, fields, api, _
from odoo.exceptions import UserError

class MudanzasProvince(models.Model):
    _name = 'mudanzas.province'
    _description = 'Province for Mudanzas'

    name = fields.Char(string='Provincia', required=True)
    state = fields.Char(string='Estado')


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

    # carga (pickup) address fields (manual select)
    streetup = fields.Char(string="Calle")
    streetup2 = fields.Char(string="Calle 2")
    cityup = fields.Char(string="Ciudad")
    zipup = fields.Char(string="Código Postal")

    # map of Spanish comunidades to their provincias; used for both pickup and delivery
    STATE_PROVINCE_MAP = {
        'Andalucía': ['Almería', 'Cádiz', 'Córdoba', 'Granada', 'Huelva', 'Jaén', 'Málaga', 'Sevilla'],
        'Aragón': ['Huesca', 'Teruel', 'Zaragoza'],
        'Asturias': ['Principado de Asturias'],
        'Baleares': ['Islas Baleares'],
        'Canarias': ['Las Palmas', 'Santa Cruz de Tenerife'],
        'Cantabria': ['Cantabria'],
        'Castilla-La Mancha': ['Albacete', 'Ciudad Real', 'Cuenca', 'Guadalajara', 'Toledo'],
        'Castilla y León': ['Ávila', 'Burgos', 'León', 'Palencia', 'Salamanca', 'Segovia', 'Soria', 'Valladolid', 'Zamora'],
        'Cataluña': ['Barcelona', 'Girona', 'Lleida', 'Tarragona'],
        'Comunidad Valenciana': ['Alicante', 'Castellón', 'Valencia'],
        'Extremadura': ['Badajoz', 'Cáceres'],
        'Galicia': ['A Coruña', 'Lugo', 'Ourense', 'Pontevedra'],
        'Madrid': ['Comunidad de Madrid'],
        'Murcia': ['Región de Murcia'],
        'Navarra': ['Comunidad Foral de Navarra'],
        'País Vasco': ['Álava', 'Guipúzcoa', 'Vizcaya'],
        'La Rioja': ['La Rioja'],
    }
    # Precomputed selection tuples to ensure availability during module load
    STATE_SELECTION = [(key, key) for key in STATE_PROVINCE_MAP.keys()]
    _ALL_PROVINCES = []
    for _lst in STATE_PROVINCE_MAP.values():
        _ALL_PROVINCES.extend(_lst)
    PROVINCE_SELECTION = sorted([(p, p) for p in set(_ALL_PROVINCES)], key=lambda x: x[0])

    state_up = fields.Selection(selection=STATE_SELECTION, string="Estado", default='Comunidad Valenciana')
    province_up = fields.Selection(selection=PROVINCE_SELECTION, string="Provincia", default='Valencia')

    # descarga (delivery) address fields (manual select)
    streetdown = fields.Char(string="Calle")
    streetdown2 = fields.Char(string="Calle 2")
    citydown = fields.Char(string="Ciudad")
    zipdown = fields.Char(string="Código Postal")
    state_down = fields.Selection(selection=STATE_SELECTION, string="Estado", default='Comunidad Valenciana')
    province_down = fields.Selection(selection=PROVINCE_SELECTION, string="Provincia", default='Valencia')

    @api.onchange('state_up')
    def _onchange_state_up(self):
        if self.state_up:
            provinces = self.STATE_PROVINCE_MAP.get(self.state_up, [])
            if len(provinces) == 1:
                self.province_up = provinces[0]
            elif self.province_up not in provinces:
                self.province_up = False

    @api.onchange('state_down')
    def _onchange_state_down(self):
        if self.state_down:
            provinces = self.STATE_PROVINCE_MAP.get(self.state_down, [])
            if len(provinces) == 1:
                self.province_down = provinces[0]
            elif self.province_down not in provinces:
                self.province_down = False
