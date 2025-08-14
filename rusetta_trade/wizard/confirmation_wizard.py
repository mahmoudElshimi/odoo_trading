from odoo import models, fields, api
from odoo.exceptions import UserError

class ConfirmationWizard(models.TransientModel):
    _name = "confirmation.wizard"
    _description = "Close Trade Wizard"

    trade_id = fields.Many2one("rusetta.trade", string="Trade", required=True)
    market_price = fields.Float(string="Market Price", digits=(16, 5))

    @api.model
    def default_get(self, fields_list):
        """Pre-fill market_price based on trade's opt_type (Bid for Buy, Ask for Sell)."""
        res = super().default_get(fields_list)
        trade = self.env['rusetta.trade'].browse(self._context.get('active_id'))
        if trade:
            trade._fetch_and_update_forex_data()
            if trade.opt_type == 'buy':
                res['market_price'] = trade.bid
            else:
                res['market_price'] = trade.ask
            res['trade_id'] = trade.id
        return res

    def confirm_close(self):
        self.ensure_one()
        if not self.market_price:
            raise UserError("Please enter the market price before closing.")

        self.trade_id.close_price = self.market_price
        self.trade_id.action_close()

        return {"type": "ir.actions.act_window_close"}

