"""Shared helpers for LaTeX reporting."""


def escape_latex(text: str) -> str:
    """Escape special LaTeX characters. Backslash is replaced first to avoid double-escaping."""
    # Order matters: replace \ first so that \ in other replacements are not re-expanded
    special_chars = [
        ('\\', r'\textbackslash{}'),
        ('&', r'\&'),
        ('%', r'\%'),
        ('$', r'\$'),
        ('#', r'\#'),
        ('^', r'\textasciicircum{}'),
        ('_', r'\_'),
        ('{', r'\{'),
        ('}', r'\}'),
        ('~', r'\textasciitilde{}'),
    ]
    for char, replacement in special_chars:
        text = text.replace(char, replacement)
    return text
