class CancelledError(Exception):
    pass


class DependencyError(RuntimeError):
    pass


class DownloadError(RuntimeError):
    pass
