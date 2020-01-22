import requests
import threading
from six import iteritems
from models.exception import ResourceNotFoundError, InvalidHttpMethodError, HttpCodeError


class ApiClient(object):
    """
    Generic API Client for the Venmo API
    """

    def __init__(self, access_token):
        """
        :param access_token: <str> access token you received for your account.
        """
        access_token = self.__validate_access_token(access_token)

        self.access_token = access_token
        self.configuration = {"host": "https://api.venmo.com/v1"}
        self.default_headers = {"Authorization": access_token,
                                "User-Agent": "Venmo/7.44.0 (iPhone; iOS 13.0; Scale/2.0)"}
        self.session = requests.Session()
        self.session.headers.update(self.default_headers)

    def call_api(self, resource_path, method, header_params=None, params=None, body=None, callback=None):
        """
        Makes the HTTP request (Synchronous) and return the deserialized data.
        To make it async multi-threaded, define a callback function.

        :param resource_path: <str> Specific Venmo API path
        :param method: <str> HTTP request method
        :param header_params: <dict> request headers
        :param params: <dict> request parameters (?=)
        :param body: <dict> request body will be send as JSON
        :param callback: <function> Needs to be provided for async

        :return: response: <dict> {'status_code': <int>, 'headers': <dict>, 'body': <dict>}
        """

        if callback is None:
            return self.__call_api(resource_path=resource_path, method=method,
                                   header_params=header_params, params=params,
                                   body=body, callback=callback)
        else:
            thread = threading.Thread(target=self.__call_api,
                                      args=(resource_path, method, header_params,
                                            params, body, callback))
        thread.start()
        return thread

    def __call_api(self, resource_path, method,
                   header_params=None, params=None,
                   body=None, callback=None):
        """
        Calls API on the provided path

        :param resource_path: <str> Specific Venmo API path
        :param method: <str> HTTP request method
        :param header_params: <dict> request headers
        :param body: <dict> request body will be send as JSON
        :param callback: <function> Needs to be provided for async

        :return: response: <dict> {'status_code': <int>, 'headers': <dict>, 'body': <dict>}
        """

        # Update the header with the required values
        header_params = header_params or {}

        if body:
            header_params.update({"Content-Type": "application/json"})

        url = self.configuration['host'] + resource_path

        # Use a new session for multi-threaded
        if callback:
            session = requests.Session()
            session.headers.update(self.default_headers)

        else:
            session = self.session

        # perform request and return response
        processed_response = self.request(method, url, session,
                                          header_params=header_params, params=params,
                                          body=body)

        self.last_response = processed_response

        if callback:
            callback(processed_response)
        else:
            return processed_response

    def request(self, method, url, session, header_params=None, params=None, body=None):
        """
        Make a request with the provided information using a requests.session
        :param method:
        :param url:
        :param session:
        :param header_params:
        :param params:
        :param body:
        :return:
        """

        if method not in ['POST', 'PUT', 'GET', 'DELETE']:
            raise InvalidHttpMethodError()

        response = session.request(
            method=method, url=url, headers=header_params, params=params, json=body)

        # Only accepts the 20x status codes.
        response = self.validate_response(response)

        return {"status_code": response.status_code, "headers": response.headers, "body": response.json()}

    def validate_response(self, response):

        if response.status_code in range(200, 205) and response.json:
            return response

        elif response.status_code == 400 and response.json().get('error').get('code') == 283:
            raise ResourceNotFoundError()

        else:
            raise HttpCodeError(response=response)

    def __validate_access_token(self, access_token):
        """
        Validate the access_token
        :param access_token:
        :return:
        """
        if access_token[:6] != 'Bearer':
            return f"Barear {access_token}"

        return access_token

    def clean_kwargs(self, all_params, params):

        for key, val in iteritems(params['kwargs']):
            if key not in all_params:
                raise TypeError(
                    "Got an unexpected keyword argument '%s'"
                    " to method bla bla" % key
                )
            params[key] = val
        del params['kwargs']

        return params