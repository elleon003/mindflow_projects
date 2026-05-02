from environs import env

# Load environment variables from .env file
env.read_env()

# Determine the environment
environment = env.str('DJANGO_ENV', 'development')

if environment == 'production':
    from .production import *
else:
    from .development import *

