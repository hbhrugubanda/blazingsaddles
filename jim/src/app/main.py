import base64
import os
from pathlib import Path

import trafaret as t
from aiohttp import web
from trafaret_config import read_and_validate

import aiohttp_session
from aiohttp_session.cookie_storage import EncryptedCookieStorage

from .views import index


THIS_DIR = Path(__file__).parent
BASE_DIR = THIS_DIR.parent
SETTINGS_FILE = BASE_DIR / 'settings.yml'  # type: Path

DEV_DICT = t.Dict()
DEV_DICT.allow_extra('*')
ENV_PREFIX = 'APP_'

SETTINGS_STRUCTURE = t.Dict({
    # the "dev" dictionary contains information used by aiohttp-devtools to serve your app locally
    # you may wish to use it yourself,
    # eg. you might use dev.static_path in a management script to deploy static assets
    'dev': DEV_DICT,
    'cookie_secret_key': t.String,
})


def substitute_environ(s_dict: dict, prefix: str) -> dict:
    """
    Substitute environment variables into a settings dict.

    Names are searched hierarchically with underscores representing levels, environment variables must be
    capitalised.

    For example lets say we have ` {'foo': 'bar', 'subdict': {'value': 123}}` with prefix 'APP_',
    the environment variable "APP_FOO = spam" would replace "bar" and "APP_SUBDICT_VALUE = 3"
    would be converted to int and replace 123 in the dict.

    :param: s_dict: dict to replace values in
    :param: prefix: required prefix for environment variables to
    :return: modified dict
    """
    for key, value in s_dict.items():
        if isinstance(value, dict):
            s_dict[key] = substitute_environ(value, prefix + key + '_')
        elif isinstance(value, list):
            # doesn't make sense, we can't do anything here
            pass
        else:
            env_var = os.getenv((prefix + key).upper(), None)
            if env_var is not None:
                # basic attempt to convert the new value to match the original type
                if isinstance(value, int):
                    s_dict[key] = int(env_var)
                else:
                    # are there any other types we might need to cope with here?
                    s_dict[key] = env_var
    return s_dict


def load_settings() -> dict:
    """
    Read settings.yml and, validation its content.
    :return: settings dict
    """
    settings_file = SETTINGS_FILE.resolve()
    settings = read_and_validate(str(settings_file), SETTINGS_STRUCTURE)
    settings = substitute_environ(settings, ENV_PREFIX)
    return settings


def setup_routes(app):
    app.router.add_get('/', index, name='index')


def create_app(loop):
    app = web.Application(loop=loop)
    app['name'] = 'src'
    app.update(load_settings())

    secret_key = base64.urlsafe_b64decode(app['cookie_secret_key'])
    aiohttp_session.setup(app, EncryptedCookieStorage(secret_key))

    setup_routes(app)
    return app
