from odoo import http
from odoo.http import request
from odoo.addons.auth_signup.controllers.main import AuthSignupHome


class MudanzasAuthHome(AuthSignupHome):

    @http.route('/web/login', type='http', auth='none', readonly=False)
    def web_login(self, redirect=None, **kw):
        response = super().web_login(redirect=redirect, **kw)
        qcontext = getattr(response, 'qcontext', None)
        if qcontext is not None:
            qcontext['signup_enabled'] = False
            qcontext['debug'] = ''
        return response

    @http.route('/web/signup', type='http', auth='public', website=True, sitemap=False)
    def web_auth_signup(self, *args, **kw):
        return request.redirect('/web/login', code=303)

    @http.route('/web/become', type='http', auth='user', sitemap=False, readonly=True)
    def switch_to_admin(self):
        return request.redirect('/web/login', code=303)
