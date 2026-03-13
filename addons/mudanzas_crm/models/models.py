
import os
import xml.etree.ElementTree as ET

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup


def _env_float(name, default):
    try:
        return float(os.getenv(name, default))
    except (TypeError, ValueError):
        return float(default)


def _env_int(name, default):
    try:
        return int(float(os.getenv(name, default)))
    except (TypeError, ValueError):
        return int(default)


class MudanzasProvince(models.Model):
    _name = 'mudanzas.province'
    _description = 'Province for Mudanzas'

    name = fields.Char(string='Provincia', required=True)
    state = fields.Char(string='Comunidad')


class MudanzasObjectCatalog(models.Model):
    _name = 'mudanzas.object.catalog'
    _description = 'Catalogo de objetos para mudanza'
    _order = 'sequence, name'

    _LEGACY_XMLID_MAP = {
        'objeto_catalogo_alacena': 'objeto_catalogo_alacena_despensa',
        'objeto_catalogo_alfombra': 'objeto_catalogo_alfombra_enrollada',
        'objeto_catalogo_aparador': 'objeto_catalogo_aparador_vitrina',
        'objeto_catalogo_armario_2': 'objeto_catalogo_armario_ropero_2_cuerpos',
        'objeto_catalogo_armario_4': 'objeto_catalogo_armario_ropero_4_cuerpos',
        'objeto_catalogo_caja_grande': 'objeto_catalogo_caja_carton_grande',
        'objeto_catalogo_caja_pequena': 'objeto_catalogo_caja_carton_pequena',
        'objeto_catalogo_cama_individual': 'objeto_catalogo_cama_individual_arcon',
        'objeto_catalogo_comoda': 'objeto_catalogo_comoda_cajonera',
        'objeto_catalogo_cuadro': 'objeto_catalogo_cuadro_pintura',
        'objeto_catalogo_cuna': 'objeto_catalogo_cuna_camita_nino',
        'objeto_catalogo_escritorio': 'objeto_catalogo_escritorio_oficina',
        'objeto_catalogo_frigorifico': 'objeto_catalogo_frigorifico_nevera',
        'objeto_catalogo_librero': 'objeto_catalogo_estanteria_libros_librero',
        'objeto_catalogo_maleta': 'objeto_catalogo_maleta_viaje',
        'objeto_catalogo_mesa_comedor_grande': 'objeto_catalogo_mesa_comedor_6_8',
        'objeto_catalogo_mesa_comedor_pequena': 'objeto_catalogo_mesa_comedor_2_4',
        'objeto_catalogo_monitor_pc': 'objeto_catalogo_monitor_pc_escritorio',
        'objeto_catalogo_planta_grande': 'objeto_catalogo_planta_interior_maceta_grande',
        'objeto_catalogo_sillon': 'objeto_catalogo_sillon_individual_reclinable',
        'objeto_catalogo_sofa_2': 'objeto_catalogo_sofa_2_plazas',
        'objeto_catalogo_sofa_3': 'objeto_catalogo_sofa_3_plazas',
        'objeto_catalogo_tocador': 'objeto_catalogo_tocador_espejo',
    }

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
    volumen_referencia = fields.Float(string='M³ de referencia')
    peso_referencia = fields.Float(string='Kg de referencia')
    embalaje_recomendado = fields.Boolean(string='Embalaje recomendado')
    desmontaje_recomendado = fields.Boolean(string='Desmontaje recomendado')
    is_other = fields.Boolean(string='Es opcion manual', default=False)

    @api.model
    def _get_catalog_xml_path(self):
        return os.path.normpath(
            os.path.join(os.path.dirname(__file__), '..', 'data', 'object_catalog.xml')
        )

    @api.model
    def _parse_catalog_xml_values(self):
        tree = ET.parse(self._get_catalog_xml_path())
        root = tree.getroot()
        boolean_fields = {'embalaje_recomendado', 'desmontaje_recomendado', 'is_other'}
        integer_fields = {'sequence'}
        float_fields = {'volumen_referencia', 'peso_referencia'}
        allowed_fields = boolean_fields | integer_fields | float_fields | {'name', 'category'}
        values_by_xmlid = {}

        for record_node in root.findall(".//record[@model='mudanzas.object.catalog']"):
            xmlid_suffix = record_node.get('id')
            if not xmlid_suffix:
                continue
            vals = {}
            for field_node in record_node.findall('field'):
                field_name = field_node.get('name')
                if field_name not in allowed_fields:
                    continue
                raw_value = (field_node.text or '').strip()
                if field_name in boolean_fields:
                    vals[field_name] = raw_value.lower() in {'1', 'true'}
                elif field_name in integer_fields:
                    vals[field_name] = int(raw_value or 0)
                elif field_name in float_fields:
                    vals[field_name] = float(raw_value or 0.0)
                else:
                    vals[field_name] = raw_value
            values_by_xmlid[xmlid_suffix] = vals

        return values_by_xmlid

    @api.model
    def _migrate_legacy_catalog_xmlids(self):
        imd_model = self.env['ir.model.data'].sudo()
        line_model = self.env['mudanzas.lead.object.line'].sudo()
        lead_model = self.env['crm.lead'].sudo()

        for legacy_xmlid, current_xmlid in self._LEGACY_XMLID_MAP.items():
            legacy_imd = imd_model.search(
                [
                    ('module', '=', 'mudanzas_crm'),
                    ('name', '=', legacy_xmlid),
                    ('model', '=', 'mudanzas.object.catalog'),
                ],
                limit=1,
            )
            current_record = self.env.ref(f'mudanzas_crm.{current_xmlid}', raise_if_not_found=False)
            if not legacy_imd or not current_record:
                continue

            legacy_record = self.browse(legacy_imd.res_id).exists()
            if not legacy_record or legacy_record.id == current_record.id:
                legacy_imd.unlink()
                continue

            line_model.search([('objeto_catalogo_id', '=', legacy_record.id)]).write(
                {'objeto_catalogo_id': current_record.id}
            )
            if 'objeto_catalogo_id' in lead_model._fields:
                lead_model.search([('objeto_catalogo_id', '=', legacy_record.id)]).write(
                    {'objeto_catalogo_id': current_record.id}
                )

            legacy_imd.unlink()
            legacy_record.unlink()

    @api.model
    def sync_reference_volumes(self):
        for xmlid_suffix, vals in self._parse_catalog_xml_values().items():
            record = self.env.ref(f'mudanzas_crm.{xmlid_suffix}', raise_if_not_found=False)
            if record:
                record.write(vals)
        self._migrate_legacy_catalog_xmlids()


