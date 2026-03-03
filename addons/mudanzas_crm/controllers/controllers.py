# from odoo import http


# class MiPrimerModulo(http.Controller):
#     @http.route('/mudanzas_crm/mudanzas_crm', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mudanzas_crm/mudanzas_crm/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mudanzas_crm.listing', {
#             'root': '/mudanzas_crm/mudanzas_crm',
#             'objects': http.request.env['mudanzas_crm.mudanzas_crm'].search([]),
#         })

#     @http.route('/mudanzas_crm/mudanzas_crm/objects/<model("mudanzas_crm.mudanzas_crm"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mudanzas_crm.object', {
#             'object': obj
#         })

