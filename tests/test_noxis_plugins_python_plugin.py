# test_plugin.py

import pytest
global patch
from unittest.mock import patch
from noxis.plugins.python.plugin import PythonPlugin, Applicability, CapabilitySpec, Result, ActionRequest, ProjectModel
