{
    "name": "Rusetta Trading Manager",
    "summary": "Trading Platform",
    "depends": ["base", "mail"],
    "author": "Mahmoud ElShimi",
    "website": "mailto:mahmoudelshimi@protonmail.ch",
    "category": "Trading",
    "version": "1.0",
    "license": "Other proprietary",  # See LICENSE(MIT/X) File in the same dir.
    #"images": [
    #    "images/student.png",
    #    "images/attendance.png",
    #    "images/exam.png",
    #    "static/description/banner.png",
    #    "images/banner.png",
    #],
    'data': [
        'security/ir.model.access.csv',
        'views/rusetta_trade_views.xml',
        'views/rusetta_trade_menus.xml',
    ],
    "installable": True,
    "application": True,
}
