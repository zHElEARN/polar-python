from dataclasses import dataclass

from .pmd_data_frame import PmdDataFrame, PmdDataFrameType


@dataclass
class PPIData:
    """Represents Peak-to-Peak Interval (PPI) measurement data.

    Attributes:
        samples: A list of PPISample objects containing the interval data.
    """

    @dataclass
    class PPISample:
        """Represents a single Peak-to-Peak Interval (PPI) sample.

        Attributes:
            ppi: The peak-to-peak interval in milliseconds (ms).
            error_estimate: The error estimate of the PPI measurement in milliseconds (ms).
            hr: The calculated heart rate in beats per minute (BPM).
            invalid_ppi: Indicates whether the PPI measurement is considered invalid.
            skin_contact_status: Indicates whether the sensor has detected skin contact.
            skin_contact_supported: Indicates whether the device supports skin contact detection.
        """

        ppi: int
        error_estimate: int
        hr: int
        invalid_ppi: bool
        skin_contact_status: bool
        skin_contact_supported: bool
        # timestamp: int

    samples: list[PPISample]

    PPI_SAMPLE_CHUNK = 6

    @classmethod
    def from_dataframe(cls, frame: PmdDataFrame) -> "PPIData":
        if frame.is_compressed_frame:
            raise ValueError(f"Compressed FrameType: {frame.frame_type.name} is not supported by PPI data parser")

        if frame.frame_type == PmdDataFrameType.TYPE_0:
            return cls._data_from_raw_type_0(frame)
        else:
            raise ValueError(f"Raw FrameType: {frame.frame_type.name} is not supported by PPI data parser")

    @classmethod
    def _data_from_raw_type_0(cls, frame: PmdDataFrame) -> "PPIData":
        """Parse raw TYPE_0 data."""
        content = frame.data_content
        offset = 0
        step = cls.PPI_SAMPLE_CHUNK

        raw_samples = []
        while offset + step <= len(content):
            chunk = content[offset : offset + step]

            hr = chunk[0]
            ppi = int.from_bytes(chunk[1:3], byteorder="little", signed=False)
            error_estimate = int.from_bytes(chunk[3:5], byteorder="little", signed=False)
            status_byte = chunk[5]

            invalid_ppi = (status_byte & 0x01) != 0
            skin_contact_status = (status_byte & 0x02) != 0
            skin_contact_supported = (status_byte & 0x04) != 0

            raw_samples.append(
                {
                    "ppi": ppi,
                    "error_estimate": error_estimate,
                    "hr": hr,
                    "invalid_ppi": invalid_ppi,
                    "skin_contact_status": skin_contact_status,
                    "skin_contact_supported": skin_contact_supported,
                }
            )

            offset += step

        final_samples = []
        if frame.timestamp != 0:
            current_timestamp = frame.timestamp

            for sample in reversed(raw_samples):
                final_samples.append(
                    cls.PPISample(
                        ppi=int(sample["ppi"]),
                        error_estimate=int(sample["error_estimate"]),
                        hr=int(sample["hr"]),
                        invalid_ppi=bool(sample["invalid_ppi"]),
                        skin_contact_status=bool(sample["skin_contact_status"]),
                        skin_contact_supported=bool(sample["skin_contact_supported"]),
                        # timestamp=current_timestamp,
                    )
                )
                current_timestamp -= int(sample["ppi"]) * 1_000_000

            final_samples.reverse()
        else:
            for sample in raw_samples:
                final_samples.append(
                    cls.PPISample(
                        ppi=int(sample["ppi"]),
                        error_estimate=int(sample["error_estimate"]),
                        hr=int(sample["hr"]),
                        invalid_ppi=bool(sample["invalid_ppi"]),
                        skin_contact_status=bool(sample["skin_contact_status"]),
                        skin_contact_supported=bool(sample["skin_contact_supported"]),
                        # timestamp=0,
                    )
                )

        return cls(samples=final_samples)
