"""
Provide zero-FOUC (Flash of Unstyled Content) theme engine primitives. Support semantic flicker-free dark mode via W3C Media Queries Level 5 prefers-color-scheme.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("assessment_engine.infrastructure.primitives.zero_fouc_theme")


class ZeroFoucThemeService:
    @staticmethod
    def get_inline_head_script() -> str:
        """Inject a synchronous blocking script into <head>. Execute before first paint to prevent dark mode white flash."""
        return """<script>
        !function(){
            try {
                var stored = localStorage.getItem('app_theme');
                var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
                var isDark = stored === 'dark' || (!stored && prefersDark);
                document.documentElement.classList.toggle('dark', isDark);
            } catch(e) {}
        }();
        </script>"""


class ZeroFOUCThemePrimitive:
    """
    Inject an anti-flicker script for light and dark theme management.
    """

    def generate_inline_head_script(self, default_mode: str = "light") -> str:
        """Generate the inline <script> block for the <head> of index.html."""
        return f"""<script>
(function() {{
  try {{
    var stored = localStorage.getItem('theme');
    var prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    var defaultMode = '{default_mode}';
    if (stored === 'dark' || (!stored && defaultMode === 'dark') || (!stored && defaultMode === 'system' && prefersDark)) {{
      document.documentElement.classList.add('dark');
    }} else {{
      document.documentElement.classList.remove('dark');
    }}
  }} catch (e) {{}}
}})();
</script>"""


zero_fouc_theme = ZeroFOUCThemePrimitive()
