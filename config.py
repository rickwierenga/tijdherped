""" Codes in environment variables """

import os


class Config:
    BASE_DIR = os.path.abspath(os.path.dirname(__file__))  

    THREADS_PER_PAGE = 2

    CSRF_ENABLED     = True
    CSRF_SESSION_KEY = os.environ['CSRF_SESSION_KEY']

    SECRET_KEY = os.environ['SECRET_KEY']
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True


class ProductionConfig(Config):
    DEBUG = False
    ASSETS_DEBUG = False
