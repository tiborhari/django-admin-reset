DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3'
    }
}
INSTALLED_APPS = [
    'django_admin_reset',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles'
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.locale.LocaleMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]
# This insecure hasher speeds up tests
PASSWORD_HASHERS = ['django.contrib.auth.hashers.SHA1PasswordHasher']
SECRET_KEY = '!!!INSECURE!!! 2OQcxcgohdo= !!!INSECURE!!!'
ROOT_URLCONF = 'django_admin_reset.tests.urls'
STATIC_URL = '/static/'
USE_TZ = True
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
