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
import unittest
from mockito import mock

from robotide.robotapi import TestCaseFile, ResourceFile
from robotide.controller import Project
from robotide.controller.ctrlcommands import RenameResourceFile
from robotide.controller.filecontrollers import TestCaseFileController
from robotide.namespace.namespace import Namespace

from utest.resources import (
    MINIMAL_SUITE_PATH, SUITEPATH, MessageRecordingLoadObserver, FakeSettings)
from robotide.spec.librarymanager import LibraryManager


class TestFormatChange(unittest.TestCase):

    def setUp(self):
        ns = Namespace(FakeSettings())
        self.project = ProjectChecker(ns, settings=ns.settings)

    def test_format_change_to_tsv(self):
        self._test_format_change('tsv')

    def test_format_change_to_txt(self):
        self._test_format_change('txt')

    def _test_format_change(self, to_format):
        controller = self._get_file_controller(MINIMAL_SUITE_PATH)
        assert controller is not None
        controller.save_with_new_format(to_format)
        self._assert_removed(MINIMAL_SUITE_PATH)
        path_with_tsv = os.path.splitext(MINIMAL_SUITE_PATH)[0] + '.'+to_format
        self._assert_serialized(path_with_tsv)

    def test_recursive_format_change(self):
        controller = self._get_file_controller(SUITEPATH)
        controller.save_with_new_format_recursive('robot')
        init_file = os.path.join(SUITEPATH,'__init__.robot')
        self._assert_serialized(init_file)
        path_to_sub_init_file = os.path.join(SUITEPATH,'subsuite','__init__.robot')
        self._assert_serialized(path_to_sub_init_file)
        path_to_old_sub_init_file = os.path.join(SUITEPATH,'subsuite','__init__.tsv')
        self._assert_removed(path_to_old_sub_init_file)
        path_to_txt_file = os.path.join(SUITEPATH,'subsuite','test.robot')
        self._assert_not_serialized(path_to_txt_file)
        self._assert_not_removed(path_to_txt_file)

    def _get_file_controller(self, path):
        self.project.load_datafile(path, MessageRecordingLoadObserver())
        return self.project.controller

    def _assert_serialized(self, path):
        assert path in self.project.serialized_files

    def _assert_not_serialized(self, path):
        assert not path in self.project.serialized_files

    def _assert_removed(self, path):
        assert path in self.project.removed_files

    def _assert_not_removed(self, path):
        assert not path in self.project.removed_files


class ProjectChecker(Project):

    def __init__(self, namespace, settings=None, library_manager=None):
        self.removed_files = []
        self.serialized_files = []
        library_manager = library_manager or LibraryManager(':memory:')
        if not library_manager:
            library_manager.create_database()
        Project.__init__(self, namespace, settings, library_manager)

    def save(self, controller):
        self.serialized_files.append(controller.source)

    def _remove_file(self, path):
        self.removed_files.append(path)


class _UnitTestsWithWorkingResourceImports(unittest.TestCase):

    def _create_data(self, resource_name, resource_import):
        res_path = os.path.abspath(resource_name)
        tcf = TestCaseFile(source=os.path.abspath('test.robot'))
        tcf.setting_table.add_resource(resource_import)
        tcf.variable_table.add('${dirname}', os.path.abspath('.').replace('\\', '\\\\'))
        tcf.variable_table.add('${path}', os.path.abspath(resource_name).replace('\\', '\\\\'))
        library_manager = LibraryManager(':memory:')
        library_manager.create_database()
        self.project = Project(Namespace(FakeSettings()), FakeSettings(), library_manager)
        self.project.controller = TestCaseFileController(tcf, self.project)
        res = ResourceFile(source=res_path)
        self.res_controller = \
            self.project._resource_file_controller_factory.create(res)
        self.project.namespace._resource_factory.cache[os.path.normcase(res_path)] = res

    @property
    def import_setting(self):
        return self.project.controller.imports[0]

    def _verify_import_reference(self, imp_is_resolved):
        if imp_is_resolved:
            self._verify_import_reference_exists()
        else:
            self._verify_import_reference_is_not_resolved()

    def _verify_import_reference_exists(self):
        assert (self.import_setting.get_imported_controller() ==
                          self.res_controller)

    def _verify_import_reference_is_not_resolved(self):
        imported_controller = self.import_setting.get_imported_controller()
        if imported_controller:
            msg = 'Resolved to source %s' % imported_controller.source
        else:
            msg = None
        assert imported_controller is None, msg


class TestResourceFileRename(_UnitTestsWithWorkingResourceImports):

    def test_import_is_invalidated_when_resource_file_name_changes(self):
        self._create_data('resource.robot', '${path}')
        self._verify_import_reference_exists()
        self._rename_resource('resu', False)
        self._verify_import_reference_is_not_resolved()
        assert self.import_setting.name == '${path}'

    def test_import_is_modified_when_resource_file_name_changes_and_habaa(self):
        self._create_data('fooo.robot', 'fooo.robot')
        self._verify_import_reference_exists()
        self._rename_resource('gooo', True)
        self._verify_import_reference_exists()
        assert self.import_setting.name == 'gooo.robot'

    """
    # DEBUG test fails with invoke but passes locally
    def test_cancel_execute_when_modify_imports_is_canceled(self):
        self._create_data('fooo.robot', 'fooo.robot')
        self._verify_import_reference_exists()
        self._execute_rename_resource('gooo', None)
        # just2delay = os.getpid()  # DEBUG
        # print("DEBUG: test_cancel_execute_when_modify_imports_is_canceled PID=%s\n" % just2delay)
        assert_false(self.res_controller.remove_from_filesystem.called)
        assert_false(self.res_controller.save.called)
    """

    def test_import_is_invalidated_when_resource_file_name_changes_and_hubaa(self):
        self._create_data('resource.robot', '${path}')
        self._verify_import_reference_exists()
        self._rename_resource('resu', True)
        self._verify_import_reference_is_not_resolved()
        assert self.import_setting.name == '${path}'

    def _execute_rename_resource(self, new_basename, boolean_variable):
        self.res_controller.remove_from_filesystem = mock()
        self.res_controller.save = mock()
        self.res_controller.execute(RenameResourceFile(new_basename, lambda : boolean_variable))

    def _rename_resource(self, new_basename, boolean_variable):
        self._execute_rename_resource(new_basename, boolean_variable)
        assert self.res_controller.remove_from_filesystem.called
        assert self.res_controller.save.called


class TestResourceFormatChange(_UnitTestsWithWorkingResourceImports):

    def test_imports_are_updated(self):
        self._create_data('name.robot', 'name.robot')
        self._change_format('BAR')
        self._assert_format_change('name.bar', 'name.bar')

    def test_imports_with_variables_and_path_are_updated(self):
        self._create_data('name.robot', '${dirname}${/}name.robot')
        self._change_format('cock')
        self._assert_format_change('${dirname}${/}name.cock', 'name.cock')

    def test_imports_with_only_variables(self):
        self._create_data('res.robot', '${path}')
        self._change_format('zap')
        self._assert_format_change('${path}', 'res.zap', imp_is_resolved=False)

    def _change_format(self, format):
        self.res_controller.set_format(format)

    def _assert_format_change(self, import_name, resource_path,
                              imp_is_resolved=True):
        imp = self.import_setting
        assert imp.name == import_name
        assert self.res_controller.filename == os.path.abspath(resource_path)
        self._verify_import_reference(imp_is_resolved)


if __name__ == '__main__':
    unittest.main()

