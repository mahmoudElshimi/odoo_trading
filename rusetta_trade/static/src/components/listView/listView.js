import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CustomList extends Component {
    static template = "rusetta_trade.CustomList";

    setup() {
        this.state = useState({ trades: [] });
        this.orm = useService("orm");

        onWillStart(async () => {
            this.state.trades = await this.orm.searchRead(
                "rusetta.trade",
                [],
                ["create_date", "opt_type", "state"]
            );
        });
    }
}

registry.category("actions").add(
    "rusetta_trade.action_custom_list",
    CustomList
);

