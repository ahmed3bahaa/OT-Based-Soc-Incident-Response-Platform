from src import opcua_monitor


def test_default_simulator_node_ids_include_data_access_view_tags() -> None:
    node_ids = opcua_monitor.default_simulator_node_ids()

    assert node_ids == [
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.DEBI",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.MOTOR1",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.MOTOR2",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.SAMANDIRA",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.SU_SEVIYESI",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.ScenarioID",
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.VALF",
    ]


def test_env_node_ids_ignores_empty_entries(monkeypatch) -> None:
    monkeypatch.setenv(
        "OPCUA_MONITOR_NODE_IDS",
        "ns=2;s=A, ,ns=2;s=B,",
    )

    assert opcua_monitor.env_node_ids() == ["ns=2;s=A", "ns=2;s=B"]
