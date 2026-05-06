import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

import streamlit as st
from lib import store, analytics, combined_score  # noqa: F401
import pages.tasks as tasks_page
import pages.habits as habits_page
import pages.dashboard as dashboard_page


st.set_page_config(
    page_title="ProductKitchen",
    page_icon="🍳",
    layout="wide",
    initial_sidebar_state="expanded",
)

PAGES = {
    "📊 Combined Dashboard": dashboard_page,
    "✅ Tasks Tracker": tasks_page,
    "⏱ Habits Tracker": habits_page,
}


def main():
    st.sidebar.title("🍳 ProductKitchen")
    st.sidebar.markdown("---")

    selection = st.sidebar.radio("Navigate", list(PAGES.keys()), index=0)

    st.sidebar.markdown("---")
    st.sidebar.caption("Track tasks + habits → honest productivity.")

    PAGES[selection].render()


if __name__ == "__main__":
    main()
