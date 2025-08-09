from odoo import http
from odoo.http import request

class RusettaTradeDashboard(http.Controller):
    @http.route('/rusetta_trade/dashboard', auth='user', website=True)
    def dashboard(self):
        return request.render('rusetta_trade.dashboard_template')

