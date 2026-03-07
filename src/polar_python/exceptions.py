class PolarPythonError(Exception):
    """Base exception class for all custom errors raised by this library."""

    pass


class ControlPointResponseError(PolarPythonError):
    """Raised when the device's PMD control point returns an unexpected or invalid response.

    Attributes:
        message: A descriptive explanation of the error.
    """

    def __init__(self, message="Unexpected response from the control point"):
        """Initializes the ControlPointResponseError.

        Args:
            message: The error message detailing the unexpected response. Defaults to
                a generic unexpected response message.
        """
        self.message = message
        super().__init__(self.message)
