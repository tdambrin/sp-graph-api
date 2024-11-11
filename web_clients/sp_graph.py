import http.client

import config

sp_graph_client = http.client.HTTPConnection(
    host=config.API_HOST,
    port=config.API_PORT,
)
