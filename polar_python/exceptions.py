class PolarPythonError(Exception):
    pass


class ControlPointResponseError(PolarPythonError):
    """Exception raised when there is an unexpected response from the control point."""

    def __init__(self, message="Unexpected response from the control point"):
        self.message = message
        super().__init__(self.message)


class ConnectionError(PolarPythonError):
    """Exception raised when the device fails to connect."""

    def __init__(self, message="Failed to connect to the Polar device"):
        self.message = message
        super().__init__(self.message)


class DisconnectionError(PolarPythonError):
    """Exception raised when the device fails to disconnect."""

    def __init__(self, message="Failed to disconnect from the Polar device"):
        self.message = message
        super().__init__(self.message)


class NotificationError(PolarPythonError):
    """Exception raised when notifications cannot be started or stopped."""

    def __init__(self, message="Failed to start or stop notifications"):
        self.message = message
        super().__init__(self.message)


class ReadCharacteristicError(PolarPythonError):
    """Exception raised when a GATT characteristic cannot be read."""

    def __init__(self, message="Failed to read GATT characteristic"):
        self.message = message
        super().__init__(self.message)


class WriteCharacteristicError(PolarPythonError):
    """Exception raised when a GATT characteristic cannot be written."""

    def __init__(self, message="Failed to write GATT characteristic"):
        self.message = message
        super().__init__(self.message)


class StreamSettingsError(PolarPythonError):
    """Exception raised when stream settings are invalid or cannot be set."""

    def __init__(self, message="Invalid or failed to set stream settings"):
        self.message = message
        super().__init__(self.message)
