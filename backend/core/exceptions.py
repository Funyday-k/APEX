class SciPlotError(Exception):
    """Base application error."""


class ImageNotFoundError(SciPlotError):
    pass


class ExtractionNotFoundError(SciPlotError):
    pass
