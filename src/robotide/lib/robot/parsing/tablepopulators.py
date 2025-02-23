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

import re

from robotide.lib.robot.utils import py2to3

from .comments import Comments
from .settings import Documentation, MetadataList


class Populator(object):
    """Explicit interface for all populators."""

    def add(self, row):
        raise NotImplementedError

    def populate(self):
        raise NotImplementedError


@py2to3
class NullPopulator(Populator):

    def add(self, row):
        """ To be overriden """
        pass

    def populate(self):
        """ To be overriden """
        pass

    def __nonzero__(self):
        return False


class _TablePopulator(Populator):

    def __init__(self, table):
        self._table = table
        self._populator = NullPopulator()

    def add(self, row):
        self._add(row)

    def _is_cacheable_comment_row(self, row):
        return row.is_commented()

    def _add(self, row):
        if not self._is_continuing(row):
            self._populator.populate()
            self._populator = self._get_populator(row)
        self._populator.add(row)

    def _is_continuing(self, row):
        return row.is_continuing() and self._populator

    def _get_populator(self, row):
        raise NotImplementedError

    def populate(self):
        # DEBUG: Not using comments self._consume_comments()
        self._populator.populate()


class SettingTablePopulator(_TablePopulator):

    def _get_populator(self, row):
        setter = self._table.get_setter(row.head) if row.head else None
        if row.head == '...':
            setter = self._table.get_setter('Documentation')
        if not setter:
            return NullPopulator()
        if isinstance(setter.__self__, Documentation):
            return DocumentationPopulator(setter)
        if isinstance(setter.__self__, MetadataList):
            return MetadataPopulator(setter)
        return SettingPopulator(setter)


class VariableTablePopulator(_TablePopulator):

    def _get_populator(self, row):
        return VariablePopulator(self._table.add, row.head)

    def _populate_standalone_comment(self, comment):
        populator = self._get_populator(comment)
        populator.add(comment)
        populator.populate()

    def populate(self):
        self._populator.populate()
        # DEBUG Not using comments self._consume_standalone_comments()


class _StepContainingTablePopulator(_TablePopulator):

    def _is_continuing(self, row):
        return row.is_indented() and self._populator or row.is_commented()

    def _is_cacheable_comment_row(self, row):
        return row.is_commented() and not self._populator


class TestTablePopulator(_StepContainingTablePopulator):

    def _get_populator(self, row):
        return TestCasePopulator(self._table.add)


class KeywordTablePopulator(_StepContainingTablePopulator):

    def _get_populator(self, row):
        return UserKeywordPopulator(self._table.add)


class ForLoopPopulator(Populator):

    def __init__(self, for_loop_creator):
        self._for_loop_creator = for_loop_creator
        self._loop = None
        self._populator = NullPopulator()
        self._declaration = []
        self._declaration_comments = []

    def add(self, row):
        if not self._loop:
            declaration_ready = self._populate_declaration(row)
            if not declaration_ready:
                return
            self._create_for_loop()
        if not row.is_continuing():
            self._populator.populate()
            self._populator = StepPopulator(self._loop.add_step)
        self._populator.add(row)

    def _populate_declaration(self, row):
        if row.starts_for_loop() or row.is_continuing():
            self._declaration.extend(row.dedent().data)
            self._declaration_comments.extend(row.comments)
            return False
        return True

    def _create_for_loop(self):
        self._loop = self._for_loop_creator(self._declaration,
                                            self._declaration_comments)

    def populate(self):
        if not self._loop:
            self._create_for_loop()
        self._populator.populate()


