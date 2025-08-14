import os
import requests
from datetime import datetime, timedelta
from odoo import models, fields, api
from odoo.exceptions import UserError

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
        ], default='draft', string="Status", tracking=True
    )

    start_time = fields.Datetime(string="Start Time")
    close_time = fields.Datetime(string="Close Time")

    bid = fields.Float(string="Bid", digits=(16, 5), readonly=True)
    ask = fields.Float(string="Ask", digits=(16, 5), readonly=True)
    open_ = fields.Float(string="Open", digits=(16, 5), readonly=True)
    low = fields.Float(string="Low", digits=(16, 5), readonly=True)
    high = fields.Float(string="High", digits=(16, 5), readonly=True)
    change = fields.Float(string="Change", digits=(16, 5), readonly=True)
    api_time = fields.Datetime(string="Data Update Date", readonly=True)

    current_profit = fields.Float(string="Current Profit", digits=(16, 2), readonly=True)
    final_profit = fields.Float(string="Final Profit", digits=(16, 2), readonly=True)

    API_URL = "https://financialmodelingprep.com/api/v3/forex/EURUSD"

    @api.model
    def _get_api_key(self):
        """Fetch API key from system parameters, then env variable, else raise error."""
        param_key = self.env['ir.config_parameter'].sudo().get_param('rusetta_trade.api_key')
        if param_key:
            return param_key

        env_key = os.getenv('RUSETTA_API_KEY')
        if env_key:
            return env_key

        raise UserError("No API key found. Please set one in Settings > Technical > System Parameters "
                        "with key 'rusetta_trade.api_key' or in the environment variable 'RUSETTA_API_KEY'.")

    @api.model
    def create(self, vals):
        record = super().create(vals)
        record._fetch_and_update_forex_data()
        return record


    @api.model
    def write(self, vals):
        for rec in self:
            # Completely block edits for closed or canceled trades
            if rec.state in ('close', 'cancel'):
                raise UserError("You cannot modify a closed or canceled trade.")

            protected_fields_running = {'entry_price', 'opt_type', 'lot_size'}
            if rec.state == 'running' and protected_fields_running.intersection(vals.keys()):
                raise UserError(
                    "You cannot change Entry Price, Opration Type, or Lot Size while the trade is running."
                )

        return super().write(vals)
    def _fetch_and_update_forex_data(self):
        api_key = self._get_api_key()
        try:
            response = requests.get(f"{self.API_URL}?apikey={api_key}")
            if response.status_code == 200:
                data = response.json()
                if isinstance(data, list) and data:
                    data = data[0]
                # To make it UTC+3 (Cairo Daylight)
                api_date = datetime.strptime(data.get('date'), "%Y-%m-%d %H:%M:%S") + timedelta(hours=4)

                self.write({
                    'bid': data.get('bid'),
                    'ask': data.get('ask'),
                    'open_': data.get('open'),
                    'low': data.get('low'),
                    'high': data.get('high'),
                    'change': data.get('changes'),
                    'api_time': api_date,
                })

                self._compute_current_profit()

        except Exception as e:
            raise UserError(f"Error fetching forex data: {e}")

    def _compute_current_profit(self):
        for rec in self:
            if rec.entry_price and rec.lot_size and rec.bid and rec.ask:
                lot_unit = rec.lot_size * 100000
                if rec.opt_type == 'buy':
                    rec.current_profit = round(lot_unit * (rec.bid - rec.entry_price), 5)
                else:
                    rec.current_profit = round(lot_unit * (rec.entry_price - rec.ask), 5)

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

    def action_update_values(self):
        self._fetch_and_update_forex_data()

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

