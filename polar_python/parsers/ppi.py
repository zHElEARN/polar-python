"""PPI (Peak-to-Peak Interval) data parsing functions."""

from typing import List
from .. import constants


def parse_ppi_data(data: List[int], timestamp: int) -> constants.PPIData:
    """Parse PPI data from a list of integers."""
    ppi_samples = []
    offset = 10

    while offset + 6 <= len(data):
        sample = data[offset : offset + 6]

        hr = sample[0] & 0xFF
        ppi = int.from_bytes(sample[1:3], byteorder="little", signed=False)
        error_estimate = int.from_bytes(sample[3:5], byteorder="little", signed=False)
        status_byte = sample[5] & 0xFF

        invalid_ppi = (status_byte & 0x01) != 0
        skin_contact_status = (status_byte & 0x02) != 0
        skin_contact_supported = (status_byte & 0x04) != 0

        ppi_samples.append(
            {
                "ppi": ppi,
                "error_estimate": error_estimate,
                "hr": hr,
                "invalid_ppi": invalid_ppi,
                "skin_contact_status": skin_contact_status,
                "skin_contact_supported": skin_contact_supported,
            }
        )

        offset += 6

    samples = []
    if timestamp != 0:
        current_timestamp = timestamp

        for sample in reversed(ppi_samples):
            samples.append(
                constants.PPISample(
                    ppi=sample["ppi"],
                    error_estimate=sample["error_estimate"],
                    hr=sample["hr"],
                    invalid_ppi=sample["invalid_ppi"],
                    skin_contact_status=sample["skin_contact_status"],
                    skin_contact_supported=sample["skin_contact_supported"],
                    timestamp=current_timestamp,
                )
            )
            current_timestamp -= sample["ppi"] * 1_000_000

        samples.reverse()
    else:
        for sample in ppi_samples:
            samples.append(
                constants.PPISample(
                    ppi=sample["ppi"],
                    error_estimate=sample["error_estimate"],
                    hr=sample["hr"],
                    invalid_ppi=sample["invalid_ppi"],
                    skin_contact_status=sample["skin_contact_status"],
                    skin_contact_supported=sample["skin_contact_supported"],
                    timestamp=0,
                )
            )

    return constants.PPIData(samples=samples)
