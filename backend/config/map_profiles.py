import json
import math
import os


MAPA_ARAC_TAREFAS = "mapa_arac_tarefas"


def load_map_profiles():
    raw = os.getenv("ARAC_TAREFAS_LEVELS")
    if raw is None:
        return {}

    levels = json.loads(raw)
    initial_level = int(os.getenv("ARAC_TAREFAS_INITIAL_LEVEL", "0"))
    fields = {"count", "scale_multiplier", "minimum_player_distance_m"}
    if not isinstance(levels, list) or not 0 <= initial_level < len(levels):
        raise ValueError("ARAC_TAREFAS_LEVELS must contain the initial level")

    for level in levels:
        if not isinstance(level, dict) or level.keys() != fields:
            raise ValueError("Each spider level must define count, scale and minimum distance")
        if type(level["count"]) is not int or level["count"] < 0:
            raise ValueError("Spider count must be a nonnegative integer")
        for field in ("scale_multiplier", "minimum_player_distance_m"):
            value = level[field]
            if type(value) not in (int, float) or not math.isfinite(value) or value <= 0:
                raise ValueError(f"{field} must be a positive finite number")

    return {
        MAPA_ARAC_TAREFAS: {
            "command": "set_spider_parameters",
            "initial_level": initial_level,
            "levels": levels,
        }
    }
