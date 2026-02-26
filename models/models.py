from odoo import models, fields, api, _
from odoo.exceptions import UserError


class CrmLead(models.Model):
    _inherit = 'crm.lead'

    @api.model
    def create(self, vals):
        partner_id = vals.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.is_company:
                raise UserError(_("You can only create leads linked to contacts, not companies."))
        return super().create(vals)

    def write(self, vals):
        partner_id = vals.get('partner_id')
        if partner_id:
            partner = self.env['res.partner'].browse(partner_id)
            if partner.is_company:
                raise UserError(_("Leads must be associated with contacts, not companies."))
        return super().write(vals)



# class mi_primer_modulo(models.Model):
#     _name = 'mi_primer_modulo.mi_primer_modulo'
#     _description = 'mi_primer_modulo.mi_primer_modulo'

#     name = fields.Char()
#     value = fields.Integer()
#     value2 = fields.Float(compute="_value_pc", store=True)
#     description = fields.Text()
#
#     @api.depends('value')
#     def _value_pc(self):
#         for record in self:
#             record.value2 = float(record.value) / 100

