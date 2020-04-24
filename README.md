# PyRABIT
AutoRABIT API wrapper for Python

current version: `1.0.0`

### Supported APIs

Current version supports only cijobs services in v1 (/api/cijobs/v1/*)
Supported services:
 - CIjobHistory: `autorabit.cijobs.history`
 - PollCIJobStatus: `autorabit.cijobs.poll`
 - TriggerBuild: `autorabit.cijobs.trigger`
 - TriggerQuickDeploy: `autorabit.cijobs.quick_deploy`
 - UpdatBaseLineRevision: `autorabit.cijobs.update`

Detailed lists of required parameters and function behaviour available in docstrings
 
Full AutoRABIT API documentation:
https://documenter.getpostman.com/view/7212585/SVtYQmEg?version=latest


### Usage

Update the `src/examples.py` with your instance URL, API token and CI Job name, where indicated.
Running it by simply invoking `$ py examples.py` will pack autorabit.py into `src/__pycache__` and treat it as a module.

To use the module in existing programs, copy `src/autorabit.py` to any Python3 import lookup location