HABITACION_SELECTION = [
    ('recibidor', 'Recibidor'),
    ('sala_comedor', 'Sala/Comedor'),
    ('habitacion_matrimonial', 'Habitación Matrimonial'),
    ('habitacion_individual', 'Habitación Individual'),
    ('cocina', 'Cocina'),
    ('despacho', 'Despacho'),
    ('terraza_trastero', 'Terraza/Trastero'),
    ('otros', 'Otros'),
]

ELEVATOR_SELECTION = [
    ('tiene', 'Tiene'),
    ('no_tiene', 'NO Tiene'),
]

OPERARIOS_SELECTION = [(str(i), str(i)) for i in range(1, 11)]


class MudanzasLeadObjectLine(models.Model):
    _name = 'mudanzas.lead.object.line'
    _description = 'Linea de objeto de mudanza'
    _order = 'id'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    cantidad = fields.Integer(string='Cantidad', default=1)
    objeto = fields.Char(string='Objeto')
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
    objeto_manual = fields.Char(string='Otro objeto')
    peso = fields.Float(string='Kg')
    horas_referencia = fields.Float(string='Horas aprox', digits=(16, 2))
    horas_referencia_manual = fields.Float(
        string='Horas aprox manual',
        digits=(16, 2),
        copy=False,
    )
    horas_referencia_manual_override = fields.Boolean(
        string='Horas aprox manual override',
        default=False,
        copy=False,
    )
    volumen = fields.Float(string='M³')
    embalaje = fields.Boolean(string='Embalaje')
    desmontaje = fields.Boolean(string='Desmontaje')
    habitacion = fields.Selection(selection=HABITACION_SELECTION, string='Habitación')

    @api.onchange(
        'cantidad',
        'volumen',
        'embalaje',
        'desmontaje',
        'objeto_catalogo_id',
        'lead_id.floorup',
        'lead_id.floordown',
        'lead_id.elevatorup',
        'lead_id.elevatordown',
        'lead_id.elevador',
        'lead_id.horas_elevador',
    )
    def _onchange_estimation_inputs(self):
        for line in self:
            if not line.horas_referencia_manual_override:
                line.horas_referencia = line._get_estimated_horas_referencia()

    @api.onchange('horas_referencia')
    def _onchange_horas_referencia(self):
        for line in self:
            estimated = line._get_estimated_horas_referencia()
            current = round(line.horas_referencia or 0.0, 2)
            if abs(current - estimated) > 0.0001:
                line.horas_referencia_manual_override = True
                line.horas_referencia_manual = current
            elif line.horas_referencia_manual_override:
                line.horas_referencia_manual = current

    def _estimate_reference_hours(self):
        self.ensure_one()

        quantity = max(self.cantidad or 1, 1)
        volume = max(self.volumen or self.objeto_catalogo_id.volumen_referencia or 0.0, 0.0)
        unit_hours = self._get_hours_base_per_item() + (volume * self._get_hours_volume_factor())

        if volume >= self._get_hours_volume_surcharge_1_threshold():
            unit_hours += self._get_hours_volume_surcharge_1()
        if volume >= self._get_hours_volume_surcharge_2_threshold():
            unit_hours += self._get_hours_volume_surcharge_2()
        if self.embalaje:
            unit_hours += self._get_hours_packing()
        if self.desmontaje:
            unit_hours += self._get_hours_disassembly()

        total_hours = quantity * unit_hours
        total_hours += quantity * self._get_access_hours_per_unit()
        total_hours += self._get_elevador_hours_share()
        return max(total_hours, 0.0)

    def _get_estimated_horas_referencia(self):
        self.ensure_one()
        return round(self._estimate_reference_hours(), 2)

    def _get_effective_horas_referencia(self):
        self.ensure_one()
        if self.horas_referencia_manual_override:
            return round(self.horas_referencia_manual or self.horas_referencia or 0.0, 2)
        return self._get_estimated_horas_referencia()

    def _get_access_hours_per_unit(self):
        self.ensure_one()
        lead = self.lead_id
        if not lead:
            return 0.0
        return (
            self._get_side_access_hours(lead.floorup, lead.elevatorup)
            + self._get_side_access_hours(lead.floordown, lead.elevatordown)
        )

    @staticmethod
    def _get_side_access_hours(floor, elevator):
        floor = max(int(floor or 0), 0)
        if floor <= 1:
            return 0.0
        if elevator == 'tiene':
            return floor * _env_float('MUDANZAS_HOURS_FLOOR_WITH_ELEVATOR', 0.03)
        if elevator == 'no_tiene':
            return floor * _env_float('MUDANZAS_HOURS_FLOOR_NO_ELEVATOR', 0.08)
        return floor * _env_float('MUDANZAS_HOURS_FLOOR_DEFAULT', 0.05)

    def _get_elevador_hours_share(self):
        self.ensure_one()
        lead = self.lead_id
        if not lead or not lead.elevador or not lead.horas_elevador:
            return 0.0

        lines = lead.mudanza_line_ids
        own_weight = self._get_estimation_weight()
        total_weight = sum(line._get_estimation_weight() for line in lines) or own_weight or 1.0
        return lead.horas_elevador * (own_weight / total_weight)

    def _get_estimation_weight(self):
        self.ensure_one()
        quantity = max(self.cantidad or 1, 1)
        minimum_volume = _env_float('MUDANZAS_ESTIMATION_MIN_VOLUME_WEIGHT', 0.5)
        volume = max(self.volumen or self.objeto_catalogo_id.volumen_referencia or minimum_volume, minimum_volume)
        return quantity * volume

    @staticmethod
    def _get_hours_base_per_item():
        return _env_float('MUDANZAS_HOURS_BASE_PER_ITEM', 0.18)

    @staticmethod
    def _get_hours_volume_factor():
        return _env_float('MUDANZAS_HOURS_VOLUME_FACTOR', 0.22)

    @staticmethod
    def _get_hours_volume_surcharge_1_threshold():
        return _env_float('MUDANZAS_HOURS_VOLUME_SURCHARGE_1_THRESHOLD', 1.5)

    @staticmethod
    def _get_hours_volume_surcharge_1():
        return _env_float('MUDANZAS_HOURS_VOLUME_SURCHARGE_1', 0.10)

    @staticmethod
    def _get_hours_volume_surcharge_2_threshold():
        return _env_float('MUDANZAS_HOURS_VOLUME_SURCHARGE_2_THRESHOLD', 2.5)

    @staticmethod
    def _get_hours_volume_surcharge_2():
        return _env_float('MUDANZAS_HOURS_VOLUME_SURCHARGE_2', 0.14)

    @staticmethod
    def _get_hours_packing():
        return _env_float('MUDANZAS_HOURS_PACKING', 0.20)

    @staticmethod
    def _get_hours_disassembly():
        return _env_float('MUDANZAS_HOURS_DISASSEMBLY', 0.35)

    @api.onchange('objeto_catalogo_id')
    def _onchange_objeto_catalogo_id(self):
        for line in self:
            catalog = line.objeto_catalogo_id
            if not catalog:
                continue

            if catalog.is_other:
                line.objeto = line.objeto_manual
                continue

            line.objeto = catalog.name
            line.objeto_manual = False
            line.volumen = catalog.volumen_referencia or 0.0
            if catalog.embalaje_recomendado:
                line.embalaje = True
            if catalog.desmontaje_recomendado:
                line.desmontaje = True
            if not line.horas_referencia_manual_override:
                line.horas_referencia = line._get_estimated_horas_referencia()

    @api.onchange('objeto_manual')
    def _onchange_objeto_manual(self):
        for line in self:
            if line.objeto_catalogo_id and line.objeto_catalogo_id.is_other:
                line.objeto = line.objeto_manual

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        for record, vals in zip(records, vals_list):
            if 'horas_referencia' in vals:
                provided_hours = round(vals.get('horas_referencia') or 0.0, 2)
                estimated_hours = record._get_estimated_horas_referencia()
                if abs(provided_hours - estimated_hours) > 0.0001:
                    super(MudanzasLeadObjectLine, record).write({
                        'horas_referencia_manual_override': True,
                        'horas_referencia_manual': provided_hours,
                    })
                else:
                    record._write_estimated_horas_referencia(estimated_hours)
                continue
            if not record.horas_referencia_manual_override:
                record._write_estimated_horas_referencia(record._get_estimated_horas_referencia())
        return records

    def write(self, vals):
        if self.env.context.get('skip_horas_manual_tracking'):
            return super().write(vals)

        manual_hours_provided = 'horas_referencia' in vals
        res = super().write(vals)
        if manual_hours_provided:
            for line in self:
                current = round(line.horas_referencia or 0.0, 2)
                estimated = line._get_estimated_horas_referencia()
                if abs(current - estimated) > 0.0001:
                    super(MudanzasLeadObjectLine, line).write({
                        'horas_referencia_manual_override': True,
                        'horas_referencia_manual': current,
                    })
                else:
                    line._write_estimated_horas_referencia(estimated)
            return res

        recalc_fields = {
            'cantidad',
            'volumen',
            'embalaje',
            'desmontaje',
            'objeto_catalogo_id',
            'lead_id',
        }
        if recalc_fields.intersection(vals):
            for line in self.filtered(lambda l: not l.horas_referencia_manual_override):
                line._write_estimated_horas_referencia(line._get_estimated_horas_referencia())
        return res

    def _write_estimated_horas_referencia(self, estimated_hours=None):
        self.ensure_one()
        if estimated_hours is None:
            estimated_hours = self._get_estimated_horas_referencia()
        return super(MudanzasLeadObjectLine, self.with_context(skip_horas_manual_tracking=True)).write({
            'horas_referencia_manual_override': False,
            'horas_referencia_manual': 0.0,
            'horas_referencia': round(estimated_hours or 0.0, 2),
        })

    @api.constrains('objeto_catalogo_id', 'objeto_manual')
    def _check_objeto_manual_required(self):
        for line in self:
            if line.objeto_catalogo_id and line.objeto_catalogo_id.is_other and not line.objeto_manual:
                raise ValidationError(_("Debes indicar el nombre en 'Otro objeto'."))


