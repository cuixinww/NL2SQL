import os
from pathlib import Path
from typing import Type
from omegaconf import OmegaConf

# 环境变量前缀
_ENV_PREFIX = "BANK_AGENT_"


def _overlay_env_vars(cfg: OmegaConf, prefix: str = _ENV_PREFIX):
    """
    用环境变量覆盖配置。
    命名规则：BANK_AGENT_{SECTION}_{KEY}，全大写，下划线分隔。
    例：BANK_AGENT_DB_DW_HOST → db_dw.host
        BANK_AGENT_LLM_API_KEY → llm.api_key
    """
    for key, value in os.environ.items():
        if not key.startswith(prefix):
            continue
        parts = key[len(prefix):].lower().split("_")
        # 尝试匹配 section.key 两级路径
        # 特殊处理：db_dw、db_meta 等含下划线的 section
        matched = False
        for split_pos in range(1, len(parts)):
            section = "_".join(parts[:split_pos])
            field = "_".join(parts[split_pos:])
            try:
                OmegaConf.select(cfg, f"{section}.{field}")
                # 类型转换：int / float / bool
                casted = value
                try:
                    casted = int(value)
                except ValueError:
                    try:
                        casted = float(value)
                    except ValueError:
                        if value.lower() in ("true", "false"):
                            casted = value.lower() == "true"
                OmegaConf.update(cfg, f"{section}.{field}", casted)
                matched = True
                break
            except Exception:
                continue
        if not matched:
            # 顶层字段
            try:
                OmegaConf.update(cfg, parts[0].lower(), value)
            except Exception:
                pass


def load_config[T](config_file: Path, schema_cls: Type[T]) -> T:
    context = OmegaConf.load(config_file)
    schema = OmegaConf.structured(schema_cls)
    merged = OmegaConf.merge(schema, context)
    _overlay_env_vars(merged)
    return OmegaConf.to_object(merged)
