"""Pet breathing / pulse scan component (components/petscan), declared in its own
module so Streamlit registers it under a stable name."""
import os
import streamlit.components.v1 as _components

_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "components", "petscan")
petscan_component = _components.declare_component("petainurse_petscan", path=_DIR)
