{
    "name": "Rusetta Trading Manager",
    "summary": "Trading Platform",
    "depends": ["base", "mail"],
    "author": "Mahmoud ElShimi",
    "website": "mailto:mahmoudelshimi@protonmail.ch",
    "category": "Trading",
    "version": "1.0",
    "license": "Other proprietary",  # See LICENSE(MIT/X) File in the same dir.
    "images": [
        "images/list_view.png",
        "images/form_view.png",
    ],
    #'qweb': [
    #    'static/src/xml/card_templates.xml',
    #],
    'data': [
        'security/ir.model.access.csv',
        'wizard/confirmation_wizard.xml',
        'views/dashboard_template.xml',
        'views/rusetta_trade_views.xml',
        'views/rusetta_trade_menus.xml',
    ],
    "installable": True,
    "application": True,
}
