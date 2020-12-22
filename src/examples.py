import time
import autorabit
# initiate handlers
autorabit.init(
    endpoint = 'https://my.autorabit.url',
    token = 'myAutoRABITtoken'
)
# short-hand for cijobs services
ci = autorabit.cijobs
# example CI Job (has to exist in the instance)
job = 'job-to-test-apis'

# get job history
history = ci.history(projectName=job)
for build in history:
    print(f'{build["orgProjectName"]}_{build["buildNumber"]}: {build["overAllStatus"]}')

# trigger a job
response = ci.trigger(projectName=job, title='testing-pyrabit')
print(response)

# poll the triggered job
build_num = response['cyclenum']
while 'Inprogress' == response['status']:
    print(f'{job}_{build_num}: Inprogress')
    time.sleep(2) # wait for 2 seconds
    response = ci.poll(projectName=job, buildNumber=build_num)
print(f'{job}_{build_num}: {response["status"]}')

# trigger a quick deploy on a successful validation job
# the job must be a validate-only,
# running the required minimum of unit tests to cover the payload
# and be successful; there cannot be any deployments in the org after the validation
# as that would invalidate the quick deploy option
response = ci.quick_deploy(projectName=job)
# optionally, a specific build number can be used:
#response = ci.quick_deploy(projectName=job, buildNumber=build_num)
print(f'{job}: {response}')

# trigger a rollback validation on a successful deployment
# the job must be configured with rollback enabled
# first, check the status
details = ci.rollback_details(projectName=job)
# optionally, a specific biuld number can be used
#details = ci.rollback_details(projectName=job, buildNumber=build_num)
build_num = details.get('cyclenum', build_num)
backup_status = details.get('backupStatus', None)
print(f'backup status for {job}_{build_num}: {backup_status}')
# print out the manifest
manifest = {}
manifest_keys = ['constructiveChanges', 'destructiveChangesPre', 'destructiveChangesPost']
for key in manifest_keys:
    if key in details:
        # optionally, save the manifest into a dict
        # to override when invoked
        # elements can be either removed entirely
        # or moved between pre- and post-destructive
        manifest.update({key: details[key]})
        print(f'{key}: {details[key]}')
# trigger rollback validation using the successful backup
if backup_status in autorabit.STATUS_OK:
    response = ci.rollback(
        projectName=job, buildNumber=build_num,
        validateDeployment=True, **manifest)

# get iteration id and check the status using poll method
# replace the rollback status fields with the ci job status fields
iteration = response.pop('revertId', None)
rollback_status = response.pop('status', 'Inprogress')
response.update({
    'rollbackstatus': rollback_status,
    'rollbackIternationNumber': iteration
})
# poll
while 'Inprogress' == response['rollbackstatus']:
    print(f'{job}_{build_num}_{iteration}: Inprogress')
    time.sleep(2) # wait for 2 seconds
    response = ci.poll(projectName=job, buildNumber=build_num)
print(f'{job}_{build_num}_{iteration}: {response["rollbackstatus"]}')

# alternatively, get the history of rollback iterations for a given job
rollback_history = ci.rollback_history(projectName=job, buildNumber=build_num)
print(rollback_history) # this will print all iterations



# update baseline revision
revision = '1234567'
update_response = ci.update(projectName=job, revision=revision)
print(update_response)
