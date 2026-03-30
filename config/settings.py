"""Project settings.

This module is maintained for backwards compatibility with older deployment setups
that reference `config.settings` directly. The actual configuration is defined in
`config/base.py` and imported by the environment-specific configs (`dev.py`,
`prod.py`).

To keep behavior consistent, this file simply re-exports everything from `base.py`.
"""

from .base import *
