import qctoolkit as qtk
import re, sys, os, copy, shutil
import numpy as np
from qctoolkit import utilities as ut

def qmDir_inplace(inp, **kwargs):
  qps = qtk.pathStrip
  _prefix = ''
  if 'prefix' in kwargs:
    _prefix = kwargs['prefix']
    del kwargs['prefix']
  _suffix = ''
  if 'suffix' in kwargs:
    _suffix = kwargs['suffix']
    del kwargs['suffix']
  try:
    root = re.match(re.compile('(.*/)[^\/]*'),inp).group(1)+'/'
  except:
    root = './'

  inproot = re.sub('\.inp', '',re.sub('.*/', '', inp))
  psinp = _prefix + inproot + _suffix
  inpdir = root
  inpname = inpdir + psinp + ".inp"
  new_run = True
  if os.path.exists(inpdir+psinp+'.out'):
    qtk.warning("io_format.cpmd.qmDir_inplace: output file "+\
                qps(inpdir+psinp)+\
                '.out exist, nothing to be done')
    new_run = False

  return qps(inpdir), qps(inpname), qps(psinp), new_run, kwargs

def qmDir(inp, **kwargs):
  """
  an root/inp folder contains all inp files
  inp files in root/inp/foo.inp
  will be copied to root/inp/foo/foo.inp
  scratch files will be generated and cleaned at root/inp/fc
  """

  qps = qtk.pathStrip
  _prefix = ''
  if 'prefix' in kwargs:
    _prefix = kwargs['prefix']
    del kwargs['prefix']
  _suffix = ''
  if 'suffix' in kwargs:
    _suffix = kwargs['suffix']
    del kwargs['suffix']
  _inplace = False
  if 'outdir' in kwargs:
    outdir = re.sub('\/$','', kwargs['outdir']) + '/'
    del kwargs['outdir']
  else:
    outdir = './'
  try:
    root = re.match(re.compile('(.*/)[^\/]*'),inp).group(1)\
           + outdir
  except:
    root = './' + outdir

  inproot = re.sub('\.inp', '',re.sub('.*/', '', inp))
  psinp = _prefix + inproot + _suffix
  inpdir = root + psinp
  inpname = inpdir + "/" + psinp + ".inp"
  new_run = True
  if not os.path.exists(inpdir):
    os.makedirs(inpdir)
    shutil.copyfile(inp, inpname) # copy inp file to folder
  elif _inplace:
    shutil.copyfile(inp, inpname)
  else:
    qtk.warning("io_format.cpmd.qmDir: folder '" + inpdir +\
               "' exists, nothing to be done")
    new_run = False
  return qps(inpdir), qps(inpname), qps(psinp), new_run, kwargs

class Setting(object): 
  def __init__(self): 
    """
    input setup should be manipulated here 
    to provide general interface for other program
    seperate setting is for flexibility of switching
    different input struture
    """
 
    # default settings
    self.theory = "PBE" 
    self.mode = "single_point" 
    self.maxstep = 1000 
    self.save_density = False 
 
    self.charge = 'auto'
    self.multiplicity = 'auto'
    self.cutoff = 100 
    self.margin = 5 
    self.center = np.array([0,0,0]) 
    self.celldm = [20,20,20,0,0,0] 
    self.unit = "Angstrom" 
    self.symmetry = "isolated" 
    self.mesh = 0 
    self.kmesh = [1,1,1] 
    self.ks_states = 0 
    self.convergence = 1.0E-5
    self.scale = [1,1,1]
    self.shift = np.array([0,0,0])

    self.set_multiplicity = False
    self.set_charge = False
    self.set_center = False
    self.set_celldm = False
    self.set_margin = False
    self.set_mode = False
    self.set_step = False
    self.set_init_random = False
    self.set_scale = False
    self.set_convergence = False
    self.debug = False
    self.restart = False
    self.kpoints = False
    self.isolated = True
    self.set_shift = False

# put to setting? #
  def q_symmetry(self):
    a = self.celldm[3]
    b = self.celldm[4]
    c = self.celldm[5]
    if self.isolated:
      self.symmetry = 'isolated'
      return '  ISOLATED'
    elif a==0 and b==0 and c==0:
      self.symmetry = 'orthorhombic'
      return '  ORTHORHOMBIC'
    elif a+b+c==0.5 and (a*b==0 or b*c==0 or c*a==0):
      self.symmetry = 'triclinic'
      return '  TRICLINIC'

