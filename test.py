#!/usr/bin/env python3

# https://docs.python.org/3/library/unittest.html
# assertEqual(a, b) 	a == b
# assertNotEqual(a, b) 	a != b
# assertTrue(x) 		bool(x) is True
# assertFalse(x) 		bool(x) is False
# assertIs(a, b) 		a is b
# assertIsNot(a, b) 	a is not
# assertIsNone(x) 		x is None
# assertIsNotNone(x) 	x is not None
# assertIn(a, b) 		a in b
# assertNotIn(a, b) 			a not in b
# assertIsInstance(a, b) 		isinstance(a, b)
# assertNotIsInstance(a, b) 	not isinstance(a, b)

import unittest, json, codecs, os, logging
import parse, blame
from models import LineChange

TEST_DATA_DIR_NAME = 'test_data'

class MarvinTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(MarvinTest, self).__init__(*args, **kwargs)
		self.test_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), TEST_DATA_DIR_NAME)

	def full_test_path(self, file):
		return os.path.join(self.test_data_dir, file)

	def setup_parser(self, file):
		file_path = self.full_test_path(file)
		parser = parse.DiffParser(file_path)
		return parser

	def assertLength(self, lst, length):
		self.assertEqual(len(lst), length)


class TestLineChangeEquality(unittest.TestCase):
	def test_custom_eq(self):
		self.assertEqual(LineChange(), LineChange())

	def test_custom_ne(self):
		self.assertNotEqual(LineChange(), LineChange(line_number='1'))

