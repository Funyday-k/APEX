"""Scale calibration pixel coordinates when the working image is resized."""

from core.schemas import CalibrationConfig, CalibrationPoint, Point


def scale_calibration(config: CalibrationConfig, scale: float) -> CalibrationConfig:
    if abs(scale - 1.0) < 1e-6:
        return config

    def scale_point(cp: CalibrationPoint) -> CalibrationPoint:
        return CalibrationPoint(
            pixel=Point(x=cp.pixel.x * scale, y=cp.pixel.y * scale),
            data=cp.data,
        )

    return CalibrationConfig(
        x_axis=config.x_axis.model_copy(
            update={"ref1": scale_point(config.x_axis.ref1), "ref2": scale_point(config.x_axis.ref2)}
        ),
        y_axis=config.y_axis.model_copy(
            update={"ref1": scale_point(config.y_axis.ref1), "ref2": scale_point(config.y_axis.ref2)}
        ),
    )
