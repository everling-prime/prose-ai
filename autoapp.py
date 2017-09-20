# -*- coding: utf-8 -*-
"""Create an application instance."""
from flask.helpers import get_debug_flag

from kojak_flask.app import create_app
from kojak_flask.settings import DevConfig, ProdConfig

CONFIG = DevConfig if get_debug_flag() else ProdConfig
app = create_app(CONFIG)

#enable for debugging only
#app.config.update(
#    PROPAGATE_EXCEPTIONS = True
#)