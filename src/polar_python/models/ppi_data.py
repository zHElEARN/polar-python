from dataclasses import dataclass


@dataclass
class PPIData:
    """Represents PPI data."""

    @dataclass
    class PPISample:
        """Represents a single PPI sample."""

        ppi: int
        error_estimate: int
        hr: int
        invalid_ppi: bool
        skin_contact_status: bool
        skin_contact_supported: bool
        timestamp: int

    samples: list[PPISample]
