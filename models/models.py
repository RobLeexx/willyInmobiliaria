from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class MudanzasProvince(models.Model):
    _name = 'mudanzas.province'
    _description = 'Province for Mudanzas'

    name = fields.Char(string='Provincia', required=True)
    state = fields.Char(string='Estado')


class MudanzasObjectCatalog(models.Model):
    _name = 'mudanzas.object.catalog'
    _description = 'Catalogo de objetos para mudanza'
    _order = 'sequence, name'

    name = fields.Char(string='Objeto', required=True, translate=False)
    sequence = fields.Integer(string='Secuencia', default=10)
    category = fields.Selection(
        [
            ('inmueble', 'Inmueble'),
            ('objeto', 'Objeto'),
            ('especial', 'Especial'),
        ],
        string='Categoria',
        default='objeto',
        required=True,
    )
    peso_referencia = fields.Float(string='Kg de referencia')
    embalaje_recomendado = fields.Boolean(string='Embalaje recomendado')
    desmontaje_recomendado = fields.Boolean(string='Desmontaje recomendado')
    is_other = fields.Boolean(string='Es opcion manual', default=False)


class CrmLead(models.Model):
    _inherit = "crm.lead"

    test_debug_field = fields.Char(string="Test Debug Field")

    # Personal information
    contact_name = fields.Char(string="Contacto")
    email_form = fields.Char(string="Email")
    phone = fields.Char(string="Teléfono")

    # Mudanza fields
    cantidad = fields.Integer(string="Cantidad")
    objeto = fields.Char(string="Objetos")
    objeto_catalogo_id = fields.Many2one(
        'mudanzas.object.catalog',
        string='Objeto (catalogo)',
        help='Busca y selecciona un objeto frecuente de mudanza.',
    )
    objeto_es_otro = fields.Boolean(
        string='Objeto manual',
        related='objeto_catalogo_id.is_other',
        readonly=True,
    )
    objeto_manual = fields.Char(string="Otro objeto")
    peso = fields.Float(string="KG")
    embalaje = fields.Boolean(string="Embalaje")
    desmontaje = fields.Boolean(string="Desmontaje")
    habitacion = fields.Selection(
        [
            ('recibidor', 'Recibidor'),
            ('sala_comedor', 'Sala/Comedor'),
            ('habitacion_matrimonial', 'Habitación Matrimonial'),
            ('habitacion_individual', 'Habitación Individual'),
            ('cocina', 'Cocina'),
            ('despacho', 'Despacho'),
            ('terraza_trastero', 'Terraza/Trastero'),
            ('otros', 'Otros')
        ],
        string="Habitación"
    )
    observaciones_mudanza = fields.Char(string="Observaciones")

    # Offer details
    #recibidor = fields.Char(string="Recibidor")
    #sala_comedor = fields.Char(string="Sala/Comedor")
    #habitacion_matrimonial = fields.Char(string="Habitación Matrimonial")
    #habitacion_individual = fields.Char(string="Habitación Individual")
    #cocina = fields.Char(string="Cocina")
    #despacho = fields.Char(string="Despacho")
    #terraza_trastero = fields.Char(string="Terraza/Trastero")

    precio_oferta = fields.Float(string="Precio Oferta")
    tipo_oferta = fields.Selection(
        [
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
        ],
        string="Tipo Oferta",
        default='baja'
    )
    
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

    @api.onchange('precio_oferta')
    def _onchange_precio_oferta(self):
        if self.precio_oferta:
            if self.precio_oferta < 500:
                self.tipo_oferta = 'baja'
            elif self.precio_oferta <= 700:
                self.tipo_oferta = 'media'
            else:
                self.tipo_oferta = 'alta'

    @api.model
    def create(self, vals):
        if 'precio_oferta' not in vals and 'expected_revenue' in vals:
            vals['precio_oferta'] = vals['expected_revenue']
        vals = self._prepare_objeto_vals(vals)
        return super().create(vals)

    def write(self, vals):
        if 'objeto_catalogo_id' in vals or 'objeto_manual' in vals:
            for lead in self:
                lead_vals = lead._prepare_objeto_vals(dict(vals))
                super(CrmLead, lead).write(lead_vals)
            return True

        vals = self._prepare_objeto_vals(vals)
        return super().write(vals)
    
    @api.onchange('expected_revenue')
    def _onchange_expected_revenue(self):
        if self.expected_revenue:
            self.precio_oferta = self.expected_revenue

    @api.onchange('objeto_catalogo_id')
    def _onchange_objeto_catalogo_id(self):
        self._apply_objeto_catalogo_defaults()

    @api.onchange('objeto_manual')
    def _onchange_objeto_manual(self):
        for lead in self:
            if lead.objeto_catalogo_id and lead.objeto_catalogo_id.is_other:
                lead.objeto = lead.objeto_manual

    @api.constrains('objeto_catalogo_id', 'objeto_manual')
    def _check_objeto_manual_required(self):
        for lead in self:
            if lead.objeto_catalogo_id and lead.objeto_catalogo_id.is_other and not lead.objeto_manual:
                raise ValidationError(_("Debes indicar el nombre en 'Otro objeto'."))

    def _apply_objeto_catalogo_defaults(self):
        for lead in self:
            catalog = lead.objeto_catalogo_id
            if not catalog:
                continue

            if catalog.is_other:
                lead.objeto = lead.objeto_manual
                continue

            lead.objeto = catalog.name
            lead.objeto_manual = False
            lead.peso = catalog.peso_referencia or False
            if catalog.embalaje_recomendado:
                lead.embalaje = True
            if catalog.desmontaje_recomendado:
                lead.desmontaje = True

    def _prepare_objeto_vals(self, vals):
        if 'objeto_catalogo_id' not in vals and 'objeto_manual' not in vals:
            return vals

        catalog_id = vals.get('objeto_catalogo_id')
        if catalog_id is None and self:
            catalog_id = self[0].objeto_catalogo_id.id

        if not catalog_id:
            return vals

        catalog = self.env['mudanzas.object.catalog'].browse(catalog_id)
        if not catalog.exists():
            return vals

        if catalog.is_other:
            manual_name = vals.get('objeto_manual')
            if manual_name is None and self:
                manual_name = self[0].objeto_manual
            vals['objeto'] = manual_name or False
            return vals

        vals['objeto'] = catalog.name
        vals.setdefault('objeto_manual', False)
        if not vals.get('peso') and catalog.peso_referencia:
            vals['peso'] = catalog.peso_referencia
        if catalog.embalaje_recomendado:
            vals.setdefault('embalaje', True)
        if catalog.desmontaje_recomendado:
            vals.setdefault('desmontaje', True)
        return vals