class TestReturnType(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('modify.diff').parse()

	def test_collection(self):
		self.assertIsInstance(self.file_changes, list)

	def test_linechange(self):
		self.assertIsInstance(self.file_changes[0], LineChange)

class TestLineChangeRenameFile(MarvinTest):
	def setUp(self):
		self.parser = self.setup_parser('rename.diff')
		self.parser.parse()

	def test_rename(self):
		# rename.diff renames 'sample.patch' to 'sample.diff'
		for line, added in self.parser.changes['sample.diff'][0].items():
			self.assertIn(line, self.parser.changes['sample.patch'][1])

class TestLineChangeBlocks(MarvinTest):
	def setUp(self):
		self.parser = self.setup_parser('modify.diff')
		self.parser.parse()

	def test_interesting_lines_count(self):
		# This should be 2
		self.assertLength(self.parser.interesting['Gemfile'], 4)

	def test_skip_not_interesting_lines(self):
		self.assertNotIn(39, self.parser.interesting['Gemfile'])
		self.assertNotIn(42, self.parser.interesting['Gemfile'])

class TestDiffModifiedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('modify.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 1)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_change(self):
		change = self.file_changes[0]
		self.assertEqual(change.line_number, 40)
		self.assertEqual(change.commit_sha, "d486669")
		self.assertEqual(change.change_type, LineChange.ChangeType.modified)

class TestDiffAppendedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('append.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 1)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_change(self):
		change = self.file_changes[0]
		self.assertEqual(change.line_number, 117)
		self.assertEqual(change.commit_sha, "77e39d5")
		self.assertEqual(change.change_type, LineChange.ChangeType.added)

class TestDiffMultipleAppendedLines(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('multiple_appends.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 9 + 13)

	def test_file_paths(self):
		file_paths = [change.file_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile']*9 + ['README.md']*13, file_paths)

	def test_change_file1(self):
		file1_changes = [c for c in self.file_changes if c.file_path == 'Gemfile']
		for change in file1_changes:
			# lines 117 to 125 appended
			self.assertIn(change.line_number, range(117, 125+1))
			self.assertEqual(change.change_type, LineChange.ChangeType.added)

	def test_change_file2(self):
		file1_changes = [c for c in self.file_changes if c.file_path == 'README.md']
		for change in file1_changes:
			# lines 115 to 127 appended
			self.assertIn(change.line_number, range(115, 127+1))
			self.assertEqual(change.change_type, LineChange.ChangeType.added)

class TestDiffPrependedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('prepend.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 1)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_changes(self):
		change = self.file_changes[0]
		self.assertEqual(change.line_number, 1)
		self.assertEqual(change.commit_sha, "de30360")
		self.assertEqual(change.change_type, LineChange.ChangeType.added)

class TestDiffDeletedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('delete.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 1)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_changes(self):
		change = self.file_changes[0]
		self.assertEqual(change.line_number, 37)
		self.assertEqual(change.change_type, LineChange.ChangeType.deleted)

	def test_old_sha(self):
		# In case of a deletion the old commit is of interest
		change = self.file_changes[0]
		self.assertEqual(change.commit_sha, "647ad8d")

class TestDiffDeleteMoreThanAdded(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('delete_more.diff').parse()

	def test_overall_amount(self):
		self.assertLength(self.file_changes, 4)

	def test_amount_deletions(self):
		deletions = [lc for lc in self.file_changes if lc.change_type == LineChange.ChangeType.deleted]
		self.assertLength(deletions, len(self.file_changes) - 1)

	def test_amount_modifications(self):
		modifications = [lc for lc in self.file_changes if lc.change_type == LineChange.ChangeType.modified]
		self.assertLength(modifications, 1)

class TestDiffMultipleEdits(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('multiple_edits.diff').parse()
		self.new_sha = "484e717"
		self.file_path = "Gemfile"

	def test_amount(self):
		# One line prepended, one line edited, two lines appended
		self.assertLength(self.file_changes, 4)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_prepend(self):
		# First line prepended
		actual = LineChange(line_number=1, commit_sha=self.new_sha,
			file_path=self.file_path, change_type=LineChange.ChangeType.added)
		self.assertIn(actual, self.file_changes)

	def test_modify(self):
		#line 58 (now 59) modified
		actual = LineChange(line_number=59, commit_sha=self.new_sha,
			file_path=self.file_path, change_type=LineChange.ChangeType.modified)
		self.assertIn(actual, self.file_changes)

	def test_append(self):
		#lines 118, 119 appended.
		actual = [	LineChange(line_number=118, commit_sha=self.new_sha,
						file_path=self.file_path, change_type=LineChange.ChangeType.added),
					LineChange(line_number=119, commit_sha=self.new_sha,
						file_path=self.file_path, change_type=LineChange.ChangeType.added)]
		for lc in actual:
			self.assertIn(lc, self.file_changes)

class TestDiffMultipleFiles(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('multiple_files.diff').parse()

	def test_amount(self):
		self.assertLength(self.file_changes, 5)

	def test_file_paths(self):
		file_paths = [change.file_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile']*3 + ['README.md']*2, file_paths)

	def test_changes_file1(self):
		file = "Gemfile"
		new_sha = "37c323f"
		single_file_changes = [c for c in self.file_changes if c.file_path == file]
		# line 1 prepended, line 37 (now 38) and line 40 (now 41) modified
		expected = [LineChange(line_number=1, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.added),
					LineChange(line_number=38, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.modified),
					LineChange(line_number=41, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.modified)]
		for e in expected:
			self.assertIn(e, single_file_changes)

	def test_changes_file2(self):
		file = "README.md"
		new_sha = "9add005"
		single_file_changes = [c for c in self.file_changes if c.file_path == file]
		# Inserted lines 25 and 26
		expected = [LineChange(line_number=25, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.added),
					LineChange(line_number=26, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.added)]
		for e in expected:
			self.assertIn(e, single_file_changes)

class TestDiffLarge(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('pr_338.diff').parse()

	def test_amount(self):
		self.assertTrue(len(self.file_changes) > 30)

	def test_selected_changes(self):
		file = "app/views/time_sheets/edit.html.erb"
		new_sha = "9b41892"
		single_file_changes = [c for c in self.file_changes if c.file_path == file]
		# Deleted line 5, line 6-13 added
		expected = [LineChange(line_number=5, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.modified),
					LineChange(line_number=12, commit_sha=new_sha,
						file_path=file, change_type=LineChange.ChangeType.added)]
		for e in expected:
			self.assertIn(e, single_file_changes)

class TestBlame(MarvinTest):
	def setUp(self):
		self.line_count = 116
		html_path = self.full_test_path('test_blame.html')
		self.blamer = blame.BlameParser(project_link='')
		self.blamer.load_html_file(html_path)

	def test_count_blames(self):
		data = self.blamer.blame_data
		self.assertIsNotNone(data)
		# 116 lines in the file
		self.assertLength(data, self.line_count)

	def test_blame_first_line(self):
		blame_info = self.blamer.blame_line(1)
		self.assertEqual(blame_info.user_name, 'jaSunny')
		self.assertEqual(blame_info.commit_message, 'adding rails 4.2.4 app')
		self.assertEqual(blame_info.short_sha, '867c8f8')
		self.assertIn(blame_info.short_sha, blame_info.commit_url)

	def test_blame_multiple_line_commit(self):
		blame_info = self.blamer.blame_line(42)
		self.assertEqual(blame_info.user_name, 'WGierke')
		self.assertEqual(blame_info.commit_message, 'code refactoring of dev branch')

	def test_blame_last_line(self):
		blame_info = self.blamer.blame_line(self.line_count)
		self.assertEqual(blame_info.user_name, 'jaSunny')
		message = 'adding newrelic, errbit supprt; improving views and validation'
		self.assertEqual(blame_info.commit_message, message)

	def test_blame_nonexistent_line(self):
		logging.disable(logging.CRITICAL)
		blame_info_before = self.blamer.blame_line(0)
		self.assertIsNone(blame_info_before)
		blame_info_after = self.blamer.blame_line(self.line_count + 1)
		self.assertIsNone(blame_info_after)
		logging.disable(logging.NOTSET)


if __name__ == '__main__':
	unittest.main()
