#!/usr/bin/env python

"""
Create & run BIRD jobs to do copying to group area for ROOT files in a XML file
"""

from __future__ import print_function

import os
import sys
import argparse
import subprocess
from shutil import copy2, rmtree
try:
    # py3
    from itertools import zip_longest
except ImportError:
    # py2
    from itertools import izip_longest as zip_longest


SRM_PREFIX = "srm://dcache-se-cms.desy.de:8443"

GROUP_DIRECTORY = "/pnfs/desy.de/cms/tier2/store/group/uhh/uhh2ntuples/"

KNOWN_BRANCHES = [
    "RunII_102X_v2",
    "RunII_102X_v1",
    "RunII_101_v1",
    "RunII_94X_v3",
    "RunII_94X_v2",
    "RunII_94X_v1",
    "RunII_80X_v5",
    "RunII_80X_v4",
    "RunII_80X_v3",
]

# Sometimes people chop off the "RunII", so let's consider those as well
KNOWN_BRANCHES_CHOP = [x.replace("RunII_", "") for x in KNOWN_BRANCHES]

# Here are some manual mappings - each will be replaced by the branch name (key)
MANUAL_MAPPINGS = {
    "RunII_80X_v3": [
        'CMSSW80v3',
        'Moriond17',
        'Moriond17_80X_v3',
        'RunII_80X_Moriond17',
        'RunII_80X_v3_Dep2016Campaign',
        'RunII_80X_v3_legacy',
        'CMSSW8024',
        'RunII_80X_v3_Background',
        'RunII_80X_v3_Data',
        'RunII_80X_v3_Signal',
        'NTuples_Moriond17',
    ],

}

REVERSE_MANUAL_MAPPINGS = {x:k for k,v in MANUAL_MAPPINGS.items() for x in v}


def check_voms():
    """Checks if the user has a valid VOMS proxy, returns True if so, False otherwise"""
    cmd = "voms-proxy-info -e"
    return_code = subprocess.call(cmd.split())
    if return_code != 0:
        print("You need a valid voms proxy. Please run:")
        print("")
        print("    voms-proxy-init -voms cms")
        print("")
        print("Then retry this script")
        return False
    return True


def copy_proxy(dest="~/x509_proxy"):
    """Copy the VOMS proxy into a known location, so it can be used by condor"""
    subprocess.call("cp $(voms-proxy-info -p) %s" % (dest), shell=True)


def setup_voms():
    """Over-arching method to check VOMS proxy and copy it into known location

    Raises
    ------
    RuntimeError
        Invalid proxy
    """
    if not check_voms():
        raise RuntimeError("Failed voms certificate check")
    copy_proxy(dest="~/x509_proxy") # check it's the same as in the job template above


JOB_TEMPLATE = """
requirements      = OpSysAndVer == "SL6"
universe          = vanilla
initialdir        = {initialdir}
output            = $(logpath).o$(ClusterId).$(Process)
error             = $(logpath).e$(ClusterId).$(Process)
log               = $(logpath).$(Cluster).log
getenv            = True
environment       = "LD_LIBRARY_PATH_STORED="""+os.environ.get('LD_LIBRARY_PATH')+""""
JobBatchName      = $(JOB)
executable        = htcScript.sh
use_x509userproxy = True
# Need to copy: cp $(voms-proxy-info -p) ~/x509_proxy
# Or somehow set X509_USER_PROXY env var
x509userproxy     = $ENV(HOME)/x509_proxy
arguments         = $(scriptargs)
queue
"""

class Job(object):

    def __init__(self, name, args):
        self.name = name
        self.args = args


def setup_dir(dir_name, rm_existing=True):
    if rm_existing and os.path.isdir(dir_name):
        rmtree(dir_name)
    if not os.path.isdir(dir_name):
        os.makedirs(dir_name)


def extract_root_filename(line):
    """Get ROOT filename from line in XML file

    Parameters
    ----------
    line : str

    Returns
    -------
    str
        Ntuple filepath, sanitised to remove e.g //, which can affect splitting
    """
    this_line = line.replace('<In FileName="', '').replace('" Lumi="0.0"/>', '')
    this_line = os.path.realpath(this_line)
    return this_line


def get_root_files_from_xml(xml_filename):
    """Get list of all ROOT ntuples from XML file

    Filenames are sanitised for //, comments are ignored, and
    only files stored on /nfs or /pnfs are considered
    """
    root_filenames = []
    with open(xml_filename) as f:
        for line in f:
            line = line.strip()
            if line.startswith(("<!--", "-->")):
                continue
            root_filename = extract_root_filename(line)
            if root_filename.startswith(("/nfs", "/pnfs")):
                root_filenames.append(os.path.realpath(root_filename))
    return root_filenames


