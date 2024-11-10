import http.client

import config

sp_graph_client = http.client.HTTPConnection(config.API_HOST, config.API_PORT)
