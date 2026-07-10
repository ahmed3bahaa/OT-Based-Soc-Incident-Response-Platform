from __future__ import annotations

from .models import Asset, Rule, Tag

TAG_PREFIX = "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI"

RULE_CATALOG = [
    {
        "rule_id": "110103",
        "name": "Passive OPC UA datachange observed",
        "description": "OT OPC UA datachange observed by passive monitor - validation scenario",
        "level": 3,
        "source": "opcua_monitor",
        "category": "process_datachange",
        "classification_hint": "validation_not_malicious",
    },
    {
        "rule_id": "110104",
        "name": "OPC UA network flow observed",
        "description": "OT OPC UA network flow observed by Suricata - validation scenario",
        "level": 3,
        "source": "suricata",
        "category": "network_flow",
        "classification_hint": "validation_not_malicious",
    },
    {
        "rule_id": "110105",
        "name": "KEPServerEX diagnostics write observed",
        "description": "OT OPC UA write observed in KEPServerEX diagnostics - validation scenario",
        "level": 3,
        "source": "kepserverex_diagnostics",
        "category": "server_diagnostics",
        "classification_hint": "validation_not_malicious",
    },
    {
        "rule_id": "110200",
        "name": "Selected simulator OT tag changed",
        "description": "OT simulator selected tag datachange observed - MVP rule",
        "level": 3,
        "source": "wazuh_simulator_rules",
        "category": "simulator_tag",
        "classification_hint": "validation_not_malicious",
    },
    {
        "rule_id": "110201",
        "name": "Critical command tag changed",
        "description": "OT simulator critical command tag changed",
        "level": 7,
        "source": "wazuh_simulator_rules",
        "category": "critical_command",
        "classification_hint": "important_ot_operation",
    },
    {
        "rule_id": "110202",
        "name": "Motor or pump command changed",
        "description": "OT simulator motor or pump command changed",
        "level": 8,
        "source": "wazuh_simulator_rules",
        "category": "motor_pump_command",
        "classification_hint": "suspicious_ot_operation",
    },
    {
        "rule_id": "110203",
        "name": "Valve command changed",
        "description": "OT simulator valve command changed",
        "level": 8,
        "source": "wazuh_simulator_rules",
        "category": "valve_command",
        "classification_hint": "suspicious_ot_operation",
    },
    {
        "rule_id": "110204",
        "name": "Water level tag changed",
        "description": "OT simulator water level tag changed",
        "level": 5,
        "source": "wazuh_simulator_rules",
        "category": "water_level_process",
        "classification_hint": "important_ot_operation",
    },
    {
        "rule_id": "110205",
        "name": "Repeated failed OPC UA writes",
        "description": "OT repeated failed OPC UA write attempts observed",
        "level": 9,
        "source": "wazuh_simulator_rules",
        "category": "write_failure_repeated",
        "classification_hint": "suspicious_ot_operation",
    },
]

TAG_CATALOG = [
    {
        "name": "VALF",
        "node_id": f"{TAG_PREFIX}.VALF",
        "tag_type": "valve_command",
        "criticality": "high",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": True,
        "description": "Simulator valve command tag.",
    },
    {
        "name": "SU_SEVIYESI",
        "node_id": f"{TAG_PREFIX}.SU_SEVIYESI",
        "tag_type": "water_level",
        "criticality": "medium",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": True,
        "description": "Simulator water level process tag.",
    },
    {
        "name": "MOTOR1",
        "node_id": f"{TAG_PREFIX}.MOTOR1",
        "tag_type": "motor_command",
        "criticality": "high",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": True,
        "description": "Simulator motor command tag.",
    },
    {
        "name": "MOTOR2",
        "node_id": f"{TAG_PREFIX}.MOTOR2",
        "tag_type": "motor_command",
        "criticality": "high",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": True,
        "description": "Simulator motor command tag.",
    },
    {
        "name": "MOTOR3",
        "node_id": f"{TAG_PREFIX}.MOTOR3",
        "tag_type": "motor_command",
        "criticality": "high",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": True,
        "description": "Simulator motor command tag.",
    },
    {
        "name": "SAMANDIRA",
        "node_id": f"{TAG_PREFIX}.SAMANDIRA",
        "tag_type": "float_switch",
        "criticality": "medium",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": False,
        "description": "Simulator float-switch style process tag.",
    },
    {
        "name": "DEBI",
        "node_id": f"{TAG_PREFIX}.DEBI",
        "tag_type": "flow_rate",
        "criticality": "medium",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": False,
        "description": "Simulator flow-rate process tag.",
    },
    {
        "name": "DEBI2",
        "node_id": f"{TAG_PREFIX}.DEBI2",
        "tag_type": "flow_rate",
        "criticality": "medium",
        "station_or_area": "ARTIRMA_VERI",
        "is_writable": False,
        "description": "Simulator secondary flow-rate process tag.",
    },
]

ASSET_CATALOG = [
    {
        "name": "Ubuntu Wazuh / OPC UA monitor host",
        "ip_address": "192.168.56.10",
        "role": "wazuh_manager_opcua_monitor",
        "platform": "Ubuntu",
        "description": "Ubuntu host running Wazuh manager and passive Python OPC UA monitor.",
    },
    {
        "name": "Windows KEPServerEX / Suricata / Wazuh agent host",
        "ip_address": "192.168.56.1",
        "role": "kepserverex_suricata_wazuh_agent",
        "platform": "Windows",
        "description": "Windows host running KEPServerEX simulator, Suricata, and Wazuh agent.",
    },
]


def seed_catalogs() -> dict[str, int]:
    counts = {
        "rules_created": 0,
        "rules_updated": 0,
        "tags_created": 0,
        "tags_updated": 0,
        "assets_created": 0,
        "assets_updated": 0,
    }

    for item in RULE_CATALOG:
        _, created = Rule.objects.update_or_create(
            rule_id=item["rule_id"],
            defaults={key: value for key, value in item.items() if key != "rule_id"},
        )
        counts["rules_created" if created else "rules_updated"] += 1

    for item in TAG_CATALOG:
        _, created = Tag.objects.update_or_create(
            name=item["name"],
            defaults={key: value for key, value in item.items() if key != "name"},
        )
        counts["tags_created" if created else "tags_updated"] += 1

    for item in ASSET_CATALOG:
        _, created = Asset.objects.update_or_create(
            ip_address=item["ip_address"],
            defaults={key: value for key, value in item.items() if key != "ip_address"},
        )
        counts["assets_created" if created else "assets_updated"] += 1

    return counts
