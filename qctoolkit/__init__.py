from molecule import *
from QM.qmInterface import *
from QM.qmjob import *
from alchemy.aljob import *
from alchemy.alpath import *
from QM.pseudo.pseudo import *
from analysis import *
from utilities import *
from setting import *
from ccs.ccs import CCS

import MD
import ML
import ccs
import QM
import optimization
import alchemy
import setting

import os

# check for qtk setting
missing_files = []
paths = os.environ["PATH"].split(":")
code_pattern = re.compile('cpmd|bigdft|vasp|nwchem')
exe_pattern = re.compile('.*exe')
url_pattern = re.compile('.*url')
for dep in dir(setting):
  if code_pattern.match(dep) and not url_pattern.match(dep):
    not_found = True
    file_str = getattr(setting, dep)
    if exe_pattern.match(dep):
       itr = 0
       while not_found and itr < len(paths):
         path = paths[itr]
         test_path = os.path.join(path, file_str)
         itr = itr +1
         if os.access(test_path, os.X_OK):
           not_found = False
    else:
      if os.access(file_str, os.F_OK):
        not_found = False
    if not_found:
      missing_files.append(file_str)

if missing_files:
  for missing_file in missing_files:
    qtk.warning("missing file: %s" % missing_file)
  qtk.warning(
               'please modify /path/to/qctoolkit/setting/py ' +\
               'and recompile.'
             )
