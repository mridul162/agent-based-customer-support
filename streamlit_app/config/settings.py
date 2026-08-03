from dataclasses import dataclass, field
import os
from pathlib import Path


@dataclass(frozen=True)
class StreamlitSettings:
    app_title: str = "Agent Based Customer Support"
    app_icon: str = "💬"
    layout: str = "wide"
    initial_sidebar_state: str = "expanded"
    theme_base: str = "light"
    primary_color: str = "#4B8BBE"
    background_color: str = "#F0F2F6"
    secondary_background_color: str = "#E1E5EE"
    text_color: str = "#0E1117"
    font: str = "sans serif"
    show_toolbar: bool = False
    navigation_button: str = "disabled"
    max_history_items: int = 50
    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_api_base: str = field(default_factory=lambda: os.getenv("OPENAI_API_BASE", ""))
    data_dir: Path = field(default_factory=lambda: Path(os.getenv("DATA_DIR", Path.cwd() / "data")))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))
    DEFAULT_API_BASE_URL: str = field(default_factory=lambda: os.getenv("API_BASE_URL", "http://localhost:8000"))

    @property
    def page_config(self) -> dict:
        return {
            "page_title": self.app_title,
            "page_icon": self.app_icon,
            "layout": self.layout,
            "initial_sidebar_state": self.initial_sidebar_state,
        }

    @property
    def theme(self) -> dict:
        return {
            "base": self.theme_base,
            "primaryColor": self.primary_color,
            "backgroundColor": self.background_color,
            "secondaryBackgroundColor": self.secondary_background_color,
            "textColor": self.text_color,
            "font": self.font,
        }


settings = StreamlitSettings()
