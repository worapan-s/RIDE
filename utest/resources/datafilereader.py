#  Copyright 2008-2015 Nokia Networks
#  Copyright 2016-     Robot Framework Foundation
#
#  Licensed under the Apache License, Version 2.0 (the "License");
#  you may not use this file except in compliance with the License.
#  You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS,
#  WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#  See the License for the specific language governing permissions and
#  limitations under the License.

import os
from . import FakeSettings
from robotide.controller import Project
from robotide.namespace import Namespace
from robotide.spec.librarymanager import LibraryManager

RESOURCES_DIR = 'resources'
RESOURCES_RESOURCE = 'resource.resource'
DATAPATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'robotdata')


def _makepath(*elements):
    elements = [DATAPATH]+list(elements)
    return os.path.normpath(os.path.join(*elements)).replace('\\', '/')


ALL_FILES_PATH = _makepath('all_files')
RESOURCE_PATH = _makepath(RESOURCES_DIR, RESOURCES_RESOURCE)
RESOURCE_LIB_PATH = _makepath(RESOURCES_DIR, 'resource_lib_imports.robot')
RESOURCE_WITH_VARS = _makepath(RESOURCES_DIR, 'resource_with_variables.robot')
TESTCASEFILE_WITH_EVERYTHING = _makepath('testsuite', 'everything.robot')
RELATIVE_IMPORTS = _makepath('relative_imports', 'relative.robot')
LOG_MANY_SUITE = _makepath('logmanysuite', 'log_many.robot')
KW1000_TESTCASEFILE = _makepath('performance', 'suite_kw1000.robot')
KW2000_TESTCASEFILE = _makepath('performance', 'suite_kw2000.robot')
KW3000_TESTCASEFILE = _makepath('performance', 'suite_kw3000.robot')
KW4000_TESTCASEFILE = _makepath('performance', 'suite_kw4000.robot')
COMPLEX_TEST = _makepath('complex_tests', 'TestSuite.robot')
RESOURCE_WITH_VARIABLE_IN_PATH = _makepath(RESOURCES_DIR, 'resu.${extension}')
LIBRARY_WITH_SPACES_IN_PATH = _makepath('lib with spaces', 'spacelib.py')
TESTCASEFILE_WITH_RESOURCES_WITH_VARIABLES_FROM_VARIABLE_FILE = \
    _makepath('var_file_variables',
              'import_resource_with_variable_from_var_file.robot')

SIMPLE_TEST_SUITE_RESOURCE_NAME = 'Testdata Resource'
SIMPLE_TEST_SUITE_RESOURCE_FILE = 'testdata_resource.robot'
SIMPLE_TEST_SUITE_INNER_RESOURCE_DIR = 'Resources Folder'
SIMPLE_TEST_SUITE_PATH = \
    _makepath('simple_testsuite_with_different_namespaces')

FOR_LOOP_PATH = _makepath('forloop')

ARGUMENTS_PATH = _makepath('arguments_suite')

SIMPLE_PROJECT = _makepath('simple', 'test.robot')

UNUSED_KEYWORDS_PATH = _makepath('unused_keywords')

FINDWHEREUSED_VARIABLES_PATH = _makepath('findwhereused_variables')

SMALL_TEST_PATH = _makepath('small_test')

IMPORTS = _makepath('imports')


def construct_project(datapath, temp_dir_for_excludes=None):
    print("DEBUG: construct_project with argpath: %s\n" % datapath)
    settings = FakeSettings({'excludes': temp_dir_for_excludes, 'txt number of spaces': 2})
    print("DEBUG: construct_project FakeSettings: %s\n" % list(settings.iteritems()))
    library_manager = LibraryManager(':memory:')
    library_manager.create_database()
    project = Project(Namespace(settings), settings, library_manager)
    print("DEBUG: construct_project Project: %s\n" % project.display_name)
    project.load_data(datapath)  #, NullObserver())
    # DEBUG
    print("DEBUG: Path arg is: %s\n" % datapath)
    return project


def get_ctrl_by_name(name, datafiles):
    for file in datafiles:
        if file.name == name:
            return file
    return None
