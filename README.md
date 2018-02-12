# marvin

## Setup
* A [venv](https://docs.python.org/3/library/venv.html) virtual Python environment is recommended.
* Ensure libxml2 development packages are installed `sudo apt install libxml2-dev libxmlsec1-dev`
* Install Python dependencies using `pip3 install -r requirements.txt`

## Run tests
Python's [unittest](https://docs.python.org/3/library/unittest.html) is being used.
* Run all tests using `python3 -m unittest test`
* Run selected tests by stating the test class name `python3 -m unittest test.TestDiffDeletedLine`
