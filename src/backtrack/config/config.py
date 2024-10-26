from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class GeneralConfig:
    static_dir: str
    template_dir: str
    hostname: str
    log_level: str = "debug"



@dataclass
class AppConfig:
    general: GeneralConfig


def init_config(conf_fi: Path) -> AppConfig:
    with open(conf_fi) as conf:
        conf_vals: dict = yaml.safe_load(conf)

        general_conf: GeneralConfig = GeneralConfig(**conf_vals["general"])

    return AppConfig(general_conf)
