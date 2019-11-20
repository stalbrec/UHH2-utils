# UHH2-utils

Collection of scripts, etc, that are useful for UHH2-related things.

e.g. collating statistics about ntuples, manipulating XMLs

## Installation



## Utilities

### DAGstatus

Utility to pretty-print status from condor DAG jobs.

This requires you to add the following to your DAG file:

```
NODE_STATUS_FILE <status file> <time interval> ALWAYS-UPDATE
```

See: https://htcondor.readthedocs.io/en/latest/users-manual/dagman-applications.html#capturing-the-status-of-nodes-in-a-file

Usage:

```
DAGstatus [-s] <status file> [<status file> <status file>...]
```

The script handles 1 or more DAG status files.
By default, it prints info for each job in a DAG.
Using the `-s` option only produces a one-line summary for each DAG.

The colours and formatting are configurable in `DAGstatus_config.json`.

### copyCompress

This handles transferring files from users' areas on DESY T2 to the shared group space.
