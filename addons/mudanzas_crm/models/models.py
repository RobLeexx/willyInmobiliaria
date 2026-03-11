from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from markupsafe import Markup


class MudanzasProvince(models.Model):
    _name = 'mudanzas.province'
    _description = 'Province for Mudanzas'

    name = fields.Char(string='Provincia', required=True)
    state = fields.Char(string='Comunidad')


class MudanzasObjectCatalog(models.Model):
    _name = 'mudanzas.object.catalog'
    _description = 'Catalogo de objetos para mudanza'
    _order = 'sequence, name'

    _REFERENCE_VOLUME_BY_XMLID = {
        'objeto_catalogo_cama_matrimonial': 1.71,
        'objeto_catalogo_cama_individual': 1.0,
        'objeto_catalogo_cuna': 0.57,
        'objeto_catalogo_colchon': 0.71,
        'objeto_catalogo_armario_2': 2.57,
        'objeto_catalogo_armario_4': 4.86,
        'objeto_catalogo_mesita_noche': 0.34,
        'objeto_catalogo_comoda': 1.14,
        'objeto_catalogo_tocador': 1.0,
        'objeto_catalogo_zapatero': 0.71,
        'objeto_catalogo_sofa_3': 2.14,
        'objeto_catalogo_sofa_2': 1.57,
        'objeto_catalogo_sillon': 1.0,
        'objeto_catalogo_mueble_tv': 1.0,
        'objeto_catalogo_mesa_centro': 0.57,
        'objeto_catalogo_librero': 1.29,
        'objeto_catalogo_aparador': 1.43,
        'objeto_catalogo_puff': 0.23,
        'objeto_catalogo_lampara_pie': 0.2,
        'objeto_catalogo_mesa_comedor_grande': 1.71,
        'objeto_catalogo_mesa_comedor_pequena': 1.0,
        'objeto_catalogo_silla_comedor': 0.2,
        'objeto_catalogo_frigorifico': 2.43,
        'objeto_catalogo_lavadora_secadora': 2.0,
        'objeto_catalogo_lavavajillas': 1.43,
        'objeto_catalogo_microondas': 0.43,
        'objeto_catalogo_horno_cocina': 1.86,
        'objeto_catalogo_alacena': 1.29,
        'objeto_catalogo_escritorio': 1.0,
        'objeto_catalogo_silla_ergonomica': 0.4,
        'objeto_catalogo_archivador': 0.86,
        'objeto_catalogo_estanteria_metalica': 1.14,
        'objeto_catalogo_monitor_pc': 0.34,
        'objeto_catalogo_impresora_grande': 0.71,
        'objeto_catalogo_caja_pequena': 0.43,
        'objeto_catalogo_caja_grande': 0.29,
        'objeto_catalogo_espejo_grande': 0.34,
        'objeto_catalogo_cuadro': 0.11,
        'objeto_catalogo_alfombra': 0.23,
        'objeto_catalogo_bicicleta': 0.37,
        'objeto_catalogo_planta_grande': 0.51,
        'objeto_catalogo_maleta': 0.34,
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
    def sync_reference_volumes(self):
        for xmlid_suffix, volume in self._REFERENCE_VOLUME_BY_XMLID.items():
            record = self.env.ref(f'mudanzas_crm.{xmlid_suffix}', raise_if_not_found=False)
            if record:
                record.write({'volumen_referencia': volume})


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
    volumen = fields.Float(string='M³')
    embalaje = fields.Boolean(string='Embalaje')
    desmontaje = fields.Boolean(string='Desmontaje')
    habitacion = fields.Selection(selection=HABITACION_SELECTION, string='Habitación')

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

    @api.onchange('objeto_manual')
    def _onchange_objeto_manual(self):
        for line in self:
            if line.objeto_catalogo_id and line.objeto_catalogo_id.is_other:
                line.objeto = line.objeto_manual

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

    @api.model
    def create(self, vals):
        vals = self._prepare_offer_vals(vals)
        vals = self._prepare_objeto_vals(vals)
        return super().create(vals)

    def write(self, vals):
        if 'objeto_catalogo_id' in vals or 'objeto_manual' in vals:
            for lead in self:
                lead_vals = lead._prepare_offer_vals(dict(vals))
                lead_vals = lead._prepare_objeto_vals(lead_vals)
                super(CrmLead, lead).write(lead_vals)
            return True

        vals = self._prepare_offer_vals(vals)
        vals = self._prepare_objeto_vals(vals)
        return super().write(vals)

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

    def _get_offer_client_name(self):
        self.ensure_one()
        return self.partner_id.name or self.contact_name or self.name or _('Cliente')

    def _get_offer_report_date(self):
        self.ensure_one()
        return fields.Date.to_string(self.create_date.date()) if self.create_date else fields.Date.to_string(fields.Date.context_today(self))

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
                    'nombre': line.objeto_manual or line.objeto_catalogo_id.name or line.objeto or _('Objeto sin nombre'),
                    'volumen': line.volumen or 0.0,
                    'embalaje': line.embalaje,
                    'desmontaje': line.desmontaje,
                    'habitacion': dict(line._fields['habitacion'].selection).get(line.habitacion, ''),
                }
                for line in self.mudanza_line_ids
            ]
        return [{
            'cantidad': self.cantidad or 1,
            'nombre': self.objeto_manual or self.objeto_catalogo_id.name or self.objeto or _('Objeto sin nombre'),
            'volumen': self.volumen or 0.0,
            'embalaje': self.embalaje,
            'desmontaje': self.desmontaje,
            'habitacion': dict(self._fields['habitacion'].selection).get(self.habitacion, ''),
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
        return [value for value in values if value]

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
