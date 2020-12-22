"""
Wrapper module for AutoRABIT API services

To utilize the module, place it in the import directory
and use the code below
    >>> import autorabit
    >>> autorabit.init(endpoint=[your endpoint], token=[your token])
    >>> autorabit.service_handler.service_function(**kwargs)

Available service functions:
    - cijobs.history
    - cijobs.poll
    - cijobs.quick_deploy
    - cijobs.trigger
    - cijobs.update
    - cijobs.rollback
    - cijobs.rollback_details
    - cijobs.rollback_history


Full documentation of the AutoRABIT API can be found in the Knowledge Base:
https://knowledgebase.autorabit.com/docs/get-allcijoblist
"""
import requests

__author__ = 'Jakub Platek'
__version__ = '1.2.0'
__maintainer__ = 'Jakub Platek'
__email__ = 'jakub.p@autorabit.com'

# constants
STATUS_INPROGRESS = 'Inprogress'
STATUS_COMPLETE = ['Completed', 'Success', 'Successful']
STATUS_OK = ['Inprogress', 'Completed', 'Success', 'Successful']


def init(endpoint='http://localhost', token=None, **kwargs):
    """
    Authentication initialization for AutoRABIT instance

    Has to be called before using any service handlers

    Parameters:
        endpoint (str): full URL of the AutoRABIT instance (including https://)
        token (str): authentication token string

    Raises:
        RabitError: if token is not provided
    """
    # set properties
    global _endpoint
    global _token
    _endpoint = endpoint
    if token is None:
        raise RabitError('Please provide a valid AutoRABIT TOKEN')
    _token = token
    # init global service handlers
    global cijobs
    cijobs = CIJobService()
# END init