class _TestCaseUserKeywordPopulator(Populator):

    def __init__(self, test_or_uk_creator):
        self._test_or_uk_creator = test_or_uk_creator
        self._test_or_uk = None
        self._populator = NullPopulator()
        self._documentation_setting = False
        # DEBUG: Not using comments self._comment_cache = CommentCache()

    def add(self, row):
        # if row:
        #    print(f"DEBUG: _TestCaseUserKeywordPopulator enter row {row.cells} {row.comments}")
        # DEBUG: Not using comments
        # if row.is_commented():
        #    self._comment_cache.add(row)
        #    # print(f"DEBUG: _TestCaseUserKeywordPopulator returning from comment {row.cells} {row.comments}")
        #    return
        if not self._test_or_uk:
            self._test_or_uk = self._test_or_uk_creator(row.head)
        dedented_row = row.dedent()
        if dedented_row:
            self._handle_data_row(dedented_row)

    def _handle_data_row(self, row):
        if not self._continues(row):
            self._populator.populate()
        else:
            # Need to add a new row to split by ...
            self.add(row)
        self._populator = self._get_populator(row)
        self._populator.add(row)

    def _end_for_loop(self):
        if self._populating_for_loop():
            return True
        return self._test_or_uk.end_for_loop()

    def _populating_for_loop(self):
        return isinstance(self._populator, ForLoopPopulator)

    def _continues(self, row):
        return (row.is_continuing() and self._populator or
                self._populating_for_loop() and row.is_indented())

    def _populate_comment_row(self, crow):
        # print("DEBUG: _populate_comment_row ENTER %s" % crow)
        populator = StepPopulator(self._test_or_uk.add_step)
        populator.add(crow)
        populator.populate()

    def populate(self):
        self._populator.populate()
        # self._comment_cache.consume_with(self._populate_comment_row)

    def _get_populator(self, row):
        is_setting = row.starts_test_or_user_keyword_setting()
        if is_setting or self._documentation_setting:
            setter = None
            if row.head == '...' and self._documentation_setting:
                setter = self._test_or_uk.get_setter('Documentation')
            else:
                self._documentation_setting = False
            if not is_setting and not self._documentation_setting:
                return StepPopulator(self._test_or_uk.add_step)
            if is_setting and not self._documentation_setting:
                setter = self._setting_setter(row)
            if is_setting and not setter:
                self._documentation_setting = False
                return NullPopulator()
            if isinstance(setter.__self__, Documentation):
                self._documentation_setting = True
                return DocumentationPopulator(setter)
            self._documentation_setting = False
            return SettingPopulator(setter)
        self._documentation_setting = False
        return StepPopulator(self._test_or_uk.add_step)

    def _setting_setter(self, row):
        setting_name = row.test_or_user_keyword_setting_name()
        return self._test_or_uk.get_setter(setting_name)


class TestCasePopulator(_TestCaseUserKeywordPopulator):
    _item_type = 'test case'


class UserKeywordPopulator(_TestCaseUserKeywordPopulator):
    _item_type = 'keyword'


class _PropertyPopulator(Populator):

    def __init__(self, setter):
        self._setter = setter
        self._value = []
        self._comments = Comments()
        self._data_added = False

    def add(self, row):
        if not row.is_commented():
            self._add(row)
        self._comments.add(row)

    def _add(self, row):
        if row.cells == ['...']:
            self._deprecate_continuation_without_values()
        self._value.extend(row.tail if not self._data_added else row.data)
        self._data_added = True

    def _deprecate_continuation_without_values(self):
        location = self._get_deprecation_location()
        message = ("%sIgnoring lines with only continuation marker '...' is "
                   "deprecated." % ('In %s: ' % location if location else ''))
        self._setter.__self__.report_invalid_syntax(message, level='WARN')

    def _get_deprecation_location(self):
        return ''


class VariablePopulator(_PropertyPopulator):

    def __init__(self, setter, name):
        _PropertyPopulator.__init__(self, setter)
        self._name = name

    def populate(self):
        self._setter(self._name, self._value, self._comments.value)

    def _get_deprecation_location(self):
        return "'Variables' section"


class SettingPopulator(_PropertyPopulator):

    def populate(self):
        self._setter(self._value, self._comments.value)

    def _get_deprecation_location(self):
        return "'%s' setting" % self._setter.__self__.setting_name


class DocumentationPopulator(_PropertyPopulator):
    _end_of_line_escapes = re.compile(r'(\\+)n?$')

    def populate(self):
        self._setter(self._value, self._comments.value)

    def _add(self, row):
        if row.data[0] == '...':
            row.data[0] = '\\n...'
            self._value.append(''.join(row.data))
        else:
            self._add_to_value(row.dedent().data)

    def _add_to_value(self, data):
        joiner = self._row_joiner()
        if joiner:
            self._value.append(joiner)
        self._value.append(' '.join(data))

    def _row_joiner(self):
        if self._is_empty():
            return None
        return self._joiner_based_on_eol_escapes()

    def _is_empty(self):
        return not self._value or \
               (len(self._value) == 1 and self._value[0] == '')

    def _joiner_based_on_eol_escapes(self):
        match = self._end_of_line_escapes.search(self._value[-1])
        if not match or len(match.group(1)) % 2 == 0:
            return '\\n'
        if not match.group(0).endswith('n'):
            return ' '
        return None


class MetadataPopulator(DocumentationPopulator):

    def __init__(self, setter):
        _PropertyPopulator.__init__(self, setter)
        self._name = None

    def populate(self):
        self._setter(self._name, self._value, self._comments.value)

    def _add(self, row):
        data = row.dedent().data
        if self._name is None:
            self._name = data[0] if data else ''
            data = data[1:]
        self._add_to_value(data)


class StepPopulator(_PropertyPopulator):

    def _add(self, row):
        if row.cells == ['...']:
            self._deprecate_continuation_without_values()
        self._value.extend(row.data)
        # print(f"DEBUG: tablepopulators StepPopulator _add row={row.data}")

    def populate(self):
        if self._value or self._comments.value:
            self._setter(self._value, self._comments.value)
