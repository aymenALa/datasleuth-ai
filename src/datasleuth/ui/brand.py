"""Brand identity, custom SVG logo, and visual components for DataSleuth AI."""

from __future__ import annotations

GITHUB_REPO_URL = "https://github.com/aymenALa/datasleuth-ai"


def datasleuth_logo_svg(size: int = 36) -> str:
    """Return the custom DataSleuth AI SVG logo combining lens, data bars, and circuit nodes."""
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        'viewBox="0 0 40 40" fill="none" aria-label="DataSleuth AI Logo">'
        '<defs>'
        '<linearGradient id="dsLogoGrad" x1="4" y1="4" x2="36" y2="36" gradientUnits="userSpaceOnUse">'
        '<stop offset="0%" stop-color="#22D3EE"/>'
        '<stop offset="55%" stop-color="#38BDF8"/>'
        '<stop offset="100%" stop-color="#2DD4BF"/>'
        '</linearGradient>'
        '</defs>'
        '<rect x="2" y="2" width="36" height="36" rx="10" fill="#0B1628" stroke="url(#dsLogoGrad)" stroke-width="1.5"/>'
        '<circle cx="17.5" cy="17.5" r="8.5" stroke="url(#dsLogoGrad)" stroke-width="2.2"/>'
        '<line x1="23.8" y1="23.8" x2="30.5" y2="30.5" stroke="#22D3EE" stroke-width="2.6" stroke-linecap="round"/>'
        '<rect x="13" y="18" width="2.2" height="4" rx="0.8" fill="#38BDF8"/>'
        '<rect x="16.4" y="15" width="2.2" height="7" rx="0.8" fill="#22D3EE"/>'
        '<rect x="19.8" y="13" width="2.2" height="9" rx="0.8" fill="#2DD4BF"/>'
        '<circle cx="30" cy="10" r="2" fill="#2DD4BF"/>'
        '<path d="M25.5 11.5L28.5 10" stroke="#2DD4BF" stroke-width="1.2" stroke-linecap="round"/>'
        '</svg>'
    )
