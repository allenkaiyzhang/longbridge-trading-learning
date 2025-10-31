"""
Utility functions to load and merge hierarchical prompt configurations.

This module provides a helper to assemble prompts from a layered
configuration. Prompts live in the `config/prompts` directory and are
organized by foundation, domain, module, and scenario. At runtime,
variables can be interpolated into the prompt templates.

Usage:
    from utils_prompt import load_prompt
    prompt_cfg = load_prompt(module="realtime_analysis",
                             scenario="analysis_intraday_snapshot",
                             runtime_vars={"symbols": "HK.0005,US.AAPL", "window": 5})
    system_msg = prompt_cfg.get("system", "")
    user_msg = prompt_cfg.get("user_template", "")

The lookup order (lowest to highest priority) is:
    1. Foundation (global) prompt: `config/prompts/foundation.yaml`
    2. Domain prompt (e.g. analysis): `config/prompts/domain/<domain>.yaml`
    3. Module prompt (e.g. realtime_analysis): `config/prompts/modules/<module>.yaml`
    4. Scenario prompt: `config/prompts/scenarios/<scenario>.yaml`
Runtime variables provided to `load_prompt` override template variables in any of
the above layers.
"""

from __future__ import annotations

import os
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

import yaml

# Determine base directories relative to this file
ROOT: Path = Path(__file__).resolve().parent
CONF_ROOT: Path = ROOT / "config"
PROMPTS_ROOT: Path = CONF_ROOT / "prompts"


def _read_yaml(path: Path) -> Dict[str, Any]:
    """Safely load a YAML file. If the file does not exist, return an empty dict."""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def _merge(a: Dict[str, Any], b: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two dictionaries, with values from b overriding those in a."""
    out: Dict[str, Any] = dict(a or {})
    for k, v in (b or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _merge(out[k], v)
        else:
            out[k] = v
    return out


def _render_template(template: Any, vars: Dict[str, Any]) -> Any:
    """
    Render a simple template by replacing {var} placeholders with values.

    Only applies to strings; other data types are returned unchanged.
    """
    if not isinstance(template, str):
        return template
    result = template
    for k, v in vars.items():
        result = result.replace("{" + str(k) + "}", str(v))
    return result


def load_prompt(
    module: Optional[str] = None,
    scenario: Optional[str] = None,
    runtime_vars: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Load and merge prompts from foundation, domain, module, and scenario layers.

    Parameters
    ----------
    module : Optional[str]
        Name of the module layer to load (e.g. "realtime_analysis").
    scenario : Optional[str]
        Name of the scenario layer to load (e.g. "analysis_intraday_snapshot").
    runtime_vars : Optional[Dict[str, Any]]
        Variables to substitute into the prompt templates. Common keys include
        "symbols", "window", and "now". If not provided, an empty dict is used.

    Returns
    -------
    Dict[str, Any]
        A merged prompt configuration with templates rendered using runtime
        variables.
    """
    # 1. Foundation layer
    foundation = _read_yaml(PROMPTS_ROOT / "foundation.yaml")

    # 2. Domain layer: infer domain from module, fallback to empty
    domain: Dict[str, Any] = {}
    if module == "realtime_analysis":
        # realtime_analysis belongs to the analysis domain
        domain = _read_yaml(PROMPTS_ROOT / "domain" / "analysis.yaml")

    # 3. Module layer
    module_doc: Dict[str, Any] = _read_yaml(PROMPTS_ROOT / "modules" / f"{module}.yaml") if module else {}

    # 4. Scenario layer
    scen_doc: Dict[str, Any] = _read_yaml(PROMPTS_ROOT / "scenarios" / f"{scenario}.yaml") if scenario else {}

    # Merge layers: lower priority first
    merged = foundation
    merged = _merge(merged, domain)
    merged = _merge(merged, module_doc)
    merged = _merge(merged, scen_doc)

    # Prepare runtime variables; include current timestamp
    vars: Dict[str, Any] = {"now": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
    if runtime_vars:
        vars.update(runtime_vars)

    # Render template strings
    for key in ("system", "assistant_primer", "user_template"):
        if key in merged:
            merged[key] = _render_template(merged[key], vars)

    return merged


__all__ = ["load_prompt"]