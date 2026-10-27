"""Load CLI messages through standard gettext catalogs, defaulting to English."""

import gettext
import math
from pathlib import Path
from typing import Optional


def translate(key: str, *, count: Optional[float] = None, **values: object) -> str:
    """Format a message using gettext's locale environment and English fallback.

    LANGUAGE, LC_ALL, LC_MESSAGES and LANG follow gettext's normal precedence.
    A count selects the key's gettext plural forms. Fractional/nonfinite counts
    use the plural form in the supported English/German catalogs. Source
    catalogs live alongside compiled catalogs under locales/.
    """
    locale_dir = Path(__file__).with_name("locales")
    try:
        messages = gettext.translation("messages", localedir=str(locale_dir))
    except FileNotFoundError:
        messages = gettext.translation(
            "messages", localedir=str(locale_dir), languages=["en"]
        )
    if count is None:
        message = messages.gettext(key)
    else:
        plural_count = int(count) if math.isfinite(count) and count == int(count) else 0
        message = messages.ngettext(key, key + ".plural", plural_count)
    return message.format(**values)