class inp(object):
  def __init__(self, structure_inp, info, **kwargs):
    self.setting = Setting()
    self.atom_list = {}
    self.structure = qtk.geometry.Molecule()
    if type(structure_inp) == str:
      self.structure.read(structure_inp, **kwargs)
    else:
      self.structure = copy.deepcopy(structure_inp)
    if self.structure.scale:
      self.setting.scale = self.structure.scale
      self.setting.set_scale = True
      self.setting.isolated = False
    if self.structure.celldm:
      self.setting.celldm = self.structure.celldm
      self.setting.set_celldm = True
      self.setting.isolated = False
    self.info = info

  def load_structure(self, new_structure, **kwargs):
    self.structure.read(new_structure, **kwargs)
    if self.setting.set_multiplicity:
      _multiplicity = self.setting.multiplicity
    else:
      _multiplicity = 'auto'
    if self.setting.set_charge:
      _charge = self.setting.charge
    else:
      _charge = 'auto'

    print self.setting.set_multiplicity
    print _charge, _multiplicity
    self.structure.setChargeMultiplicity(_charge,
                                         _multiplicity,
                                         **kwargs)
   
  # set atom pseudopotential string
  def PPString(self, atom_type, **kwargs):
    if 'ext' in kwargs:
      ext = kwargs['ext']
    else:
      ext = '.psp'
    if atom_type.title() in kwargs:
      return atom_type.title() + kwargs[atom_type.title()]
    else:
      return atom_type.title() + "_q" + str(qtk.n2ve(atom_type))\
             + "_" + self.setting.theory.lower() + ext
    


  # CPMD input format
  def write(self, *args, **kwargs):
    new_structure = copy.deepcopy(self.structure)
    if len(args) == 1:
      name = args[0]
    else: name = ''

    if 'no_warning' in kwargs and kwargs['no_warning']:
      no_warning = True
    else: no_warning = False
    if os.path.exists(name) and not no_warning:
      qtk.prompt(name + " exist, overwrite?")
    inp = sys.stdout if not name else open(name,"w")

    #isolated = False
    #if re.match("ISOLATED", self.setting.symmetry.upper()):
    #  self.setting.isolated = True
  
    angstrom = False
    if re.match("ANGSTROM", self.setting.unit.upper()):
      angstrom = True
  
    print >>inp, "&INFO"
    print >>inp, " qmInfo:%s" % self.info
    print >>inp, "&END"
    print >>inp, ""
    print >>inp, "&CPMD"

    if self.setting.debug:
      print >>inp, " BENCHMARK"
      print >>inp, "  1 0 0 0 0 0 0 0 0 0 "

    if self.setting.set_init_random:
      print >>inp, " INITIALIZE WAVEFUNCTION RANDOM"

    if not self.setting.set_mode:
      print >>inp, " OPTIMIZE WAVEFUNCTION"
    elif re.match("GEOPT", self.setting.mode.upper()):
      print >>inp, " OPTIMIZE GEOMETRY"
    elif re.match("KSEG", self.setting.mode.upper()):
      print >>inp, " KOHN-SHEM ENERGIES"
      print >>inp, "  " + str(self.setting.ks_states)
      self.restart = True
    else:
      sys.exit("ERROR from io_format/cpmd.py->inp.write: " +\
               "mode '" + self.setting.mode +\
               "' is not implemented. Supported modes:\n" +\
               " single_point\n" +\
               " geopt\n" +\
               " kseg"
              )

    if self.setting.restart:
      print >>inp, " RESTART WAVEFUNCTION"

    if not self.setting.set_center and self.setting.set_margin:
      print >>inp, " CENTER MOLECULE OFF"
      if not self.setting.set_celldm:
        Rt = np.transpose(new_structure.R)
        for i in xrange(0, 3):
          self.setting.celldm[i] = (max(Rt[i]) - min(Rt[i]))\
                                 + 2 * self.setting.margin
        new_center=[min(Rt[i])-self.setting.margin \
          for i in (0,1,2)]
        new_structure.center(new_center)
      elif self.setting.set_shift:
        pass
      else:
        sys.exit("ERROR from io_format/cpmd.py->inp.write: " +\
                 "celldm and margin " + \
                 "can NOT be set simultaneously.")
  
    elif self.setting.set_center and not self.setting.set_margin:
      new_structure.center(self.setting.center)
      print >>inp, " CENTER MOLECULE OFF"

    elif self.setting.set_center and self.setting.set_margin:
      sys.exit("ERROR from io_format/cpmd.py->inp.write: " +\
               "center and margin " + \
               "can NOT be set simultaneously.")

    if self.setting.set_shift:
      new_structure.shift(self.setting.shift)

    if self.setting.set_convergence:
      print >>inp, " CONVERGENCE ORBITALS"
      print >>inp, "  %e" % self.setting.convergence

    if self.setting.set_step:  
      print >>inp, " MAXITER"
      print >>inp, "  " + str(self.setting.maxstep)

    if self.setting.save_density:
      print >>inp, " RHOOUT"

    # should be set by setting!!!
    if new_structure.multiplicity > 1:
      print >>inp, " LOCAL SPIN DENSITY"
    print >>inp, " MIRROR"
    print >>inp, "&END"
    print >>inp, ""

    print >>inp, "&DFT"
    print >>inp, " FUNCTIONAL " + self.setting.theory.upper()
    print >>inp, "&END"
        
    print >>inp, ""
    print >>inp, "&SYSTEM"
    print >>inp, " SYMMETRY"
    print >>inp, self.setting.q_symmetry()
    if self.setting.isolated:
      print >>inp, " POISSON SOLVER TUCKERMAN"
    if angstrom:
      print >>inp, " ANGSTROM"
    print >>inp, " CELL ABSOLUTE"
    print >>inp, "  " + " ".join(map(str, self.setting.celldm))
    if self.setting.set_scale:
      print >>inp, " SCALE",
      print >>inp, "SX=%d SY=%d SZ=%d" % \
        (self.setting.scale[0],
         self.setting.scale[1],
         self.setting.scale[2])
    print >>inp, " CUTOFF"
    print >>inp, "  " + str(self.setting.cutoff)
    if self.setting.mesh:
      mesh = np.array(self.setting.celldm[0:3])\
           * self.setting.mesh
      mesh.tolist()
      print >>inp, " MESH"
      print >>inp, "  " + " ".join(map(str,mesh))
    if not self.setting.isolated and self.setting.kpoints:
      print >>inp, " KPOINTS MONKHORST-PACK"
      print >>inp, "  " + " ".join(map(str, self.setting.kmesh))
    # set by setting
    if new_structure.charge:
      print >>inp, " CHARGE"
      print >>inp, "  " + str(new_structure.charge)
    # set by setting
    if new_structure.multiplicity > 1:
      print >>inp, " MULTIPLICITY"
      print >>inp, "  " + str(new_structure.multiplicity)
    print >>inp, "&END"
    print >>inp, ""
    print >>inp, "&ATOMS"
  
    # loop through all atom types
    #new_structure = copy.deepcopy(new_structure)
    new_structure.sort()
    PP = self.PPString
    type_index = new_structure.index
    type_list = new_structure.type_list
    atom_list = self.atom_list
    Z = new_structure.Z
    for atom_type in xrange(0,len(type_index)-1):
      type_n = type_index[atom_type+1] - type_index[atom_type]
      if atom_list.has_key(str(Z[type_index[atom_type]])):
        key = str(Z[type_index[atom_type]])
        AtomPP = atom_list[key]
        if qtk.isAtom(AtomPP):
          print >>inp, "*" + PP(AtomPP)
        else:
          print >>inp, "*" + atom_list[key]
        del atom_list[str(Z[type_index[atom_type]])]
      else:
        print >>inp, "*" + \
                PP(new_structure.type_list[type_index[atom_type]],
                   **kwargs)
      print >>inp, " LMAX=F\n" + "  " + str(type_n)
      for I in\
        xrange(type_index[atom_type],type_index[atom_type+1]):
        print >>inp, "  " + \
        " ".join(" % 8.4f" % x for x in new_structure.R[I][:])
      print >>inp 
    print >>inp, "&END"

    if name:
      inp.close()

