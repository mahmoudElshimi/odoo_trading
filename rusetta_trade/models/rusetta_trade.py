from odoo import models, fields, api
from datetime import datetime

class RusettaTrade(models.Model):
    _name = 'rusetta.trade'
    _description = 'Trade Record'
    _rec_name = "create_date"
    _order = 'create_date desc'
    _inherit = ["mail.thread", "mail.activity.mixin"]

    lot_size = fields.Float(string="Lot Size", required=True)
    opt_type = fields.Selection([
        ('buy', 'Buy'),
        ('sell', 'Sell')
    ], string="Operation Type", required=True, default='buy')
    
    entry_price = fields.Float("Entry Price", digits=(16, 5))
    close_price = fields.Float("Close Price", digits=(16, 5))
    take_profit = fields.Float("Take Profit", digits=(16, 5))
    stop_loss = fields.Float("Stop Loss", digits=(16, 5))

    profit = fields.Float(string="Desired Profit")
    loss = fields.Float(string="Desired Loss")
    

    state = fields.Selection(
        [
        ('draft', 'Draft'),
        ('running', 'Running'),
        ('closed', 'Closed'),
        ('canceled', 'Canceled'),
        ], default='draft', string="Status", tracking=True)

    start_time = fields.Datetime(string="Start Time")
    close_time = fields.Datetime(string="Close Time")
    final_profit = fields.Float(string="Final Profit", readonly=True)

    @api.onchange('profit', 'loss', 'lot_size', 'entry_price', 'opt_type')
    def _onchange_profit_loss(self):
        """Auto recalculate T/P and S/L if profit/loss changes."""
        if self.entry_price and self.lot_size:
            std_lot = 100000
            change_profit = (self.profit or 0) / (self.lot_size * std_lot)
            change_loss = abs(self.loss or 0) / (self.lot_size * std_lot)
            if self.opt_type == 'sell':
                self.take_profit = self.entry_price - change_profit
                self.stop_loss = self.entry_price + change_loss
            else:
                self.take_profit = self.entry_price + change_profit
                self.stop_loss = self.entry_price - change_loss

    @api.onchange('take_profit', 'stop_loss')
    def _onchange_tp_sl(self):
        """Recalculate profit/loss if T/P or S/L is changed."""
        if self.entry_price and self.lot_size:
            std_lot = 100000
            if self.opt_type == 'sell':
                self.profit = (self.entry_price - (self.take_profit or 0)) * (self.lot_size * std_lot)
                self.loss = ((self.stop_loss or 0) - self.entry_price) * (self.lot_size * std_lot)
            else:
                self.profit = ((self.take_profit or 0) - self.entry_price) * (self.lot_size * std_lot)
                self.loss = (self.entry_price - (self.stop_loss or 0)) * (self.lot_size * std_lot)

    def action_run(self):
        """Move to running state and set start time."""
        self.write({
            'state': 'running',
            'start_time': datetime.now()
        })

    def action_cancel(self):
        for rec in self:
            rec.state = 'canceled'

    def action_close(self):
        """Move to closed state and calculate final profit."""
        for rec in self:
            if not rec.close_price:
                raise ValueError("Please enter Close Price before closing.")
            lot_unit = rec.lot_size * 100000
            change = rec.close_price - rec.entry_price
            if rec.opt_type == 'sell':
                change = -change
            rec.final_profit = round(lot_unit * change, 2)
            rec.write({
                'state': 'closed',
                'close_time': datetime.now()
            })

