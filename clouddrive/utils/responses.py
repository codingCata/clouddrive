from flask import jsonify


def success(data=None, message=None, status=200):
    payload = {'success': True}
    if message:
        payload['message'] = message
    if data is not None:
        payload['data'] = data
    return jsonify(payload), status


def error(message, code='ERROR', status=400, details=None):
    payload = {
        'success': False,
        'error': {
            'code': code,
            'message': message
        }
    }
    if details:
        payload['error']['details'] = details
    return jsonify(payload), status


class APIError(Exception):
    def __init__(self, message, code='ERROR', status=400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
        self.details = details


ERROR_CODES = {
    'VALIDATION_ERROR': 400,
    'NOT_FOUND': 404,
    'UNAUTHORIZED': 401,
    'FORBIDDEN': 403,
    'RATE_LIMITED': 429,
    'DUPLICATE': 409,
    'INTERNAL_ERROR': 500
}
