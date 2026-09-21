"""Small ADB and UI-automation helpers shared by WhatsApp scripts."""

from __future__ import annotations

import re
import subprocess
from typing import Any


def adb(*args: str) -> str:
    """Run an ADB shell command and return its standard output."""
    return subprocess.run(
        ["adb", "shell", *args], capture_output=True, text=True
    ).stdout


def device_is_connected() -> bool:
    """Return whether ADB can see an authorized device."""
    result = subprocess.run(["adb", "get-state"], capture_output=True, text=True)
    return "device" in result.stdout


def ui_nodes() -> list[dict[str, Any]]:
    """Dump the current UI and return visible text/description labels with centers."""
    adb("uiautomator", "dump", "/sdcard/ui.xml")
    xml = adb("cat", "/sdcard/ui.xml")
    nodes = []
    for node in re.findall(r"<node [^>]*>", xml):
        text = re.search(r' text="([^"]*)"', node)
        desc = re.search(r'content-desc="([^"]*)"', node)
        bounds = re.search(r'bounds="\[(\d+),(\d+)\]\[(\d+),(\d+)\]"', node)
        if not bounds:
            continue
        x1, y1, x2, y2 = map(int, bounds.groups())
        nodes.append(
            {
                "text": text.group(1) if text else "",
                "desc": desc.group(1) if desc else "",
                "x": (x1 + x2) // 2,
                "y": (y1 + y2) // 2,
            }
        )
    return nodes


def find(nodes: list[dict[str, Any]], pattern: str) -> dict[str, Any] | None:
    """Find the first node whose label matches a regular-expression pattern."""
    for node in nodes:
        if re.search(pattern, node["text"].strip(), re.I) or re.search(
            pattern, node["desc"].strip(), re.I
        ):
            return node
    return None


def tap(node: dict[str, Any]) -> None:
    """Tap the center of a UI node returned by :func:`ui_nodes`."""
    adb("input", "tap", str(node["x"]), str(node["y"]))
