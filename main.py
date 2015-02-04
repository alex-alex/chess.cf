#!/usr/bin/env python

import webapp2
import routes
import config

app = webapp2.WSGIApplication(config=config.webapp2_config, debug=True)
routes.add_routes(app)