class out(object):
  def __init__(self, qmout):
    self.info = ''
    self.Et = np.nan
    self.SCFStep = np.nan
    self.getEt(qmout)
    #self.getSteps(qmout)

  def getEt(self, name):
    out = sys.stdout if re.match('stdout',name)\
          else open(name, 'r')

    done = False
    finished = False
    converged = True
  
    scf_p = re.compile('^ *[0-9]*  [0-9]\.[0-9]{3}E-[0-9]{2}   .*')
    Et_cpmd = re.compile('.*TOTAL ENERGY = *([-0-9\.]*)')
    convergence = re.compile('.*BUT NO CONVERGENCE.*')
    soft_exit = re.compile('.*SOFT EXIT REQUEST.*')
    done_cpmd = re.compile(' \* *FINAL RESULTS *\*')
    qmInfo = re.compile('.*qmInfo.*')
    info_head = re.compile('.*qmInfo:')
    info_tail = re.compile(' *\*\*.*')

    while True:
      line = out.readline()
      if not line: break

      if (re.match(scf_p, line)):
        try:
          data = [float(x) for x in line.split()]
          self.SCFStep = int(data[0])
        except:
          qtk.report("\n\nFailed while eading file:", name,
                    'at line: ', line,
                    '... skipping!! \n', color='yellow')
      elif re.match(convergence, line) and self.SCFStep > 5:
        converged = False
      elif re.match(soft_exit, line):
        converged = False
      elif re.match(qmInfo, line):
        tmp1 = re.sub(info_head, '', line)
        tmp2 = re.sub(info_tail, '', tmp1)
        self.info = tmp2
      elif (re.match(done_cpmd,line)):
        done = True,
      elif (re.match(Et_cpmd, line)) and done and converged:
        self.Et = float(Et_cpmd.match(line).group(1))
        finished = True
        
    if not finished:
      self.Ehartree = 0
      self.status = 'not finished'
      self.Et = np.nan
    out.close()

  # deprecated
  def getSteps(self, name):
    # CPMD format
    scf_p = \
      re.compile('^ *[0-9]*  [0-9]\.[0-9]{3}E-[0-9]{2}   .*')
    out = open(name, 'r')
    while True:
      line = out.readline()
      if not line: break
      if (re.match(scf_p, line)):
        data = [float(x) for x in line.split()]
        self.SCFStep = int(data[0])
    #return SCFStep
