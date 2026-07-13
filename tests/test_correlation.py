from correlation.opcua_case_correlator import correlate


def test_correlation_pairs_process_and_suricata_flow_evidence() -> None:
    alerts = [
        {
            "timestamp": "2026-07-08T17:20:00.000000+0000",
            "rule": {
                "id": "110203",
                "description": "OT simulator valve command changed",
            },
            "agent": {"name": "Ubuntu"},
            "location": "/home/ahmed_bahaa/ot-project/opcua-client/logs/opcua_monitor.jsonl",
            "data": {
                "ot": {
                    "tag": "VALF",
                    "node_id": "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.VALF",
                    "old_value": False,
                    "new_value": True,
                }
            },
        },
        {
            "timestamp": "2026-07-08T17:20:00.250000+0000",
            "rule": {
                "id": "110104",
                "description": "OT OPC UA network flow observed by Suricata - validation scenario",
            },
            "agent": {"name": "My-Win-Machine"},
            "location": "C:\\OT-Project\\suricata-output\\flow-proof-current\\eve.json",
            "data": {
                "src_ip": "192.168.56.10",
                "dest_ip": "192.168.56.1",
                "dest_port": "49320",
            },
        },
    ]

    cases = correlate(alerts, window_seconds=60)

    assert len(cases) == 1
    assert cases[0]["case_type"] == "confirmed_opcua_operation"
    assert cases[0]["classification"] == "suspicious_ot_operation"
    assert cases[0]["tag"] == "VALF"
    assert cases[0]["rule_ids"] == ["110104", "110203"]
    assert cases[0]["destination_port"] == "49320"


def test_correlation_requires_network_flow_confirmation() -> None:
    alerts = [
        {
            "timestamp": "2026-07-08T17:20:00.000000+0000",
            "rule": {"id": "110203"},
            "data": {
                "ot": {
                    "tag": "VALF",
                    "node_id": "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.VALF",
                }
            },
        }
    ]

    assert correlate(alerts, window_seconds=60) == []
