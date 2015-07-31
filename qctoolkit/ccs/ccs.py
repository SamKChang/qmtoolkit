from qctoolkit import *
#from geometry import *
#from utilities import *
import re, copy, sys
from compiler.ast import flatten

class MoleculeSpan(object):
  def __init__(self, xyz_file, parameter_file):
    self.structure = Molecule()
    self.structure.read_xyz(xyz_file)
    # mutation related variables
    self.mutation_list = []
    self.mutation_target = []
    # stretching related variables
    self.stretching_list = []
    self.stretching_direction = []
    self.stretching_range = []
    # rotation related variables
    self.rotation_list = []
    self.rotation_center = []
    self.rotation_axis = []
    self.rotation_range = []
    # replacing realted variables
    # not yet implemented

    # setup all parameters
    self.read_param(parameter_file)
    self.coor = flatten([
                 ['m' for _ in flatten(self.mutation_list)],
                 ['s' for _ in flatten(self.stretching_list)],
                 ['r' for _ in flatten(self.rotation_list)],
                ])

    MList = self.mutation_list
    _flatten = [item for sublist in MList for item in sublist]
    vlen = np.vectorize(len)
    try:
      lenList = vlen(MList)
    except TypeError:
      lenList = [len(MList[0]) for i in range(len(MList))]
    print "===== CCS REPORT ====="
    report("generating molecule", xyz_file)
    report("ccs parameter file", parameter_file)
    report("mutation indices", self.mutation_list)
    report("target atomic numbers", self.mutation_target)
    report("length of mutation vector",
           len(_flatten), "<=>", lenList)
    print ""
    report("stretching indices", self.stretching_list)
    report("stretching range", self.stretching_range)
    report("stretching direction indices",
           self.stretching_direction)
    print ""
    report("rotation indices", self.rotation_list)
    report("rotation center", self.rotation_center)
    report("rotation axis", self.rotation_axis)
    report("rotation range", self.rotation_range)
    print ""
    status("ccs coordinate", self.coor)
    print "========= END ========\n"

  def read_param(self, parameter_file):
    param = open(parameter_file, 'r')

    mutation_flag = re.compile(".*mutation_list:.*")
    stretching_flag = re.compile(".*stretching_list:.*")
    direction_flag = re.compile(".*direction_index:.*")
    rotation_flag = re.compile(".*rotation_list:.*")
    center_flag = re.compile(".*center_index:.*")
    end_flag = re.compile(".*end.*")

    while True:
      line = param.readline()
      if not line: break
      line = re.sub(re.compile("#.*"),'', line)
      if re.match(mutation_flag, line.lower()):
        while not re.match(end_flag, line):
          line = param.readline().rstrip()
          line = re.sub(re.compile("#.*"),'', line)
          try:
            mlist_str =  re.sub(re.compile("->.*"), "", line)\
                         .split(",")
            tlist_str =  re.sub(re.compile(".*->"), "", line)\
                         .split(",")
            mlist = []
            tlist = []
            for m in mlist_str:
              if re.match(re.compile(".*:.*"), m):
                rangeList = map(int, m.split(":"))
                mmin = rangeList[0]
                mmax = rangeList[1] + 1
                mlist.extend(range(mmin,mmax))
              else:
                mlist.append(int(m))
            for t in tlist_str:
              if re.match(re.compile(".*:.*"), t):
                rangeList = map(int, t.split(":"))
                tmin = rangeList[0]
                tmax = rangeList[1] + 1
                tlist.extend(range(tmin,tmax))
              else:
                tlist.append(int(t))
            self.mutation_list.append(mlist)
            self.mutation_target.append(tlist)
          except ValueError:
            pass
        MList = self.mutation_list
        _flatten = [item for sublist in MList for item in sublist]
        vlen = np.vectorize(len)
        # wired numpy.int32 bug for equal length sublist
        try:
          lenList = vlen(MList)
        except TypeError:
          lenList = [len(MList[0]) for i in range(len(MList))]
      elif re.match(stretching_flag, line.lower()):
        while not re.match(end_flag, line):
          line = param.readline().rstrip()
          line = re.sub(re.compile("#.*"),'', line)
          if re.match(direction_flag, line):
            dlist = map(int, re.sub(re.compile(".*:"),
                                    "", line).split(","))
            self.stretching_direction.append(dlist)
            line = param.readline().rstrip()
            line = re.sub(re.compile("#.*"),'', line)
            try:
              slist = map(int, re.sub(re.compile("->.*"),\
                                      "", line).split(","))
              self.stretching_list.append(slist)
              rlist = map(float, re.sub(re.compile(".*->"),\
                                        "", line).split(':'))
              self.stretching_range.append(rlist)
            except ValueError:
              pass

      elif re.match(rotation_flag, line.lower()):
        while not re.match(end_flag, line):
          line = param.readline()
          line = re.sub(re.compile("#.*"),'', line)
          if re.match(center_flag, line):
            center = int(re.sub(re.compile(".*:"),
                                "", line))
            self.rotation_center.append(center)
            line = param.readline().rstrip()
            line = re.sub(re.compile("#.*"),'', line)
            axis = map(int, re.sub(re.compile(".*:"),
                                   "", line).split(","))
            self.rotation_axis.append(axis)
            line = param.readline().rstrip()
            line = re.sub(re.compile("#.*"),'', line)
            try:
              rolist = map(int, re.sub(re.compile("->.*"),\
                                       "", line).split(","))
              self.rotation_list.append(rolist)
              rglist = map(float, re.sub(re.compile(".*->"),\
                                         "", line).split(':'))
              self.rotation_range.append(rglist)
            except ValueError:
              pass
    param.close()

  # !!TODO!!
  # interface between mutation and other operations is necessary!
  def generate(self, **kwargs):
    self.new_structure = copy.deepcopy(self.structure)
    if 'mutation' in kwargs:
      self._mutate(kwargs['mutation'])
    if 'stretching' in kwargs:
      self._stretch(kwargs['stretching'])
    if 'rotation' in kwargs:
      self._rotate(kwargs['rotatting'])
    return self.new_structure

  def _mutate(self, mutation):
    for m in xrange(len(mutation)):
      for i in xrange(len(mutation[m])):
        index = self.mutation_list[m][i] - 1
        #target = self.mutation_target[m][mutation[m][i]]
        target = mutation[m][i]
        self.new_structure.Z[index] = target
  def _stretch(self, stretching):
    print stretching
  def _rotate(self, rotation):
    print rotation