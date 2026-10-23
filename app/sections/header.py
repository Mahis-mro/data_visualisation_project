"""Page header: school logo, author, professor, LinkedIn link, project title."""
import base64
import html
import mimetypes

import streamlit as st

from utils import constants as C


def _logo_html(width: int = 150):
    """Logo as an inline <img> with alt text, on a white badge (readable in dark mode)."""
    path = next((p for p in C.LOGO_CANDIDATES if p.exists()), None)
    if path is None:
        return None
    mime = "image/svg+xml" if path.suffix == ".svg" else mimetypes.guess_type(path)[0]
    data = base64.b64encode(path.read_bytes()).decode()
    return (
        f'<img src="data:{mime};base64,{data}" width="{width}" alt="EFREI logo" '
        'style="background:#fff;padding:8px 12px;border-radius:8px;">'
    )


@st.cache_data(show_spinner=False)
def _cached_logo_html():
    return _logo_html()


def render_header():
    with st.container(border=True):
        c_logo, c_name, c_link = st.columns([1.5, 4, 1.4], vertical_alignment="center")
        with c_logo:
            logo = _cached_logo_html()
            if logo:
                st.markdown(logo, unsafe_allow_html=True)
            else:   # fallback when no file assets/efrei_logo.* exists
                st.markdown('<p class="app-name">EFREI</p>', unsafe_allow_html=True)
        with c_name:
            st.markdown(
                f'<p class="app-name">{html.escape(C.AUTHOR_NAME)}</p>'
                f'<p class="app-sub">{html.escape(C.COURSE_TAG)}</p>'
                f'<p class="app-sub">Professor: {html.escape(C.PROFESSOR_NAME)}</p>',
                unsafe_allow_html=True,
            )
        with c_link:
            st.link_button("LinkedIn profile", C.LINKEDIN_URL, width="stretch")

    st.title("Behind the Kitchen Door")
    st.markdown("##### How safe is our food? A data story from French food-safety inspections")