class MudanzasLeadMedia(models.Model):
    _name = 'mudanzas.lead.media'
    _description = 'Archivo multimedia de mudanza'
    _order = 'id desc'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True, ondelete='cascade')
    name = fields.Char(string='Nombre', required=True)
    media_kind = fields.Selection(
        [
            ('photo', 'Foto'),
            ('video', 'Video'),
        ],
        string='Tipo de medio',
        required=True,
        default='photo',
    )
    file_data = fields.Binary(string='Archivo', required=True, attachment=True)
    file_name = fields.Char(string='Nombre de archivo')


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    test_debug_field = fields.Char(string='Test Debug Field')

    # Personal information
    contact_name = fields.Char(string='Contacto')
    email_form = fields.Char(string='Email')
    phone = fields.Char(string='Teléfono')
    partner_vat = fields.Char(
        string='NIF',
        related='partner_id.vat',
        readonly=False,
    )
    partner_category_ids = fields.Many2many(
        'res.partner.category',
        string='Etiquetas del cliente',
        related='partner_id.category_id',
        readonly=False,
    )
    partner_medio_contacto = fields.Selection(
        related='partner_id.medio_contacto',
        string='Medio de contacto',
        readonly=False,
    )
    partner_medio_contacto_otro = fields.Char(
        related='partner_id.medio_contacto_otro',
        string='Otros',
        readonly=False,
    )

    # Mudanza fields (legacy single row + new line array)
    cantidad = fields.Integer(string='Cantidad')
    objeto = fields.Char(string='Objetos')
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
    objeto_manual = fields.Char(string='Otro objeto')
    peso = fields.Float(string='Kg')
    volumen = fields.Float(string='M³')
    embalaje = fields.Boolean(string='Embalaje')
    desmontaje = fields.Boolean(string='Desmontaje')
    habitacion = fields.Selection(selection=HABITACION_SELECTION, string='Habitación')
    mudanza_line_ids = fields.One2many(
        'mudanzas.lead.object.line',
        'lead_id',
        string='Objetos de mudanza',
    )
    mudanza_media_ids = fields.Many2many(
        'ir.attachment',
        'mudanzas_crm_lead_ir_attachment_rel',
        'lead_id',
        'attachment_id',
        string='Multimedia',
        copy=False,
    )
    mudanza_media_preview = fields.Html(
        string='Vista previa multimedia',
        compute='_compute_mudanza_media_preview',
        sanitize=False,
    )
    observaciones_mudanza = fields.Char(string='Observaciones')
    fecha_mudanza = fields.Date(string='Fecha de mudanza')
    horas = fields.Integer(string='Horas estimadas')
    horas_viaje = fields.Integer(string='Horas de viaje', default=0)
    num_operarios_select = fields.Selection(
        selection=OPERARIOS_SELECTION,
        string='Operarios',
        compute='_compute_num_operarios_select',
        inverse='_inverse_num_operarios_select',
    )
    num_operarios = fields.Integer(string='Nº operarios')
    horas_totales_aprox = fields.Float(
        string='Horas totales aprox.',
        compute='_compute_offer_estimations',
        store=True,
        digits=(16, 2),
    )
    precio_sugerido = fields.Float(
        string='Precio sugerido',
        compute='_compute_offer_estimations',
        store=True,
        digits=(16, 2),
    )
    ascensor = fields.Boolean(string='Ascensor')
    mas_de_dos_dias = fields.Boolean(string='Más de 1 Día')
    elevador = fields.Boolean(string='Elevador')
    horas_elevador = fields.Integer(string='Horas de elevador')

    # Offer details
    precio_oferta = fields.Float(string='Precio Oferta')
    tipo_oferta = fields.Selection(
        [
            ('baja', 'Baja'),
            ('media', 'Media'),
            ('alta', 'Alta'),
        ],
        string='Tipo Oferta',
        default='baja',
    )
    offer_include_furniture_handling = fields.Boolean(
        string='Incluir desmontaje/montaje',
        compute='_compute_offer_service_flags',
    )
    offer_include_client_boxes_transport = fields.Boolean(string='Incluir bultos y cajas')
    offer_client_boxes_quantity = fields.Integer(string='Cantidad aprox. bultos/cajas', default=2)
    offer_include_packing_material = fields.Boolean(
        string='Incluir material de embalaje',
        compute='_compute_offer_service_flags',
    )
    offer_include_storage = fields.Boolean(string='Incluir guardamuebles')
    offer_storage_months = fields.Integer(string='Meses de guardamuebles', default=5)
    offer_email_cc = fields.Char(
        string='CC oferta',
        compute='_compute_offer_email_settings',
    )
    offer_email_from = fields.Char(
        string='Remitente oferta',
        compute='_compute_offer_email_settings',
    )
    offer_report_filename = fields.Char(
        string='Nombre PDF oferta',
        compute='_compute_offer_report_filename',
    )

    # carga (pickup) address fields (manual select)
    streetup = fields.Char(string='Calle')
    streetup2 = fields.Char(string='Calle 2')
    floorup = fields.Integer(string='Piso')
    zipup = fields.Char(string='Código Postal')
    doorup = fields.Char(string='Puerta')
    elevatorup = fields.Selection(selection=ELEVATOR_SELECTION, string='Ascensor')

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
    STATE_SELECTION = [(key, key) for key in STATE_PROVINCE_MAP.keys()]
    _ALL_PROVINCES = []
    for _lst in STATE_PROVINCE_MAP.values():
        _ALL_PROVINCES.extend(_lst)
    PROVINCE_SELECTION = sorted([(p, p) for p in set(_ALL_PROVINCES)], key=lambda x: x[0])

    state_up = fields.Selection(selection=STATE_SELECTION, string='Comunidad', default='Comunidad Valenciana')
    province_up = fields.Selection(selection=PROVINCE_SELECTION, string='Provincia', default='Valencia')
    province_up_id = fields.Many2one('mudanzas.province', string='Provincia')
    poblation_up = fields.Char(string='Población')

    # descarga (delivery) address fields (manual select)
    streetdown = fields.Char(string='Calle')
    streetdown2 = fields.Char(string='Calle 2')
    floordown = fields.Integer(string='Piso')
    zipdown = fields.Char(string='Código Postal')
    doordown = fields.Char(string='Puerta')
    elevatordown = fields.Selection(selection=ELEVATOR_SELECTION, string='Ascensor')
    state_down = fields.Selection(selection=STATE_SELECTION, string='Comunidad', default='Comunidad Valenciana')
    province_down = fields.Selection(selection=PROVINCE_SELECTION, string='Provincia', default='Valencia')
    province_down_id = fields.Many2one('mudanzas.province', string='Provincia')
    poblation_down = fields.Char(string='Población')

    @api.depends('mudanza_media_ids', 'mudanza_media_ids.mimetype', 'mudanza_media_ids.name')
    def _compute_mudanza_media_preview(self):
        for lead in self:
            image_attachments = lead.mudanza_media_ids.filtered(
                lambda att: isinstance(att.id, int) and (att.mimetype or '').startswith('image/')
            )
            video_attachments = lead.mudanza_media_ids.filtered(
                lambda att: isinstance(att.id, int) and (att.mimetype or '').startswith('video/')
            )

            photo_section = ''
            video_section = ''

            if image_attachments:
                carousel_id = f'mudanza-media-carousel-{lead.id or "new"}'
                indicators = []
                slides = []
                for index, attachment in enumerate(image_attachments):
                    active_class = ' active' if index == 0 else ''
                    indicators.append(
                        f'<button type="button" data-bs-target="#{carousel_id}" '
                        f'data-bs-slide-to="{index}" class="{active_class.strip()}" '
                        f'aria-current="{"true" if index == 0 else "false"}" '
                        f'aria-label="Slide {index + 1}"></button>'
                    )
                    slides.append(
                        f'''
                        <div class="carousel-item{active_class}">
                          <img src="/web/image/{attachment.id}"
                               alt="{attachment.name or "Foto de mudanza"}"
                               style="width: 100%; height: 560px; object-fit: cover; border-radius: 14px;"/>
                        </div>
                        '''
                    )
                photo_section = (
                    f'''
                    <div style="width: 100%; min-width: 0;">
                      <div style="font-weight: 700; font-size: 18px; margin-bottom: 10px;">Fotos</div>
                      <div id="{carousel_id}" class="carousel slide" data-bs-ride="carousel">
                        <div class="carousel-indicators">
                          {''.join(indicators)}
                        </div>
                        <div class="carousel-inner" style="border-radius: 14px; overflow: hidden; background: #f5f5f5;">
                          {''.join(slides)}
                        </div>
                        <button class="carousel-control-prev" type="button" data-bs-target="#{carousel_id}" data-bs-slide="prev">
                          <span class="carousel-control-prev-icon" aria-hidden="true"></span>
                          <span class="visually-hidden">Previous</span>
                        </button>
                        <button class="carousel-control-next" type="button" data-bs-target="#{carousel_id}" data-bs-slide="next">
                          <span class="carousel-control-next-icon" aria-hidden="true"></span>
                          <span class="visually-hidden">Next</span>
                        </button>
                      </div>
                    </div>
                    '''
                )

            if video_attachments:
                video_cards = []
                for attachment in video_attachments:
                    video_cards.append(
                        f'''
                        <div style="margin-bottom: 16px;">
                          <div style="font-weight: 600; margin-bottom: 8px;">{attachment.name or "Video"}</div>
                          <video controls preload="metadata" style="width: 100%; height: 560px; background: #000; border-radius: 14px; object-fit: contain;">
                            <source src="/web/content/{attachment.id}" type="{attachment.mimetype or "video/mp4"}"/>
                            Tu navegador no soporta video HTML5.
                          </video>
                        </div>
                        '''
                    )
                video_section = (
                    f'''
                    <div style="width: 100%; min-width: 0;">
                      <div style="font-weight: 700; font-size: 18px; margin-bottom: 10px;">Videos</div>
                      {''.join(video_cards)}
                    </div>
                    '''
                )

            if photo_section or video_section:
                lead.mudanza_media_preview = Markup(
                    f'''
                    <div style="display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; width: 100%; margin-top: 16px; align-items: start;">
                      <div style="width: 100%; min-width: 0;">{photo_section}</div>
                      <div style="width: 100%; min-width: 0;">{video_section}</div>
                    </div>
                    '''
                )
            else:
                lead.mudanza_media_preview = False

    @api.depends(
        'embalaje',
        'desmontaje',
        'mudanza_line_ids.embalaje',
        'mudanza_line_ids.desmontaje',
    )
    def _compute_offer_service_flags(self):
        for lead in self:
            line_has_disassembly = any(line.desmontaje for line in lead.mudanza_line_ids)
            line_has_packing = any(line.embalaje for line in lead.mudanza_line_ids)
            lead.offer_include_furniture_handling = bool(lead.desmontaje or line_has_disassembly)
            lead.offer_include_packing_material = bool(lead.embalaje or line_has_packing)

    @api.depends(
        'cantidad',
        'volumen',
        'embalaje',
        'desmontaje',
        'num_operarios',
        'num_operarios_select',
        'objeto_catalogo_id.volumen_referencia',
        'mudanza_line_ids.horas_referencia',
        'mudanza_line_ids.horas_referencia_manual',
        'mudanza_line_ids.horas_referencia_manual_override',
        'mudanza_line_ids.cantidad',
        'mudanza_line_ids.volumen',
        'horas_viaje',
        'floorup',
        'floordown',
        'elevatorup',
        'elevatordown',
        'elevador',
        'horas_elevador',
    )
    def _compute_offer_estimations(self):
        for lead in self:
            reference_hours = lead._get_reference_hours_total()
            inferred_operarios = lead._infer_num_operarios(reference_hours, lead._get_reference_volume_total())
            num_operarios = lead._get_effective_num_operarios(inferred_operarios=inferred_operarios)
            operative_hours = reference_hours / num_operarios if num_operarios else reference_hours
            total_hours = operative_hours + max(lead.horas_viaje or 0, 0)
            lead.horas_totales_aprox = round(total_hours, 2)
            lead.precio_sugerido = round(
                total_hours * lead._get_suggested_hourly_rate(num_operarios),
                2,
            )
            lead.tipo_oferta = lead._get_tipo_oferta_by_amount(lead.precio_sugerido)

    @api.depends(
        'num_operarios',
        'cantidad',
        'volumen',
        'embalaje',
        'desmontaje',
        'objeto_catalogo_id.volumen_referencia',
        'mudanza_line_ids.horas_referencia',
        'mudanza_line_ids.horas_referencia_manual',
        'mudanza_line_ids.horas_referencia_manual_override',
        'mudanza_line_ids.cantidad',
        'mudanza_line_ids.volumen',
        'horas_viaje',
        'floorup',
        'floordown',
        'elevatorup',
        'elevatordown',
        'elevador',
        'horas_elevador',
    )
    def _compute_num_operarios_select(self):
        for lead in self:
            inferred_operarios = lead._infer_num_operarios(
                lead._get_reference_hours_total(),
                lead._get_reference_volume_total(),
            )
            effective_operarios = lead._get_effective_num_operarios(inferred_operarios=inferred_operarios)
            lead.num_operarios_select = str(effective_operarios)

    def _inverse_num_operarios_select(self):
        for lead in self:
            lead.num_operarios = lead._sanitize_num_operarios(lead.num_operarios_select)

    @api.onchange('num_operarios_select')
    def _onchange_num_operarios_select(self):
        for lead in self:
            lead.num_operarios = lead._sanitize_num_operarios(lead.num_operarios_select)
        self._refresh_offer_estimation_preview()

    @api.depends_context('uid')
    def _compute_offer_email_settings(self):
        user_email = self.env.user.email or False
        for lead in self:
            lead.offer_email_cc = user_email
            lead.offer_email_from = False

    @api.depends('partner_id.name', 'contact_name', 'name', 'create_date')
    def _compute_offer_report_filename(self):
        for lead in self:
            lead.offer_report_filename = lead._get_offer_report_filename()

    @api.onchange('state_up')
    def _onchange_state_up(self):
        if self.state_up:
            provinces = self.STATE_PROVINCE_MAP.get(self.state_up, [])
            if self.province_up and self.province_up not in provinces:
                self.province_up = False
            if self.province_up_id and self.province_up_id.name not in provinces:
                self.province_up_id = False
            if not self.province_up_id and provinces:
                self.province_up_id = self.env['mudanzas.province'].search(
                    [('state', '=', self.state_up), ('name', 'in', provinces)],
                    limit=1,
                )

    @api.onchange('state_down')
    def _onchange_state_down(self):
        if self.state_down:
            provinces = self.STATE_PROVINCE_MAP.get(self.state_down, [])
            if self.province_down and self.province_down not in provinces:
                self.province_down = False
            if self.province_down_id and self.province_down_id.name not in provinces:
                self.province_down_id = False
            if not self.province_down_id and provinces:
                self.province_down_id = self.env['mudanzas.province'].search(
                    [('state', '=', self.state_down), ('name', 'in', provinces)],
                    limit=1,
                )

    @api.onchange('floorup', 'floordown', 'elevatorup', 'elevatordown', 'elevador', 'horas_elevador')
    def _onchange_access_estimation_inputs(self):
        self._refresh_non_manual_line_hours()
        self._refresh_offer_estimation_preview()

    @api.onchange('precio_oferta')
    def _onchange_precio_oferta(self):
        self.expected_revenue = self.precio_oferta or 0.0
        if self.precio_oferta < 500:
            self.tipo_oferta = 'baja'
        elif self.precio_oferta <= 700:
            self.tipo_oferta = 'media'
        else:
            self.tipo_oferta = 'alta'

    @api.onchange('expected_revenue')
    def _onchange_expected_revenue(self):
        self.precio_oferta = self.expected_revenue or 0.0

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

    @api.model_create_multi
    def create(self, vals_list):
        prepared_vals_list = []
        for vals in vals_list:
            prepared_vals = self._prepare_offer_vals(dict(vals))
            prepared_vals = self._prepare_objeto_vals(prepared_vals)
            prepared_vals_list.append(prepared_vals)

        leads = super().create(prepared_vals_list)
        for lead, vals in zip(leads, prepared_vals_list):
            if lead._access_estimation_fields().intersection(vals):
                lead._refresh_non_manual_line_hours()
        return leads

    def write(self, vals):
        if 'objeto_catalogo_id' in vals or 'objeto_manual' in vals:
            for lead in self:
                lead_vals = lead._prepare_offer_vals(dict(vals))
                lead_vals = lead._prepare_objeto_vals(lead_vals)
                super(CrmLead, lead).write(lead_vals)
                if lead._access_estimation_fields().intersection(lead_vals):
                    lead._refresh_non_manual_line_hours()
            return True

        vals = self._prepare_offer_vals(vals)
        vals = self._prepare_objeto_vals(vals)
        res = super().write(vals)
        if self._access_estimation_fields().intersection(vals):
            self._refresh_non_manual_line_hours()
        return res

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
            lead.volumen = catalog.volumen_referencia or 0.0
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
        if not vals.get('volumen') and catalog.volumen_referencia:
            vals['volumen'] = catalog.volumen_referencia
        if catalog.embalaje_recomendado:
            vals.setdefault('embalaje', True)
        if catalog.desmontaje_recomendado:
            vals.setdefault('desmontaje', True)
        return vals

    def _prepare_offer_vals(self, vals):
        if 'expected_revenue' not in vals and 'precio_oferta' not in vals:
            return vals

        source_value = vals.get('expected_revenue', vals.get('precio_oferta'))
        if source_value in (False, None):
            source_value = 0.0

        vals['expected_revenue'] = source_value
        vals['precio_oferta'] = source_value
        return vals

    @staticmethod
    def _access_estimation_fields():
        return {'floorup', 'floordown', 'elevatorup', 'elevatordown', 'elevador', 'horas_elevador'}

    def _refresh_non_manual_line_hours(self):
        for lead in self:
            for line in lead.mudanza_line_ids.filtered(lambda l: not l.horas_referencia_manual_override):
                estimated_hours = line._get_estimated_horas_referencia()
                if line._origin and line._origin.id:
                    line._write_estimated_horas_referencia(estimated_hours)
                else:
                    line.horas_referencia = estimated_hours

    def _refresh_offer_estimation_preview(self):
        self._compute_num_operarios_select()
        self._compute_offer_estimations()

    def _get_reference_hours_total(self):
        self.ensure_one()
        if self.mudanza_line_ids:
            return sum(line._get_effective_horas_referencia() for line in self.mudanza_line_ids)
        return self._estimate_legacy_reference_hours()

    def _get_reference_volume_total(self):
        self.ensure_one()
        if self.mudanza_line_ids:
            return sum(
                max(line.cantidad or 1, 1) * max(line.volumen or line.objeto_catalogo_id.volumen_referencia or 0.0, 0.0)
                for line in self.mudanza_line_ids
            )
        return max(self.cantidad or 1, 1) * max(self.volumen or self.objeto_catalogo_id.volumen_referencia or 0.0, 0.0)

    def _estimate_legacy_reference_hours(self):
        self.ensure_one()

        quantity = max(self.cantidad or 1, 1)
        volume = max(self.volumen or self.objeto_catalogo_id.volumen_referencia or 0.0, 0.0)
        unit_hours = (
            MudanzasLeadObjectLine._get_hours_base_per_item()
            + (volume * MudanzasLeadObjectLine._get_hours_volume_factor())
        )

        if volume >= MudanzasLeadObjectLine._get_hours_volume_surcharge_1_threshold():
            unit_hours += MudanzasLeadObjectLine._get_hours_volume_surcharge_1()
        if volume >= MudanzasLeadObjectLine._get_hours_volume_surcharge_2_threshold():
            unit_hours += MudanzasLeadObjectLine._get_hours_volume_surcharge_2()
        if self.embalaje:
            unit_hours += MudanzasLeadObjectLine._get_hours_packing()
        if self.desmontaje:
            unit_hours += MudanzasLeadObjectLine._get_hours_disassembly()

        total_hours = quantity * unit_hours
        total_hours += quantity * self._get_access_hours_per_unit()
        total_hours += self.horas_elevador if self.elevador and self.horas_elevador else 0.0
        return max(total_hours, 0.0)

    def _get_access_hours_per_unit(self):
        self.ensure_one()
        return (
            self._get_side_access_hours(self.floorup, self.elevatorup)
            + self._get_side_access_hours(self.floordown, self.elevatordown)
        )

    @staticmethod
    def _get_side_access_hours(floor, elevator):
        floor = max(int(floor or 0), 0)
        if floor <= 1:
            return 0.0
        if elevator == 'tiene':
            return floor * 0.03
        if elevator == 'no_tiene':
            return floor * 0.08
        return floor * 0.05

    @staticmethod
    def _get_suggested_hourly_rate(num_operarios):
        num_operarios = CrmLead._sanitize_num_operarios(num_operarios) or 2
        base_rate = _env_float('MUDANZAS_RATE_2_OPERARIOS', 75.0)
        per_operario_increment = _env_float('MUDANZAS_RATE_OPERARIO_INCREMENT', 20.0)
        return base_rate + max(num_operarios - 2, 0) * per_operario_increment

    @staticmethod
    def _get_tipo_oferta_by_amount(amount):
        amount = amount or 0.0
        if amount > _env_float('MUDANZAS_TIPO_OFERTA_ALTA_MIN', 700.0):
            return 'alta'
        if amount > _env_float('MUDANZAS_TIPO_OFERTA_MEDIA_MIN', 500.0):
            return 'media'
        return 'baja'

    @staticmethod
    def _sanitize_num_operarios(value):
        try:
            value = int(value or 0)
        except (TypeError, ValueError):
            return 0
        return max(1, min(value, 10)) if value else 0

    @staticmethod
    def _infer_num_operarios(reference_hours, total_volume):
        if (
            reference_hours >= _env_float('MUDANZAS_OPERARIOS_HOURS_5_MIN', 24.0)
            or total_volume >= _env_float('MUDANZAS_OPERARIOS_VOLUME_5_MIN', 38.0)
        ):
            return 5
        if (
            reference_hours >= _env_float('MUDANZAS_OPERARIOS_HOURS_4_MIN', 16.0)
            or total_volume >= _env_float('MUDANZAS_OPERARIOS_VOLUME_4_MIN', 24.0)
        ):
            return 4
        if (
            reference_hours >= _env_float('MUDANZAS_OPERARIOS_HOURS_3_MIN', 8.0)
            or total_volume >= _env_float('MUDANZAS_OPERARIOS_VOLUME_3_MIN', 12.0)
        ):
            return 3
        return _env_int('MUDANZAS_OPERARIOS_DEFAULT', 2)

    def _get_effective_num_operarios(self, inferred_operarios=None):
        self.ensure_one()
        if inferred_operarios is None:
            inferred_operarios = self._infer_num_operarios(
                self._get_reference_hours_total(),
                self._get_reference_volume_total(),
            )
        return (
            self._sanitize_num_operarios(self.num_operarios_select)
            or self._sanitize_num_operarios(self.num_operarios)
            or inferred_operarios
        )

    def _get_offer_client_name(self):
        self.ensure_one()
        value = self.partner_id.name or self.contact_name or self.name or _('Cliente')
        return self._repair_report_text(value)

    def _repair_report_text(self, value):
        if not isinstance(value, str):
            return value
        if '\u00c3' not in value and '\u00c2' not in value:
            return value
        try:
            return value.encode('latin1').decode('utf-8')
        except (UnicodeEncodeError, UnicodeDecodeError):
            return value

    def _get_offer_report_date(self):
        self.ensure_one()
        return fields.Date.to_string(self.create_date.date()) if self.create_date else fields.Date.to_string(fields.Date.context_today(self))

    def _get_offer_current_date(self):
        self.ensure_one()
        return fields.Date.to_string(fields.Date.context_today(self))

    def _get_offer_report_filename(self):
        self.ensure_one()
        client_name = ' '.join((self._get_offer_client_name() or '').split()) or 'Cliente'
        safe_client_name = client_name.replace('/', '-').replace('\\', '-')
        return f"Presupuesto {safe_client_name} {self._get_offer_report_date()}"

    def _get_offer_lines_for_report(self):
        self.ensure_one()
        if self.mudanza_line_ids:
            return [
                {
                    'cantidad': line.cantidad or 1,
                    'nombre': self._repair_report_text(line.objeto_manual or line.objeto_catalogo_id.name or line.objeto or _('Objeto sin nombre')),
                    'volumen': line.volumen or 0.0,
                    'embalaje': line.embalaje,
                    'desmontaje': line.desmontaje,
                    'habitacion': self._repair_report_text(dict(line._fields['habitacion'].selection).get(line.habitacion, '')),
                }
                for line in self.mudanza_line_ids
            ]
        return [{
            'cantidad': self.cantidad or 1,
            'nombre': self._repair_report_text(self.objeto_manual or self.objeto_catalogo_id.name or self.objeto or _('Objeto sin nombre')),
            'volumen': self.volumen or 0.0,
            'embalaje': self.embalaje,
            'desmontaje': self.desmontaje,
            'habitacion': self._repair_report_text(dict(self._fields['habitacion'].selection).get(self.habitacion, '')),
        }]

    def _get_offer_address_lines(self, move_type):
        self.ensure_one()
        if move_type == 'pickup':
            values = [
                self.streetup,
                self.streetup2,
                self.zipup,
                self.doorup,
                self.elevatorup,
                self.floorup and _('Piso %s') % self.floorup,
                self.state_up,
                self.province_up_id.name if self.province_up_id else self.province_up,
                self.poblation_up,
            ]
        else:
            values = [
                self.streetdown,
                self.streetdown2,
                self.zipdown,
                self.doordown,
                self.elevatordown,
                self.floordown and _('Piso %s') % self.floordown,
                self.state_down,
                self.province_down_id.name if self.province_down_id else self.province_down,
                self.poblation_down,
            ]
        return [self._repair_report_text(value) for value in values if value]

    def _get_offer_address_entries(self, move_type):
        self.ensure_one()

        def _label(field_name):
            return self._repair_report_text(self._fields[field_name].string or field_name)

        def _selection_value(field_name, value):
            if not value:
                return value
            selection = dict(self._fields[field_name].selection or [])
            return selection.get(value, value)

        if move_type == 'pickup':
            entries = [
                (_label('streetup'), self.streetup),
                (_label('streetup2'), self.streetup2),
                (_label('zipup'), self.zipup),
                (_label('doorup'), self.doorup),
                (_label('elevatorup'), _selection_value('elevatorup', self.elevatorup)),
                (_label('floorup'), self.floorup),
                (_label('state_up'), self.state_up),
                (_label('province_up_id'), self.province_up_id.name if self.province_up_id else self.province_up),
                (_label('poblation_up'), self.poblation_up),
            ]
        else:
            entries = [
                (_label('streetdown'), self.streetdown),
                (_label('streetdown2'), self.streetdown2),
                (_label('zipdown'), self.zipdown),
                (_label('doordown'), self.doordown),
                (_label('elevatordown'), _selection_value('elevatordown', self.elevatordown)),
                (_label('floordown'), self.floordown),
                (_label('state_down'), self.state_down),
                (_label('province_down_id'), self.province_down_id.name if self.province_down_id else self.province_down),
                (_label('poblation_down'), self.poblation_down),
            ]

        return [
            {
                'label': label,
                'value': self._repair_report_text(value),
            }
            for label, value in entries if value not in (False, None, '')
        ]

    def action_send_offer_email(self):
        self.ensure_one()
        if not self.email_from:
            raise UserError(_("El lead no tiene email. Completa el campo 'Email' antes de enviar la oferta."))

        template = self.env.ref('mudanzas_crm.mail_template_mudanza_oferta', raise_if_not_found=False)
        if not template:
            raise UserError(_("No se encontro la plantilla de correo de oferta."))

        return {
            'type': 'ir.actions.act_window',
            'res_model': 'mail.compose.message',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_model': 'crm.lead',
                'default_res_ids': [self.id],
                'default_use_template': bool(template.id),
                'default_template_id': template.id,
                'default_composition_mode': 'comment',
                'force_email': True,
            },
        }


