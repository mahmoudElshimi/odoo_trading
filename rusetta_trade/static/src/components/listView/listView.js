import {Component} from "@odoo/owl";
import {registry} from "@web/core/registry";

export class CustomList extends Component {
	static template = "rusetta_trade.CustomList";
}

registry.category("actions").add("rusetta_trade.action_custom_list", CustomList);
