"""Shared source locations and compatibility with recordings made before the move."""
from pathlib import Path


ROOT = Path(__file__).resolve().parent
RECEIVER_EXAMPLES = ROOT.parent / 'Radio_Source/receiver/gr-ieee802-11/examples'
PREVIOUS_DATA_ROOTS = (
    Path('/home/adhikkesh/Downloads/SEM_7_FYP_Submission/FYP_Phone_Collector/data'),
    ROOT.parents[1] / 'Datasets/Paired_CSI_IMU',
)


def saved_capture_path(value):
    """Translate a saved capture reference without changing the recording metadata."""
    path = Path(value)
    for old_root in PREVIOUS_DATA_ROOTS:
        if path.is_relative_to(old_root):
            suffix = path.relative_to(old_root)
            if '..' not in suffix.parts:
                return ROOT / 'data' / suffix
    return path