def get_destination(filename, branch_name=None):
    """Figure out destination to copy file to, based on various factors.
    Ultimately, wants to put in GROUP_DIR/<branch name>/...
    It tries to figure out branch name from the filepath, but can be 'helped'
    by the user passing it in explicitly.

    Parameters
    ----------
    filename : str
        Filepath to consider
    branch_name : None, optional
        Name of branch that this file corresponds to (e.g. RunII_80X_v3).
        Setting this can help when it is otherwise unable to determine the branch

    Returns
    -------
    str
        New filepath

    Raises
    ------
    RuntimeError
        If it cannot figure out where to put the file
    """
    filename = os.path.realpath(filename.strip())  # to tidy up any double // etc
    if filename.startswith(GROUP_DIRECTORY):
        return filename

    parts = filename.split("/")

    suffix = None

    # Let's try finding if the highest-level directory that contains a branch name
    for ind, part in enumerate(parts):
        if "RunII" in part:
            # if it's only one of the branch names, we can keep it
            # however if it's different, we should nest it underneath the branch name
            # if possible
            if part in KNOWN_BRANCHES:
                suffix = "/".join(parts[ind:])
            else:
                # look to see if any of the known branches match,
                # use that as the parent dir
                for j, kb in enumerate(KNOWN_BRANCHES):
                    if kb in part:
                        suffix = "/".join([kb] + parts[ind:])

            if suffix:
                break

        for j, kb in enumerate(KNOWN_BRANCHES_CHOP):
            if part == kb:  # /80X_v3/
                # replace choped with full name
                suffix = "/".join([KNOWN_BRANCHES[j]] + parts[j+1:])
            elif kb in part:  # /80X_v3_blah/
                # nest underneath full branch
                suffix = "/".join([KNOWN_BRANCHES[j]] + parts[j:])

            if suffix:
                break

        # Here we use the hand-coded mappings where people have used vaarious names
        if not suffix:
            if part in REVERSE_MANUAL_MAPPINGS:
                suffix = "/".join([REVERSE_MANUAL_MAPPINGS[part]] + parts[ind+1:])

            if suffix:
                break

    # None of the directories references a branch name, but we have been told it then let's use that
    if not suffix and branch_name:
        # we basically want everything after the .../user/<username>/...
        # applies for both pnfs and nfs
        # Only issue is if it has something that resembles a branch name,
        # which then is a bit double-nesting...for those one should add a manual
        # intervention in MANUAL_MAPPINGS
        if 'user' in parts:
            user_ind = parts.index("user")
            # user_ind+1 is the username, which we don't want
            # so user_ind+2 is the proper start
            # let's check if it corresponds to a branch name (or chopped version)
            # so that we can do away with it
            start_ind = user_ind+2
            elem = parts[start_ind]
            if elem == branch_name or elem == branch_name.replace("RunII_", ""):
                start_ind += 1
            suffix = "/".join([branch_name] + parts[start_ind:])

    if not suffix:
        raise RuntimeError("No idea how to handle this filename %s" % filename)

    if suffix.startswith("/"):
        raise RuntimeError("suffix should not start with /: %s" % suffix)

    return os.path.join(GROUP_DIRECTORY, suffix)


def create_filename_mapping(root_filenames, branch=None):
    """Create dict of {old filename: new filename}, where new filename is
    automatically determined

    Parameters
    ----------
    root_filenames : list[str]
        List of ROOT filenames
    branch : None, optional
        See description in get_destination()
    """
    return {f : get_destination(f, branch) for f in root_filenames}


def save_mapping_to_file(filename_mapping, output_filename):
    """Save filename mapping to file"""
    with open(output_filename, "w") as outf:
        for k, v in filename_mapping.items():
            outf.write('%s:%s\n' % (k, v))


def grouper(n, iterable, fillvalue=None):
    """Iterate through iterable in groups of n, padded by fillvalue if too short

    grouper(3, 'ABCDEFG', 'x') --> ABC DEF Gxx
    """
    args = [iter(iterable)] * n
    return zip_longest(*args, fillvalue=fillvalue)


def create_copy_jobs(filename_mapping, num_per_job, log_dir, base_name):
    """Create Job objects, where each represents a set of files to be copied.

    Parameters
    ----------
    filename_mapping : dict{str:str}
        Dict mapping old to new filenames
    num_per_job : int
        Number of files to rename per job
    log_dir : str
        Directory for job log
    base_name : str
        Name of this job

    Returns
    -------
    list[Job]
    """
    jobs = []
    for ind, file_group in enumerate(grouper(num_per_job, filename_mapping.items())):
        this_file_group = [f for f in file_group if f]
        this_name = "%s_%d" % (base_name, ind)
        this_args = {
            "logpath": os.path.join(log_dir, "job%d" % (ind)),
            "scriptargs": " ".join(["%s:%s" % (k, v) for k,v in this_file_group]),
        }
        # TODO: check length of args isn't exceeding system maximum
        # Better yet, just give indices of entries in mapping txt file to use?
        # print(len(this_args['scriptargs']))
        this_job = Job(name=this_name, args=this_args)
        jobs.append(this_job)
    return jobs