class CIJobService:
    def __init__(self):
        """
        Handler for the cijobs service implementation v1
        """
        self._url = f'{_endpoint}/api/cijobs/v1'
        self._headers = {
            'token': _token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    # END constructor

    def trigger(self, projectName=None, title='automated-build', **kwargs):
        """
        Service to trigger a build of a pre-configured CI Job

        Parameters:
            projectName (str):
                name of the CI Job to be called
            title (str):
                build label for the triggered build (default automated-build)

        Raises:
            RabitError:
                required parameter is missing
            RabitStatusError:
                a failing status is returned by AutoRABIT
            RabitConnectError:
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        # if we're here, the minimum params are provided
        # build request data
        endpoint = f'{self._url}/trigger'
        data = {
            'projectName': projectName,
            'title': title
        }
        # call service
        try:
            response = requests.post(
                endpoint,
                headers=self._headers,
                json=data
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot trigger job', exc=e) from e
        # parse response
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        res_body = response.json()
        status = res_body['status']
        if not status in STATUS_OK:
            raise RabitStatusError(res_body)
        # if no exceptions were thrown, return response JSON
        return res_body
    # END trigger function

    def poll(self, projectName=None, buildNumber=None, **kwargs):
        """
        Service to poll the results of a CI Job build

        Parameters:
            projectName (str):
                name of the CI Job to be queried
            buildNumber (int):
                build number to be polled; if not provided, latest build status will be returned

        Raises:
            RabitError: 
                required parameter is missing
            RabitConnectError:
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        endpoint = f'{self._url}/pollstatus/{projectName}'
        if buildNumber is not None:
            endpoint += f'/{buildNumber}'
        # call service
        try:
            response = requests.get(
                endpoint,
                headers=self._headers
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot poll job', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        return response.json()
    # END poll function

    def history(self, projectName=None, build_from=-1, build_to=-1, **kwargs):
        """
        Service to get the history of specified range of builds of a given CI Job

        Parameters:
            projectName (str): 
                name of the CI Job to be queried
            build_from (int): 
                first build number to include in the query
            build_to (int): 
                last build number to include in the query
            buildNumber (int): 
                if provided, will override build_to and build_from, and request data for a single build

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                an unexpected response is received from AutoRABIT
            RabitConnectError 
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            list: ciJobHistoryList element of the HTTP response body; list of dicts detailing all requested builds
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        if 'buildNumber' in kwargs:
            build_from = kwargs['buildNumber']
            build_to = kwargs['buildNumber']
        # build request
        endpoint = f'{self._url}/history/{projectName}'
        parameters = {
            'from': build_from,
            'to': build_to
        }
        # call service
        try:
            response = requests.get(
                endpoint,
                headers=self._headers,
                params=parameters
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot obtain history', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        result = response.json()
        if 'ciJobHistoryList' in result:
            result = result['ciJobHistoryList']
        else:
            raise RabitStatusError(result)
        return result
    # END history function

    def update(self, projectName=None, revision=None):
        """
        Service to get the update the configuration of a given CI Job
        Currently only supports the service to update the baseline revision
        If the requested revision is aready set as baseline on the given CI Job, a RabitError exception is raised

        Parameters:
            projectName (str): 
                name of the CI Job to be updated
            revision (str): 
                new baseline revision to be set on a given CI Job
                note api v1 supports the revisions of up to 10 characters only

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                a failing status is returned by AutoRABIT
            RabitConnectError:
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        if revision is None:
            raise RabitError('Please provide a valid baseline revision')
        # build request
        endpoint = f'{self._url}/update/baselinerevision'
        data = {
            'projectName': projectName,
            'baseLineRevision': revision[0:10]
        }
        # call service
        try:
            response = requests.post(
                endpoint,
                headers=self._headers,
                json=data
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot perform update', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        res_body = response.json()
        status = res_body['status']
        if 'Success' != status:
            # TODO: parse if the response indicates the revision was already set
            raise RabitStatusError(res_body)
        return response.json()
    # END update function

    def quick_deploy(self, projectName=None, buildNumber=None):
        """
        Service to trigger Quick Deploy on a previously validated CI Job build

        Parameters:
            projectName (str): 
                name of the CI Job
            buildNumber (str): 
                build number for which the Quick Deploy is to be initiated
                if not provided, last available build will be used

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                a failing status is returned by AutoRABIT
            RabitConnectError: 
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        # build request data
        endpoint = f'{self._url}/triggerquickdeploy/{projectName}'
        if buildNumber is not None:
            endpoint += f'/{buildNumber}'
        # call service
        try:
            response = requests.post(
                endpoint,
                headers=self._headers
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot trigger job', exc=e) from e
        # parse response
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        res_body = response.json()
        status = res_body['status']
        if not status.startswith('Quick deploy initiated successfully'):
            raise RabitStatusError(status)
        # if no exceptions were thrown, return response JSON
        return res_body
    # END quick_deploy function

    def rollback(self, projectName=None, buildNumber=None, **kwargs):
        """
        Service to trigger a rollback on a given CI Job build

        Parameters:
            projectName (str): 
                name of the CI Job to be queried
            buildNumber (int): optional
                if not provided, latest available build will be used
            validateDeployment (bool): default False
                if true, rollback will run in validate-only mode
            testLevel (str): optional
                if not provided, salesforce default level will be used 
                (depends on the type of target org)
                to run tests dynamically, use RunTestsBasedOnChanges
            constructiveChanges (dict): optional
                JSON-formatted package manifest of constructive rollback elements
            destructiveChangesPost (dict): optional
                JSON-formatted package manifest of destructive (post) rollback elements
            destructiveChangesPre (dict): optional
                JSON-formatted package manifest of destructive (pre) rollback elements

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                an unexpected response is received from AutoRABIT
            RabitConnectError 
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        # build request
        endpoint = f'{self._url}/rollback'
        data = { 'projectName': projectName }
        if buildNumber:
            data.update({'cyclenum': buildNumber})
        # dump the rest of the kwargs into data and hope for the best
        data.update(kwargs)
        # call service
        try:
            response = requests.post(
                endpoint,
                headers=self._headers,
                json=data
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot trigger rollback', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        return response.json()
    # END rollback function

    def rollback_details(self, projectName=None, buildNumber=None):
        """
        Service to get the detailed information about the rollback package,
        including all constructive and destructive elements, 
        as well as execution status (for the latest iteration only)

        Parameters:
            projectName (str): 
                name of the CI Job to be queried
            buildNumber (int): optional
                if not provided, latest available build will be used 

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                an unexpected response is received from AutoRABIT
            RabitConnectError 
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        # build request
        endpoint = f'{self._url}/rollback/{projectName}'
        if buildNumber:
            endpoint = f'{endpoint}/{buildNumber}'
        # call service
        try:
            response = requests.get(
                endpoint,
                headers=self._headers
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot obtain rollback details', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        return response.json()
    # END rollback_details function

    def rollback_history(self, projectName=None, buildNumber=None):
        """
        Service to get the history of rollback iterations for a given CI Job build

        Parameters:
            projectName (str): 
                name of the CI Job to be queried
            buildNumber (int): optional
                if not provided, latest available build will be used 

        Raises:
            RabitError: 
                required parameter is missing
            RabitStatusError: 
                an unexpected response is received from AutoRABIT
            RabitConnectError 
                HTTPError was raised due to HTTP request failing (status other then 20X)

        Returns: 
            list: status of all revert iterations for a given build
                  in the format matching POST rollback response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        # build request
        endpoint = f'{self._url}/rollback/history/{projectName}'
        if buildNumber:
            endpoint = f'{endpoint}/{buildNumber}'
        # call service
        try:
            response = requests.get(
                endpoint,
                headers=self._headers
            )
        except requests.exceptions.RequestException as e:
            raise RabitConnectError('Cannot obtain rollback history', exc=e) from e
        try:
            response.raise_for_status()
        except:
            raise RabitStatusError(response)
        # if no exceptions were thrown, return response JSON
        result = response.json()
        if 'revertDeployments' in result:
            result = result['revertDeployments']
        else:
            raise RabitStatusError(result)
        return result
    # END rollback_history function
# END CIJobService class

class RabitError(Exception):
    """
    Custom AutoRABIT exception type to help with exception handling

    When exception is raised from another exception,
    the original exception can be passed as an optional parameter `exc`
    """
    def __init__(self, *args, **kwargs):
        original_exception = kwargs.pop('exc', None)
        msg = args[0] if 0 < len(args) else ''
        if original_exception is not None:
            msg += f' [{original_exception}]'
        super().__init__(msg)
# END RabitError class

class RabitStatusError(RabitError):
    """
    Custom AutoRABIT exception type to help with exception handling
    """
    pass
# END RabitStatusError class

class RabitConnectError(RabitError):
    """
    Custom AutoRABIT exception type to help with exception handling for HTTP issues
    """
    pass
# END RabitConnectError class