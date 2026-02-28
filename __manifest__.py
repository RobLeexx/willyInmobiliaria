{
    'name': "mudanzas_crm",

    'summary': "Short (1 phrase/line) summary of the module's purpose",

    'description': """
Long description of module's purpose
    """,
        'name': "mudanzas_crm",
        'version': '0.1',
        'license': 'LGPL-3',
        'category': 'Sales/CRM',
        'summary': "Hide company fields in CRM leads",
        'description': """Hide partner_id and partner_name from CRM Lead form.""",
        'author': "Mudanzas Willy",
        'website': "https://mudanzaswilly.com/",
        'depends': ['base', 'crm'],
    'author': "Mudanzas Willy",
    # Categories can be used to filter modules in modules listing
    # for the full list
    'depends': ['base', 'crm'],

    # always loaded
    'data': [
        'security/ir.model.access.csv',
        'data/provinces.xml',
        'views/views.xml',
        'views/crm_lead_inherit.xml',
        'views/templates.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'mudanzas_crm/static/src/js/mudanzas_province_widget.js',
        ],
    },
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}

