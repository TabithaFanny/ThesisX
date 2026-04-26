"""Icons subpackage - contains specialized icon modules like plagiarism_icons."""

# Re-export all icon functions from icon_functions module
from app.ui.icon_functions import *  # noqa: F401, F403

# This makes the icons directory a package so that plagiarism_icons.py
# can be imported as app.ui.icons.plagiarism_icons

