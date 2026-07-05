from typing import Self

import pytest

from src.find_node import search_node


class FakeNodeId:
    def __init__(self, value: str) -> None:
        self.value = value

    def to_string(self) -> str:
        return self.value


class FakeBrowseName:
    def __init__(
        self,
        name: str | None,
        namespace_index: int = 2,
    ) -> None:
        self.Name = name
        self.NamespaceIndex = namespace_index


class FakeDisplayName:
    def __init__(self, text: str | None) -> None:
        self.Text = text


class FakeNode:
    def __init__(
        self,
        node_id: str,
        *,
        browse_name: str | None,
        display_name: str | None = None,
        namespace_index: int = 2,
        children: list["FakeNode"] | None = None,
        children_error: Exception | None = None,
        browse_error: Exception | None = None,
    ) -> None:
        self.nodeid = FakeNodeId(node_id)
        self.browse_name = FakeBrowseName(
            browse_name,
            namespace_index,
        )
        self.display_name = FakeDisplayName(display_name)
        self.children = children or []
        self.children_error = children_error
        self.browse_error = browse_error
        self.children_calls = 0

    def add_children(self, *children: Self) -> None:
        self.children.extend(children)

    async def get_children(self) -> list["FakeNode"]:
        self.children_calls += 1

        if self.children_error is not None:
            raise self.children_error

        return self.children

    async def read_browse_name(self) -> FakeBrowseName:
        if self.browse_error is not None:
            raise self.browse_error

        return self.browse_name

    async def read_display_name(self) -> FakeDisplayName:
        return self.display_name


@pytest.mark.asyncio
async def test_search_node_finds_case_insensitive_display_name(
    capsys,
) -> None:
    target = FakeNode(
        "ns=2;s=watersim.TankPLC.MAIN."
        "ARTIRMA_VERI.SU_SEVIYESI",
        browse_name=None,
        display_name="SU_SEVIYESI",
        namespace_index=2,
    )
    main = FakeNode(
        "ns=2;s=watersim.TankPLC.MAIN",
        browse_name="MAIN",
        children=[target],
    )
    root = FakeNode(
        "i=85",
        browse_name="Objects",
        namespace_index=0,
        children=[main],
    )

    await search_node(
        root,
        "su_seviyesi",
        ["Objects"],
        set(),
    )

    output = capsys.readouterr().out

    assert "MATCH FOUND" in output
    assert "Objects / MAIN / SU_SEVIYESI" in output
    assert target.nodeid.to_string() in output
    assert "Browse namespace index: 2" in output


@pytest.mark.asyncio
async def test_search_node_stops_when_cycle_is_visited() -> None:
    root = FakeNode(
        "i=85",
        browse_name="Objects",
        namespace_index=0,
    )
    child = FakeNode(
        "ns=2;s=watersim",
        browse_name="watersim",
    )

    root.add_children(child)
    child.add_children(root)

    visited: set[str] = set()

    await search_node(
        root,
        "not-present",
        ["Objects"],
        visited,
    )

    assert visited == {
        "i=85",
        "ns=2;s=watersim",
    }
    assert root.children_calls == 1
    assert child.children_calls == 1


@pytest.mark.asyncio
async def test_search_node_respects_maximum_depth(
    capsys,
) -> None:
    deep_target = FakeNode(
        "ns=2;s=deep-target",
        browse_name="DEEP_TARGET",
    )
    level_two = FakeNode(
        "ns=2;s=level-two",
        browse_name="LEVEL_TWO",
        children=[deep_target],
    )
    level_one = FakeNode(
        "ns=2;s=level-one",
        browse_name="LEVEL_ONE",
        children=[level_two],
    )
    root = FakeNode(
        "i=85",
        browse_name="Objects",
        namespace_index=0,
        children=[level_one],
    )

    await search_node(
        root,
        "DEEP_TARGET",
        ["Objects"],
        set(),
        max_depth=1,
    )

    output = capsys.readouterr().out

    assert "DEEP_TARGET" not in output
    assert root.children_calls == 1
    assert level_one.children_calls == 1
    assert level_two.children_calls == 0
    assert deep_target.children_calls == 0


@pytest.mark.asyncio
async def test_search_node_skips_broken_child_and_continues(
    capsys,
) -> None:
    broken = FakeNode(
        "ns=2;s=broken",
        browse_name="BROKEN",
        browse_error=RuntimeError("Browse failed"),
    )
    valid = FakeNode(
        "ns=2;s=watersim.TankPLC.MAIN.ARTIRMA_VERI.VALF",
        browse_name="VALF",
    )
    root = FakeNode(
        "i=85",
        browse_name="Objects",
        namespace_index=0,
        children=[broken, valid],
    )

    await search_node(
        root,
        "VALF",
        ["Objects"],
        set(),
    )

    output = capsys.readouterr().out

    assert "MATCH FOUND" in output
    assert "Objects / VALF" in output
    assert valid.nodeid.to_string() in output
