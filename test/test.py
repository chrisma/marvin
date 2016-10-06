import unittest, json, codecs, os
from collections import namedtuple
from marvin import Marvin

header = namedtuple('header', ['index_path', 'old_path', 'old_version', 'new_path', 'new_version'])

repo_storage_dir = '../repos'

class MarvinTest(unittest.TestCase):
	def __init__(self, *args, **kwargs):
		super(MarvinTest, self).__init__(*args, **kwargs)
		self.test_data_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), 'data')
		self.marvin = Marvin(repo_dir=repo_storage_dir)
		self.marvin.repo_path = os.path.join(repo_storage_dir, 'chrisma', 'wimi-portal')

	def read(self, file):
		with open(os.path.join(self.test_data_dir, file), 'rb') as f:
			return f.read()

	def assertKeyValueInDictList(self, item, lst):
		def key_in_list(key, lst):
			return any([key in e for e in lst])

		def key_value_in_list(key, value, lst):
			return any([e.get(key, None) == value for e in lst])

		key, value = item
		self.assertTrue(key_in_list(key, lst), msg="The key was not found.")
		self.assertTrue(key_value_in_list(key, value, lst), msg="The key did not have the expected value.")

class TestDiffModifiedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('modify.diff'))
		self.line_number = 40

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [	{'start': self.line_number, 'type': 'insert', 'end': self.line_number},
					{'start': self.line_number, 'type': 'delete', 'end': self.line_number}]
		self.assertCountEqual(actual, changes)

class TestDiffAppendedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('append.diff'))
		self.line_number = 113

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'insert'}]
		self.assertCountEqual(actual, changes)

class TestDiffMultipleAppendedLines(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_appends.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 2)

	def test_header(self):
		headers_old_paths = [change['header'].old_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_old_paths)
		headers_new_paths = [change['header'].new_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_new_paths)

	def test_change_file1(self):
		file1_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='Gemfile'].pop()
		# lines 117 to 125 appended
		file1_actual = [{'start': 117, 'end': 125, 'type': 'insert'}]
		self.assertCountEqual(file1_actual, file1_changes)

	def test_change_file2(self):
		file2_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='README.md'].pop()
		# lines 115 to 127 appended
		file2_actual = [{'start': 115, 'end': 127, 'type': 'insert'}]
		self.assertCountEqual(file2_actual, file2_changes)

class TestDiffPrependedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('prepend.diff'))
		self.line_number = 1

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'insert'}]
		self.assertCountEqual(actual, changes)

class TestDiffDeletedLine(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('delete.diff'))
		self.line_number = 37

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_changes(self):
		changes = self.file_changes[0]['changes']
		actual = [{'start': self.line_number, 'end': self.line_number, 'type': 'delete'}]
		self.assertCountEqual(actual, changes)

class TestDiffMultipleEdits(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_edits.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 1)

	def test_header(self):
		header = self.file_changes[0]['header']
		self.assertEqual(header.old_path, 'Gemfile')
		self.assertEqual(header.new_path, 'Gemfile')

	def test_prepend(self):
		changes = self.file_changes[0]['changes']
		# line 1 prepended
		self.assertIn({'start': 1, 'end': 1, 'type': 'insert'}, changes)

	def test_modify(self):
		changes = self.file_changes[0]['changes']
		#line 58 (now 59) modified
		actual = [	{'start': 58, 'end': 58, 'type': 'delete'},
					{'start': 59, 'end': 59, 'type': 'insert'}]
		for elem in actual:
			self.assertIn(elem, changes)

	def test_append(self):
		changes = self.file_changes[0]['changes']
		#lines 118, 119 appended.
		self.assertIn({'start': 118, 'end': 119, 'type': 'insert'}, changes)

class TestDiffMultipleFiles(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('multiple_files.diff'))

	def test_amount(self):
		self.assertEqual(len(self.file_changes), 2)

	def test_header(self):
		headers_old_paths = [change['header'].old_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_old_paths)
		headers_new_paths = [change['header'].new_path for change in self.file_changes]
		self.assertCountEqual(['Gemfile', 'README.md'], headers_new_paths)

	def test_changes_file1(self):
		file1_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='Gemfile'].pop()
		# line 1 prepended, line 37 (now 38) and line 40 (now 41) modified
		file1_actual = [{'start': 1, 'end': 1, 'type': 'insert'},
					{'start': 37, 'end': 37, 'type': 'delete'},
					{'start': 38, 'end': 38, 'type': 'insert'},
					{'start': 40, 'end': 40, 'type': 'delete'},
					{'start': 41, 'end': 41, 'type': 'insert'}]
		self.assertCountEqual(file1_actual, file1_changes)

	def test_changes_file2(self):
		file2_changes = [c['changes'] for c in self.file_changes if c['header'].new_path=='README.md'].pop()
		# Inserted lines 25 and 26
		file2_actual = [{'start': 25, 'end': 26, 'type': 'insert'}]
		self.assertCountEqual(file2_actual, file2_changes)

class TestDiffLarge(MarvinTest):
	def setUp(self):
		self.file_changes = self.marvin.analyze_diff(self.read('pr_338.diff'))

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

class TestTest(MarvinTest):
	def test_key_value_in_dict(self):
		self.assertKeyValueInDictList(('a',2), [{'a':1,'b':2}])

if __name__ == '__main__':
	unittest.main()