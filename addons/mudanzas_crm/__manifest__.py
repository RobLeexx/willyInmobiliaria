{
    'name': 'mudanzas_crm',
    'version': '0.1',
    'license': 'LGPL-3',
    'category': 'Sales/CRM',
    'summary': 'Mudanza CRM',
    'description': 'CRM module for mudanzas.',
    'author': 'Mudanzas Willy',
    'website': 'https://mudanzaswilly.com/',
    'depends': ['base', 'web', 'crm', 'auth_signup'],
    'data': [
        'security/ir.model.access.csv',
        'data/provinces.xml',
        'data/auth_config.xml',
        'data/object_catalog.xml',
        'data/object_catalog_sync.xml',
        'report/offer_report.xml',
        'data/mail_template.xml',
        'views/views.xml',
        'views/crm_lead_inherit.xml',
        'views/res_partner_inherit.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mudanzas_crm/static/src/scss/crm_lead_form.scss',
        ],
    },
    'demo': [
        'demo/demo.xml',
    ],
}

