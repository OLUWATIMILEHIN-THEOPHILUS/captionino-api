# Environment variables validation here
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    supabase_project_url: str
    supabase_api_key: str
    supabase_bucket: str
    database_username: str
    database_password: str
    database_hostname: str
    database_port: str
    database_name: str
    secret_key: str
    algorithm: str
    access_token_expire_minutes: int
    google_client_id: str
    google_client_secret: str
    reset_token_expire_minutes: int
    smtp_server: str
    smtp_port: int
    email_sender: str
    email_password: str
    aws_access_key: str
    aws_secret_key: str
    aws_region: str
    bucket_name: str
    replicate_api_token: str


    class Config:
        env_file = ".env"

settings = Settings()