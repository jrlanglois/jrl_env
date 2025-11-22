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
# Note: This project uses Canadian English spelling conventions:
# - Verbs: -ise (initialise, normalise, customise, organise)
# - Nouns: -our (colour, behaviour, flavour)
# Documentation is generated from docstrings which follow this convention
language = 'en'

# General configuration
extensions = [
    'sphinx.ext.autodoc',
    'sphinx.ext.napoleon',
    'sphinx.ext.viewcode',
    'sphinx.ext.intersphinx',
    'sphinx.ext.inheritance_diagram',
    'sphinx_autodoc_typehints',
]

templates_path = ['_templates']
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# HTML output options
html_theme = 'sphinx_rtd_theme'
# html_static_path = ['_static']  # Uncomment if you add custom CSS/JS

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
