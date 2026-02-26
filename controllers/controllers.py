# from odoo import http


# class MiPrimerModulo(http.Controller):
#     @http.route('/mi_primer_modulo/mi_primer_modulo', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/mi_primer_modulo/mi_primer_modulo/objects', auth='public')
#     def list(self, **kw):
#         return http.request.render('mi_primer_modulo.listing', {
#             'root': '/mi_primer_modulo/mi_primer_modulo',
#             'objects': http.request.env['mi_primer_modulo.mi_primer_modulo'].search([]),
#         })

#     @http.route('/mi_primer_modulo/mi_primer_modulo/objects/<model("mi_primer_modulo.mi_primer_modulo"):obj>', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('mi_primer_modulo.object', {
#             'object': obj
#         })

