import logging
from json.decoder import JSONDecodeError

import bottle


class WebhookListener:
    """ Listen for netbox webhook requests and change DHCP configuration """

    def __init__(self, connector, host='127.0.0.1', port=8001, secret=None,
                 secret_header=None):
        self.conn = connector
        self.host = host
        self.port = port
        self.secret = secret
        self.secret_header = secret_header

    def run(self):
        """ Start web server """

        @bottle.route('/event/<name>/', 'POST')
        def new_event(name):
            """ Define an all-in-one route for our web server """

            logging.debug(f'Receive data on /event/{name}/')

            # import json
            # body = bottle.request.body.getvalue()
            # try:
            #     print(json.dumps(json.loads(body), indent=4))
            # except Exception:
            #     print(body.decode())

            if (self.secret_header and bottle.request.get_header(
                    self.secret_header) != self.secret):
                self._abort(403, 'wrong secret or secret header')

            # Parse JSON body from request
            try:
                body = bottle.request.json
            except JSONDecodeError:
                body = bottle.request.body.getvalue().decode()
                self._abort(400, f'malformed body (not JSON):  {body}')

            logging.debug(f'Parsed JSON request: {body}')
            try:
                model, id_, event = (
                    body['model'], body['data']['id'], body['event'])
            except KeyError as e:
                self._abort(400, f'request missing key: {e}')

            try:
                sync_func = getattr(self.conn, f'sync_{model}')
            except AttributeError:
                self._abort(400, f'unsupported target "{model}"')
            else:
                logging.info(f'process event: {model} id={id_} {event}')
                # Reload DHCP config before applying any changes
                self.conn.reload_dhcp_config()
                sync_func(id_)

            bottle.response.status = 201

            # Push change to DHCP server
            self.conn.push_to_dhcp()
        
        # very basic health check, basically proves bottle is already/still running
        # enough for Kubernetes probes
        @bottle.route('/health/')
        def health():
            return 'ok'

        # start server
        bottle.run(host=self.host, port=self.port)

    def _abort(self, code, msg):
        logging.error(msg)
        bottle.abort(code, msg)
