"""Load CLI messages through standard gettext catalogs, defaulting to English."""

import gettext
from pathlib import Path


def translate(key: str, **values: object) -> str:
    """Format a message using gettext's locale environment and English fallback.

    LANGUAGE, LC_ALL, LC_MESSAGES and LANG follow gettext's normal precedence.
    Source catalogs live alongside compiled catalogs under locales/.
    """
    locale_dir = Path(__file__).with_name("locales")
    try:
        messages = gettext.translation("messages", localedir=str(locale_dir))
    except FileNotFoundError:
        messages = gettext.translation(
            "messages", localedir=str(locale_dir), languages=["en"]
        )
    return messages.gettext(key).format(**values)
