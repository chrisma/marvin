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


class TestLineChangeEquality(unittest.TestCase):
	def test_custom_eq(self):
		self.assertEqual(LineChange(), LineChange())

	def test_custom_ne(self):
		self.assertNotEqual(LineChange(), LineChange(line_number='1'))

class TestLineChangeRenameFile(MarvinTest):
	def setUp(self):
		self.parser = self.setup_parser('rename.diff')
		self.parser.parse()

	def test_rename(self):
		for line, added in self.parser.changes['sample.diff'][0].items():
			self.assertTrue(line in self.parser.changes['sample.patch'][1])

class TestLineChangeBlocks(MarvinTest):
	def setUp(self):
		self.parser = self.setup_parser('modify.diff')
		self.parser.parse()

	def test_interesting_lines_count(self):
		self.assertEqual(len(self.parser.interesting['Gemfile']), 4)

	def test_skip_not_interesting_lines(self):
		self.assertTrue(39 not in self.parser.interesting['Gemfile'])
		self.assertTrue(42 not in self.parser.interesting['Gemfile'])

class TestReturnType(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('modify.diff').parse()

	def test_collection(self):
		self.assertIsInstance(self.file_changes, list)

	def test_linechange(self):
		self.assertIsInstance(self.file_changes[0], LineChange)

class TestDiffModifiedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('modify.diff').parse()

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

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
		self.assertEqual(len(self.file_changes), 1)

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
		self.assertEqual(len(self.file_changes), 9 + 13)

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
		self.assertEqual(len(self.file_changes), 1)

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
		self.assertEqual(len(self.file_changes), 1)

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

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 4)

	def test_change_type(self):
		count = {LineChange.ChangeType.deleted: 0, LineChange.ChangeType.modified: 0}

		for i in range(len(self.file_changes)):
			count[self.file_changes[i].change_type]	+= 1

		self.assertEqual(count[LineChange.ChangeType.deleted], len(self.file_changes) - 1)
		self.assertEqual(count[LineChange.ChangeType.modified], 1)

class TestDiffMultipleEdits(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('multiple_edits.diff').parse()
		self.new_sha = "484e717"
		self.file_path = "Gemfile"

	def test_amount(self):
                # One line prepended, one line edited, two lines appended
                self.assertEqual(len(self.file_changes), 4)

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
		self.assertEqual(len(self.file_changes), 5)

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

@unittest.skip("Not refactored yet")
class TestDiffLarge(MarvinTest):
	def setUp(self):
		self.file_changes = self.setup_parser('pr_338.diff').parse()

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 15)

	def test_selected_changes(self):
		changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='app/controllers/work_days_controller.rb'].pop()
		actual = [
			{'end': 16, 'start': 11, 'type': 'delete'},
			{'end': 24, 'start': 11, 'type': 'insert'},
			{'end': 20, 'start': 19, 'type': 'delete'},
			{'end': 27, 'start': 27, 'type': 'insert'},
			{'end': 32, 'start': 32, 'type': 'insert'},
			{'end': 37, 'start': 37, 'type': 'insert'},
			{'end': 59, 'start': 59, 'type': 'delete'},
			{'end': 68, 'start': 68, 'type': 'insert'},
			{'end': 76, 'start': 73, 'type': 'delete'},
			{'end': 78, 'start': 78, 'type': 'delete'},
			{'end': 83, 'start': 83, 'type': 'insert'}
		]
		self.assertCountEqual(actual, changes)

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
		self.assertEqual(len(data), self.line_count)

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

@unittest.skip("Not refactored yet")
class TestBlameInsert(MarvinTest):
	def setUp(self):
		self.line = 10
		file_changes = [
			{'changes': [{'end': self.line, 'start': self.line, 'type': 'insert'}],
			'header': header(index_path=None, old_path='Gemfile',
				old_version='647ad8d', new_path='Gemfile', new_version='de30360')}]
		self.file_blames = self.marvin.blame_changes(file_changes)

	def test_file(self):
		self.assertEqual(len(self.file_blames), 1)
		self.assertIn('Gemfile', self.file_blames)

	def test_blame(self):
		blame = self.file_blames.popitem()[1]
		actual = [{'type': 'insert',
				'author': 'jaSunny',
				'timestamp': '1444140126',
				'commit': '867c8f83d432a5c8d7236735e513a3bd0b12bb38',
				'lines': {self.line-1, self.line+1}}]
		self.assertEqual(actual, blame)

@unittest.skip("Not refactored yet")
class TestBlameMultipleInserts(MarvinTest):
	def setUp(self):
		file_changes = [{'changes': [
			{'end': 24, 'start': 11, 'type': 'insert'},
			{'end': 27, 'start': 27, 'type': 'insert'},
			{'end': 32, 'start': 32, 'type': 'insert'},
			{'end': 37, 'start': 37, 'type': 'insert'},
			{'end': 68, 'start': 68, 'type': 'insert'},
			{'end': 83, 'start': 83, 'type': 'insert'}],
		'header': header(
			index_path=None,
			old_path='app/controllers/work_days_controller.rb',
			old_version='6ace82e',
			new_path='app/controllers/work_days_controller.rb',
			new_version='70629c2')}]
		self.file_blames = self.marvin.blame_changes(file_changes)

	def test_blame(self):
		actual = [	{'commit': '8342fefcf6d5e8cb4d834a95576b4237768fcd80', 'author': 'Moritz Eissenhauer', 'timestamp': '1447859591', 'type': 'insert', 'lines': {33, 36, 69, 38, 10, 31}},
					{'commit': '0c82d240f32026caf6c6238d1d7204e7766f723a', 'author': 'Jonas Bounama', 'timestamp': '1452693891', 'type': 'insert', 'lines': {25}},
					{'commit': 'b21818bd1be06f959c5fb9916112c6889ab8f9fc', 'author': 'Lennard Wolf', 'timestamp': '1448723686', 'type': 'insert', 'lines': {26, 28}},
					{'commit': '2b573f4afeac83a59b741483fc067839d952bd5c', 'author': 'Moritz Eissenhauer', 'timestamp': '1449840415', 'type': 'insert', 'lines': {67}},
					{'commit': '04fe0c5b7a3cbad49c6847e302591a1b7c6dc8d9', 'author': 'Soeren Tietboehl', 'timestamp': '1454418775', 'type': 'insert', 'lines': {82, 84}}]
		# import pdb; pdb.set_trace()
		print([y for x,y in self.file_blames.items()][0])
		for file, blame_list in self.file_blames.items():
			for blame in blame_list:
				self.assertIn(blame, actual)


if __name__ == '__main__':
	unittest.main()
