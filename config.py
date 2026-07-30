import argparse
import dataclasses
import logging

try:
    import yaml
except ImportError:
    yaml = None


@dataclasses.dataclass
class Config:
    camera_index: int = 0

    pinch_threshold: float = 0.4
    open_palm_min_fingers: int = 4
    fist_max_fingers: int = 0

    kalman_process_noise: float = 1e-3
    kalman_measurement_noise: float = 1e-1

    palette_dwell_time: float = 0.6
    default_num_axes: int = 6

    calibrate: bool = True
    calibration_frames: int = 45

    log_level: str = "INFO"

    @staticmethod
    def from_yaml(path):
        if yaml is None:
            logging.warning('pyyaml not installed, ignoring --config %s', path)
            return {}
        try:
            with open(path, "r") as f:
                data = yaml.safe_load(f) or {}
            return data
        except FileNotFoundError:
            logging.warning('config file not found: %s', path)
            return dict()


def parse_args():
    parser = argparse.ArgumentParser(description='petrykivka air draw')
    parser.add_argument('--config', type=str, default=None,
                         help='path to a YAML config file')
    parser.add_argument('--camera-index', type=int, default=None)
    parser.add_argument('--pinch-threshold', type=float, default=None,
                         help='fixed pinch threshold; skips calibration if set')
    parser.add_argument('--no-calibrate', action='store_true',
                         help='skip the startup hand-size calibration')
    parser.add_argument('--calibration-frames', type=int, default=None)
    parser.add_argument('--log-level', type=str, default=None,
                         choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'])
    return parser.parse_args()


def build_config():
    args = parse_args()
    config = Config()

    if args.config:
        overrides = Config.from_yaml(args.config)
        config = dataclasses.replace(config, **{
            k: v for k, v in overrides.items() if k in config.__dataclass_fields__
        })

    cli_overrides = dict()
    if args.camera_index is not None:
        cli_overrides['camera_index'] = args.camera_index
    if args.pinch_threshold is not None:
        cli_overrides['pinch_threshold'] = args.pinch_threshold
        cli_overrides['calibrate'] = False
    if args.no_calibrate:
        cli_overrides['calibrate'] = False
    if args.calibration_frames is not None:
        cli_overrides['calibration_frames'] = args.calibration_frames
    if args.log_level is not None:
        cli_overrides['log_level'] = args.log_level

    return dataclasses.replace(config, **cli_overrides)