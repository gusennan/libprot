import io
import os
import subprocess
from enum import Enum
from pathlib import Path


## This generates the topology and coordinates using the protein force field
# source leaprc.protein.ff14SB
# pdb = loadPdb /home/nsg/tmp/KE07_apo_pdb4amber.pdb
# saveamberparm pdb prmtop prmcrd
# quit

## This runs sander
# sander -O -i mdin -o mdout -c rst7 -p prmtop -r ncrst
## mdin:
# Test run 1
#  &cntrl
#     IMIN = 1,
#     NCYC = 250,
#     MAXCYC = 500,
#     NTB = 0,
#     IGB = 0,
#     CUT = 12
# /

class ForceFieldType(Enum):
    PROTEIN = 'leaprc.protein.ff14SB'
    RNA = 'leaprc.RNA.OL3'
    DNA = 'leaprc.DNA.OL15'
    WATER = 'leaprc.water.tip3p'  # not needed if using implicit solvent model
    GENERAL_FF = 'leaprc.gaff2'


def make_amber_env():
    """AMBERHOME must be a valid environment variable, otherwise this function will throw.
    :returns an Amber environment, which is copied from amber.sh in the amber distribution"""
    amberhome = "AMBERHOME"
    env = dict(os.environ)
    if not env.get(amberhome):
        raise EnvironmentError(f"Expecting {amberhome} to be defined in the user's environment")

    env['AMBER_PREFIX'] = amber_prefix = env[amberhome]
    env['PATH'] = f"{amber_prefix}:{env.get('PATH')}"
    env['PYTHONPATH'] = f"{amber_prefix}/lib/python2.7/site-packages:{env.get('PYTHONPATH')}"
    env['LD_LIBRARY_PATH'] = f"{amber_prefix}/lib:{env.get('LD_LIBRARY_PATH')}"
    return env


def ensure_bin(bin: Path):
    if not bin.exists():
        raise FileNotFoundError(f"{bin} does not exist")
    if not os.access(str(bin), os.X_OK):
        raise PermissionError(f"{bin} is not executable")


def run_subprocess(bin: Path, stdin, args):
    ensure_bin(bin)
    completed_proc = subprocess.run([str(bin)] + args, stdin=stdin, capture_output=True, text=True,
                                    env=make_amber_env())
    return completed_proc.returncode, io.StringIO(completed_proc.stdout), io.StringIO(completed_proc.stderr)


def prep_pdb_for_amber(instream: io.TextIOBase):
    """Runs pdb4amber on the structure
    :param instream: an instream for the PDB.
    :return tuple(return code, stdout, stderr)
    """
    env = make_amber_env()
    path_to_bin = Path(env['AMBERHOME']).joinpath("bin", "pdb4amber")
    return run_subprocess(path_to_bin, instream, ["--dry"])


def minimize_pdb(instream: io.TextIOBase):
    """Runs sander on the PDB to minimize it"""
