import {Component, useState} from "@odoo/owl";
import {registry} from "@web/core/registry";
import {useService} from "@web/core/utils/hooks";

export class CustomList extends Component {
	static template = "rusetta_trade.CustomList";

	setup() {
		this.state = useState(
			{
				"trades": [],
			}
		);
		this.orm = useService("orm");
		this.loadTrades();
	};

	async loadTrades() {
		const trade = await this.orm.searchRead("rusetta.trade", [], []);
		this.state.trades = trade;
	};
}

registry.category("actions").add("rusetta_trade.action_custom_list", CustomList);
