import dbmodel

webapp2_config = {}
webapp2_config['webapp2_extras.sessions'] = {
    'secret_key': 'NkMV5xGRyyaG8EyYYwgRy9RDChu3e9J2',
}
webapp2_config['webapp2_extras.auth'] = {
    'user_model': dbmodel.Account,
    'user_attributes': ['email']
}

TOKEN_TIMEOUT = 120
