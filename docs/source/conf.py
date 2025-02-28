# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
#
# import os
# import sys
# sys.path.insert(0, os.path.abspath('.'))

 
import subprocess,os

read_the_docs_build = os.environ.get('READTHEDOCS', None) == 'True'

if read_the_docs_build:

    subprocess.call('doxygen Doxyfile', shell=True)


#  import subprocess
#  subprocess.call('doxygen Doxyfile', shell=True)

# -- Project information -----------------------------------------------------

project = 'systemc-clang'
copyright = '2020: Core -- Anirudh M. Kaushik, Zhuanhao Wu and Hiren Patel; 2020: HDL Plugin -- Maya Gokhale'
author = 'Anirudh M. Kaushik, Zhuanhao Wu and Hiren Patel'

# The full version, including alpha/beta/rc tags
release = '2.0.0'


# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['recommonmark'
        , 'sphinx.ext.autodoc'
        , 'sphinx.ext.viewcode'
        # , 'sphinx.ext.'
        , 'breathe'
        , 'exhale'
        ]

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']


# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
html_theme = 'sphinx_rtd_theme' #'alabaster'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
#html_static_path = ['_static']
#html_extra_path = ['doxydoc/html']

# -- Breath and Exhale 


breathe_default_project = "systemc-clang"
#
breathe_projects = {
    "systemc-clang": "./doxydoc/xml"
}

exhale_args = {
    "containmentFolder":     "./api",
    "rootFileName":          "library_root.rst",
    "rootFileTitle":         "Library API",
    "doxygenStripFromPath":  "..",
    "createTreeView":        True,
    "exhaleExecutesDoxygen": False,
    #"exhaleDoxygenStdin":    "INPUT = ../../src",
    "listingExclude": ["r.*nlohmann"]
}
#
primary_domain = 'cpp'
highlight_language = 'cpp'

