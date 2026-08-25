"""Static files app config.

tech.md section 3 puts the tailwind input at static/src/css/app.css, inside the
directory collectstatic walks. Collecting it breaks the manifest: its font urls
are relative to the built file, so ../fonts resolves to src/fonts and nothing is
there. The whole src tree is build input, never a served asset.
"""

from django.contrib.staticfiles.apps import StaticFilesConfig


class OskStaticFilesConfig(StaticFilesConfig):
    ignore_patterns = [*StaticFilesConfig.ignore_patterns, "src"]
