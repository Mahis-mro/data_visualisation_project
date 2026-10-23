"""Shared plotting helpers: consistent style, reference lines, text alternatives."""
import html

import streamlit as st

from utils.constants import REFERENCE_COLOR


def plot_chart(fig, alt: str | None = None, **kwargs):
    """Render a Plotly chart with consistent typography and a text alternative.

    `alt` is shown under the chart for screen-reader / low-vision users, since
    Streamlit does not expose an alt attribute on charts.
    """
    fig.update_layout(font=dict(size=13), margin=dict(l=25, r=25, b=30))
    kwargs.setdefault("width", "stretch")
    st.plotly_chart(fig, **kwargs)
    if alt:
        st.caption(f"Chart description: {alt}")


def add_reference(fig, value: float, label: str, orientation: str = "v"):
    """Dashed reference line. orientation 'v' = vertical line (horizontal bars)."""
    kwargs = dict(
        line_dash="dash", line_color=REFERENCE_COLOR, line_width=1.5,
        annotation_text=label, annotation_position="top",
        annotation_font=dict(size=12, color=REFERENCE_COLOR),
    )
    if orientation == "v":
        fig.add_vline(x=value, **kwargs)
    else:
        kwargs["annotation_position"] = "top left"
        fig.add_hline(y=value, **kwargs)
    return fig


CSS = """
<style>
.headline{border-left:4px solid #3A6EA5;background:rgba(58,110,165,.10);
  padding:.65rem .95rem;margin:.3rem 0 1rem;border-radius:0 8px 8px 0;
  font-weight:600;font-size:1.02rem;line-height:1.45;}
.chapter-label{font-size:.78rem;letter-spacing:.14em;text-transform:uppercase;
  font-weight:700;opacity:.7;margin:.2rem 0 0;}
.chapter-title{font-size:1.7rem;font-weight:800;margin:0 0 .15rem;line-height:1.2;}
.chapter-question{font-size:1.05rem;opacity:.85;margin:0 0 1.1rem;}
.app-name{font-weight:800;letter-spacing:.06em;font-size:1.15rem;margin:0;}
.app-sub{opacity:.75;font-size:.9rem;margin:0;}
.next-hint{border-top:1px solid rgba(128,128,128,.35);margin-top:1.5rem;
  padding-top:.6rem;opacity:.8;font-style:italic;}
.step-num{font-size:1.6rem;font-weight:800;opacity:.6;line-height:1;}
</style>
"""


def inject_css():
    st.markdown(CSS, unsafe_allow_html=True)


def headline(text: str):
    """One-sentence takeaway shown at the top of a section."""
    clean = text.replace("Headline: ", "", 1).replace("**", "").strip()
    clean = clean[:1].upper() + clean[1:]
    st.markdown(f'<div class="headline">{html.escape(clean)}</div>', unsafe_allow_html=True)


def chapter_header(number: int, total: int, title: str, question: str):
    """Chapter banner: position in the story, title and the question it answers."""
    st.markdown(
        f'<p class="chapter-label">Chapter {number} of {total}</p>'
        f'<p class="chapter-title">{html.escape(title)}</p>'
        f'<p class="chapter-question">{html.escape(question)}</p>',
        unsafe_allow_html=True,
    )


def next_hint(text: str):
    """Bridge sentence pointing to the next chapter."""
    st.markdown(f'<div class="next-hint">Next: {html.escape(text)}</div>', unsafe_allow_html=True)