class MailTemplate(models.Model):
    _inherit = 'mail.template'

    @api.model
    def mudanzas_set_offer_lang(self):
        template = self.env.ref('mudanzas_crm.mail_template_mudanza_oferta', raise_if_not_found=False)
        if not template:
            return

        lang_model = self.env['res.lang'].sudo()
        selected_code = False
        for code in ('es_AR', 'es_ES'):
            if lang_model.search([('code', '=', code)], limit=1):
                selected_code = code
                break

        if not selected_code:
            spanish_lang = lang_model.search([('code', 'like', 'es_%')], limit=1)
            selected_code = spanish_lang.code if spanish_lang else False

        template.sudo().write({'lang': selected_code})


class ResPartner(models.Model):
    _inherit = 'res.partner'

    medio_contacto = fields.Selection(
        [
            ('whatsapp', 'WhatsApp'),
            ('formulario_web', 'Formulario Web'),
            ('visita', 'Visita'),
            ('llamada_otros', 'Otros (indicar en campo "Otros")'),
        ],
        string='Medio de contacto',
    )
    medio_contacto_otro = fields.Char(string='Otros')

    @api.constrains('medio_contacto', 'medio_contacto_otro')
    def _check_medio_contacto_otro(self):
        for partner in self:
            if partner.medio_contacto == 'llamada_otros' and not partner.medio_contacto_otro:
                raise ValidationError(_("Debes indicar el valor de 'Otros'."))

