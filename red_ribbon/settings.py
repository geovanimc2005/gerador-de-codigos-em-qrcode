INSTALLED_APPS = [
    'meu_app',
    'corsheaders'
]
MIDDLEWARE=[
    'corsheaders.middleware.CorsMiddleware'
]
CORS_ALLOWED_ORIGINS = [
    'http://localhost:8000/minha_url/',
]
CORS_ALLOW_METHODS = [
    'GET',
    'POST',
    'PUT',
    'DELETE'
]