def write_dag_jobs(dag_filename, status_filename, jobs, initialdir):
    """Write condor DAG file and job file for all jobs

    Parameters
    ----------
    dag_filename : str
        Name of file to write DAG to
    status_filename : str
        Name of status file
    jobs : list[Job]
        List of Jobs to be run
    initialdir : str
        Location of initial dir with all scripts etc
    """
    job_filename = dag_filename.replace(".dag", ".job")
    with open(job_filename, 'w') as f:
        f.write(JOB_TEMPLATE.format(initialdir=initialdir))

    with open(dag_filename, 'w') as f:
        for job in jobs:
            f.write("JOB {name} {job_filename}\n".format(name=job.name, job_filename=job_filename))
            arg_str = 'logpath="{logpath}" scriptargs="{scriptargs}"'.format(**job.args)
            f.write("VARS {name} {args}\n".format(name=job.name, args=arg_str))
        f.write("RETRY ALL_NODES 2 UNLESS-EXIT 111\n")
        f.write("NODE_STATUS_FILE %s 30 ALWAYS-UPDATE\n" % (status_filename))


def write_new_xml_file(original_xml_filename, new_filename, filename_mapping):
    """Write XML file with new filenames

    Parameters
    ----------
    original_xml_filename : str
        Original XML filename to be updated
    new_filename : str
        Output XML filename
    filename_mapping : dict{str:str}
        Mapping of {original ROOT file : new ROOT file}
    """
    with open(original_xml_filename) as original_f, open(new_filename, "w") as new_f:
        for line in original_f:
            line = line.strip()
            new_line = line
            if not line.startswith(("<!--", "-->")):
                root_filename = extract_root_filename(line)
                if root_filename.startswith(("/nfs", "/pnfs")) and not root_filename.startswith(GROUP_DIRECTORY):
                    new_root_filename = filename_mapping[root_filename]
                    new_line = '<In FileName="%s" Lumi="0.0"/>' % (new_root_filename)
            new_f.write(new_line + "\n")


def write_gfal_rm_script(rm_filename, root_filenames):
    """Write script with all commands necessary to remove ROOT file from T2

    Parameters
    ----------
    rm_filename : str
        Name of output script
    root_filenames : list[str]
        List of filepaths to be removed
    """
    with open(rm_filename, 'w') as f:
        f.write("#!/usr/bin/bash -e\n")
        for rf in root_filenames:
            this_rf = rf
            if not rf.startswith(SRM_PREFIX):
                this_rf = "%s%s" % (SRM_PREFIX, rf)
            f.write("gfal-rm %s\n" % (this_rf))


if __name__ == "__main__":

    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("xml", help="XML file to process")
    parser.add_argument("--branch", help="Branch name")
    parser.add_argument("--dryRun", action='store_true', help="Make job files, but don't submit jobs to BIRD")
    parser.add_argument("--numPerJob", default=50, help="Number of files to move per job", type=int)

    args = parser.parse_args()
    print(args)

    if not os.path.isfile(args.xml):
        raise IOError("Cannot find XML file")

    if not args.dryRun:
        setup_voms()

    # Setup job directories
    base_name = os.path.splitext(os.path.basename(args.xml))[0]
    JOB_DIR = os.path.join("jobs", base_name)
    setup_dir(JOB_DIR)

    LOG_DIR = os.path.join(JOB_DIR, "logs")
    setup_dir(LOG_DIR)

    # Figure out branch name from XML path if possible and user hasn't specified it
    if not args.branch:
        for p in os.path.abspath(args.xml).split("/")[::-1]:
            if p in KNOWN_BRANCHES:
                args.branch = p
                break

    # Construct mapping from old names to new
    root_filenames = [f for f in get_root_files_from_xml(args.xml) if not f.startswith(GROUP_DIRECTORY)]
    filename_mapping = create_filename_mapping(root_filenames, branch=args.branch)
    save_mapping_to_file(filename_mapping, os.path.join(JOB_DIR, "mapping.txt"))

    # Create jobs that perform a subset of the mappings
    jobs = create_copy_jobs(filename_mapping=filename_mapping, num_per_job=args.numPerJob, log_dir=LOG_DIR, base_name=base_name)
    print("Running", len(jobs), "jobs to move", len(root_filenames), "files")

    dag_filename = "%s/copyCompress.dag" % (JOB_DIR)
    status_filename = dag_filename + ".status"
    initial_dir = os.path.dirname(os.path.abspath(__file__))
    write_dag_jobs(dag_filename=dag_filename,
                   status_filename=status_filename,
                   jobs=jobs,
                   initialdir=initial_dir)

    if not args.dryRun:
        subprocess.call("condor_submit_dag %s" % dag_filename, shell=True)
        print("Check status with:")
        print("./DAGstatus", status_filename)

    # Write new XML file
    new_filename = args.xml+".new"
    write_new_xml_file(args.xml, new_filename, filename_mapping)
    print("XML file with replacements written to", new_filename)
    print("Please only commit when all copying jobs completed successfully")

    # Write script to remove old files
    rm_filename = "rm_%s.sh" % (base_name)
    write_gfal_rm_script(rm_filename, root_filenames)
