try:
    import werkzeug
    # Some environments may have a werkzeug module without __version__ attr (packaging mismatch).
    if not hasattr(werkzeug, '__version__'):
        werkzeug.__version__ = '3.1.0'
except Exception:
    # If werkzeug is missing entirely, tests that exercise Flask will fail later; let that surface.
    pass
