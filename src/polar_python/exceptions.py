class PolarPythonError(Exception):
    pass


class ControlPointResponseError(PolarPythonError):
    """Exception raised when there is an unexpected response from the control point."""

    def __init__(self, message="Unexpected response from the control point"):
        self.message = message
        super().__init__(self.message)
