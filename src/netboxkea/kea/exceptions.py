class KeaError(Exception):
    pass


class KeaServerError(KeaError):
    pass


class KeaClientError(KeaError):
    pass


class SubnetNotEqual(KeaError):
    pass


class SubnetNotFound(KeaClientError):
    pass


class DuplicateValue(KeaClientError):
    pass


class KeaCmdError(KeaClientError):
    pass
