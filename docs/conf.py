# Configuration file for Sphinx documentation builder

import os
import sys
sys.path.insert(0, os.path.abspath('..'))

# Project information
project = 'jrl_env'
copyright = '2025, Joël R. Langlois'
author = 'Joël R. Langlois'
release = '1.0.0'

# Language and spelling
# Note: This project uses Canadian English spelling conventions. See README.md for details.
language = 'en'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx.ext.graphviz',  # For call graphs and diagrams
    'sphinx_autodoc_typehints',
    'myst_parser',  # Markdown support
]

# MyST Parser configuration (for Markdown support)
myst_enable_extensions = [
    "colon_fence",
    "deflist",
    "tasklist",
]

# Source file suffixes
source_suffix = {
    '.rst': 'restructuredtext',
    '.md': 'markdown',
}

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'furo'
# html_static_path = ['_static']  # Uncomment if you add custom CSS/JS

# Furo theme options
html_theme_options = {
    "light_css_variables": {
        "color-brand-primary": "#2980b9",
        "color-brand-content": "#2980b9",
    },
}

# Napoleon settings (for Google/NumPy style docstrings)
napoleon_google_docstring = True
napoleon_numpy_docstring = True
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = False
napoleon_include_special_with_doc = True
napoleon_use_admonition_for_examples = True
napoleon_use_admonition_for_notes = True
napoleon_use_admonition_for_references = True
napoleon_use_ivar = False
napoleon_use_param = True
napoleon_use_rtype = True
napoleon_preprocess_types = True
napoleon_type_aliases = None

# AutoDoc settings
autodoc_default_options = {
    'members': True,
    'member-order': 'bysource',
    'special-members': '__init__',
    'undoc-members': True,
    'exclude-members': '__weakref__'
}

# Intersphinx configuration
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Graphviz configuration (for call graphs and diagrams)
graphviz_output_format = 'svg'
graphviz_dot_args = [
    '-Nfontname=Helvetica',
    '-Efontname=Helvetica',
    '-Gfontname=Helvetica',
    '-Nfontsize=10',
    '-Efontsize=10',
]

# Inheritance diagram configuration
inheritance_graph_attrs = {
    'rankdir': 'TB',  # Top to bottom
    'size': '"8.0, 10.0"',
    'fontsize': 10,
    'ratio': 'compress',
}

inheritance_node_attrs = {
    'shape': 'box',
    'fontsize': 10,
    'height': 0.5,
    'color': '"#2980b9"',
    'style': '"rounded,filled"',
    'fillcolor': '"#ecf0f1"',
}
