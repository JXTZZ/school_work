import json
import os
from dataclasses import asdict
from typing import Dict, Optional, Tuple
from .engine import WatermarkSettings, ExportSettings, TextStyle, ImageStyle

TEMPLATES_FILE = os.path.join(os.path.dirname(__file__), "templates.json")

def _empty_store():
    return {"last": None, "templates": {}}


def _load_store() -> Dict:
    if not os.path.exists(TEMPLATES_FILE):
        return _empty_store()
    try:
        with open(TEMPLATES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return _empty_store()


def _save_store(store: Dict) -> None:
    os.makedirs(os.path.dirname(TEMPLATES_FILE), exist_ok=True)
    with open(TEMPLATES_FILE, "w", encoding="utf-8") as f:
        json.dump(store, f, ensure_ascii=False, indent=2)


def serialize(wm: WatermarkSettings, exp: ExportSettings) -> Dict:
    return {"wm": asdict(wm), "exp": asdict(exp)}


def deserialize(data: Dict) -> Tuple[WatermarkSettings, ExportSettings]:
    wm_data = data.get("wm", {})
    exp_data = data.get("exp", {})

    # nested dataclasses rebuild
    ts = wm_data.get("text_style", {})
    istyle = wm_data.get("image_style", {})
    wm = WatermarkSettings(
        mode=wm_data.get("mode", "text"),
        text=wm_data.get("text", "Sample Watermark"),
        text_style=TextStyle(
            font_path=ts.get("font_path"),
            font_size=ts.get("font_size", 36),
            color=tuple(ts.get("color", (255, 255, 255))),
            opacity=ts.get("opacity", 80),
            stroke_width=ts.get("stroke_width", 0),
            stroke_color=tuple(ts.get("stroke_color", (0, 0, 0))),
            shadow=ts.get("shadow", False),
            shadow_offset=tuple(ts.get("shadow_offset", (2, 2))),
        ),
        image_style=ImageStyle(
            path=istyle.get("path"),
            scale=istyle.get("scale", 0.25),
            opacity=istyle.get("opacity", 80),
        ),
        rotation=wm_data.get("rotation", 0.0),
        position=wm_data.get("position", "bottom-right"),
        offset=tuple(wm_data.get("offset", (10, 10))),
        free_pos_norm=tuple(wm_data.get("free_pos_norm")) if wm_data.get("free_pos_norm") else None,
    )

    exp = ExportSettings(
        output_dir=exp_data.get("output_dir", ""),
        prevent_overwrite_original=exp_data.get("prevent_overwrite_original", True),
        naming_mode=exp_data.get("naming_mode", "suffix"),
        prefix=exp_data.get("prefix", "wm_"),
        suffix=exp_data.get("suffix", "_watermarked"),
        out_format=exp_data.get("out_format", "JPEG"),
        jpeg_quality=exp_data.get("jpeg_quality", 90),
        resize_mode=exp_data.get("resize_mode", "none"),
        resize_value=exp_data.get("resize_value", 0),
    )
    return wm, exp


def save_last(wm: WatermarkSettings, exp: ExportSettings) -> None:
    store = _load_store()
    store["last"] = serialize(wm, exp)
    _save_store(store)


def load_last() -> Optional[Tuple[WatermarkSettings, ExportSettings]]:
    store = _load_store()
    last = store.get("last")
    if not last:
        return None
    return deserialize(last)


def list_templates() -> Dict[str, Dict]:
    return _load_store().get("templates", {})


def save_template(name: str, wm: WatermarkSettings, exp: ExportSettings) -> None:
    store = _load_store()
    store.setdefault("templates", {})[name] = serialize(wm, exp)
    _save_store(store)


def load_template(name: str) -> Optional[Tuple[WatermarkSettings, ExportSettings]]:
    store = _load_store()
    tpl = store.get("templates", {}).get(name)
    if not tpl:
        return None
    return deserialize(tpl)


def delete_template(name: str) -> bool:
    store = _load_store()
    tpls = store.get("templates", {})
    if name in tpls:
        del tpls[name]
        store["templates"] = tpls
        _save_store(store)
        return True
    return False

