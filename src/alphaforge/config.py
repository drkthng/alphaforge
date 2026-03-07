import os
from typing import Optional, Dict

import yaml
from pydantic import BaseModel, Field


class DatabaseConfig(BaseModel):
    path: str = "./data/alphaforge.db"


class PathsConfig(BaseModel):
    archive_dir: str = "./data/archive"
    equity_curves_dir: str = "./data/equity_curves"
    attachments_dir: str = "./data/attachments"
    realtest_output_dir: Optional[str] = None


class RealTestConfig(BaseModel):
    stats_csv_columns: Dict[str, str] = Field(default_factory=dict)


class ServerConfig(BaseModel):
    port: int = 8501
    host: str = "localhost"


class BackupConfig(BaseModel):
    enabled: bool = False
    target_dir: Optional[str] = None


class AppConfig(BaseModel):
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    realtest: RealTestConfig = Field(default_factory=RealTestConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    backup: BackupConfig = Field(default_factory=BackupConfig)


def load_config(path: str = "config.yaml") -> AppConfig:
    """Loads and validates configuration from a YAML file."""
    if not os.path.exists(path):
        return AppConfig()
    
    with open(path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
        
    if data is None:
        return AppConfig()
        
    return AppConfig(**data)

get_config = load_config
