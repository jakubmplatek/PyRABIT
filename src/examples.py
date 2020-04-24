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
#response = ci.quick_deploy(projectName=job, buildNumber=<your intended build number>)
print(f'{job}: {response}')

# update baseline revision
revision = '1234567'
update_response = ci.update(projectName=job, revision=revision)
print(update_response)
