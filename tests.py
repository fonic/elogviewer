from elogviewer import Elog
import unittest
from glob import glob
from os import path


class TestElog(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        datadir = "./data"
        self.elogs = glob(path.join(datadir, "*.log"))
        self.htmls = [".".join((path.splitext(elog)[0], "html"))
                      for elog in self.elogs]
        for elog, html in zip(self.elogs, self.htmls):
            if not path.isfile(html):
                with open(html, "w") as html_file:
                    html_file.writelines(Elog(elog).htmltext)

    def test_html_parser(self):
        for elog, html in zip(self.elogs, self.htmls):
            with open(html, "r") as html_file:
                self.assertMultiLineEqual(
                    Elog(elog).htmltext,
                    "".join(html_file.readlines()))

    def test_unsupported_format(self):
        with Elog(self.htmls[0]).file as elogfile:
            content = elogfile.readlines()
        self.assertNotEqual(content, [])
        self.assertIsInstance(b"".join(content), bytes)


if __name__ == "__main__":
    unittest.main()
