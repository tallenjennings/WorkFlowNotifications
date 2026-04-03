from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "Workflow Notifications"
    environment: str = "dev"
    secret_key: str = "change-me"
    database_url: str = "postgresql+psycopg://workflow:workflow@db:5432/workflow"
    graph_tenant_id: str = ""
    graph_client_id: str = ""
    graph_client_secret: str = ""
    graph_mailbox_user: str = ""
    poll_interval_seconds: int = 120
    occurrence_horizon_days: int = 90

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")


settings = Settings()
