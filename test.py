#!/usr/bin/env python3

import unittest, json, codecs, os
import parse
from models import LineChange

TEST_DATA_DIR_NAME = 'test_data'

class MarvinTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(MarvinTest, self).__init__(*args, **kwargs)
		self.test_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), TEST_DATA_DIR_NAME)

	def read(self, file):
		file_path = os.path.join(self.test_data_dir, file)
		return parse.load_file(file_path)

	def assertKeyValueInDictList(self, item, lst):
		def key_in_list(key, lst):
			return any([key in e for e in lst])

		def key_value_in_list(key, value, lst):
			return any([e.get(key, None) == value for e in lst])

		key, value = item
		self.assertTrue(key_in_list(key, lst), msg="The key was not found.")
		self.assertTrue(key_value_in_list(key, value, lst), msg="The key did not have the expected value.")

class TestMarvinTest(MarvinTest):
	def test_key_value_in_dict(self):
		self.assertKeyValueInDictList(('b',2), [{'a':1,'b':2}])

class TestLineChageEquality(unittest.TestCase):
	def test_custom_eq(self):
		self.assertEqual(LineChange(), LineChange())

	def test_custom_ne(self):
		self.assertNotEqual(LineChange(), LineChange(line_number='1'))


class TestReturnType(MarvinTest):
	def setUp(self):
		self.file_changes = parse.parse_lines(self.read('modify.diff'))

	def test_collection(self):
		self.assertIsInstance(self.file_changes, list)

	def test_linechange(self):
		self.assertIsInstance(self.file_changes[0], LineChange)

class TestDiffModifiedLine(MarvinTest):
	def setUp(self):
		self.file_changes = parse.parse_lines(self.read('modify.diff'))

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
		self.file_changes = parse.parse_lines(self.read('append.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_file_path(self):
		change = self.file_changes[0]
		self.assertEqual(change.file_path, 'Gemfile')

	def test_change(self):
		change = self.file_changes[0]
		self.assertEqual(change.line_number, 117)
		self.assertEqual(change.commit_sha, "647ad8d")
		self.assertEqual(change.change_type, LineChange.ChangeType.added)

class TestDiffMultipleAppendedLines(MarvinTest):
	def setUp(self):
		self.file_changes = parse.parse_lines(self.read('multiple_appends.diff'))

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
		self.file_changes = parse.parse_lines(self.read('prepend.diff'))

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
		self.file_changes = parse.parse_lines(self.read('delete.diff'))

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

class TestDiffMultipleEdits(MarvinTest):
	def setUp(self):
		self.file_changes = parse.parse_lines(self.read('multiple_edits.diff'))
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
		self.file_changes = parse.parse_lines(self.read('multiple_files.diff'))

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
		self.file_changes = parse.parse_lines(self.read('pr_338.diff'))

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