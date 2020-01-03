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
    - cijobs.trigger
    - cijobs.update


Full documentation of the API:

https://documenter.getpostman.com/view/7212585/SVtYQmEg?version=latest
"""
import requests

__author__ = 'Jakub Platek <jakub.p@autorabit.com>'
__version__ = '1.0.0'

# constants
STATUS_OK = ['Inprogress', 'Completed', 'Success']

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

class CIJobService:
    """
    Handler for the cijobs service implementation v1
    """
    def __init__(self):
        self._url = f'{_endpoint}/api/cijobs/v1'
        self._headers = {
            'token': _token,
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }
    # end of constructor

    def trigger(self, projectName=None, title='automated-build', **kwargs):
        """
        Service to trigger a build of a pre-configured CI Job

        Parameters:
            projectName (str): name of the CI Job to be called
            title (str): build label for the triggered build (default automated-build)

        Raises:
            RabitError: if required parameter is missing or
            RabitStatusError: if a failing status is returned by AutoRABIT
            HTTPError: if HTTP request fails (status other then 20X)

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
        response = requests.post(
            endpoint,
            headers=self._headers,
            json=data
        )
        # parse response
        response.raise_for_status()
        res_body = response.json()
        status = res_body['status']
        if not status in STATUS_OK:
            raise RabitStatusError(status)
        # if no exceptions were thrown, return response JSON
        return res_body
    # end of trigger service

    def poll(self, projectName=None, buildNumber=None, **kwargs):
        """
        Service to poll the results of a CI Job build

        Parameters:
            projectName (str): name of the CI Job to be queried
            buildNumber (int): build number to be polled; if not provided, latest build status will be returned

        Raises:
            RabitError: if required parameter is missing or
            HTTPError: if HTTP request fails (status other then 20X)

        Returns:
            dict: JSON-formatted body of the HTTP response
        """
        if projectName is None:
            raise RabitError('Please provide a valid AutoRABIT Project')
        endpoint = f'{self._url}/pollstatus/{projectName}'
        if buildNumber is not None:
            endpoint += f'/{buildNumber}'
        # call service
        response = requests.get(
            endpoint, 
            headers=self._headers
        )
        response.raise_for_status()
        return response.json()
    # end of poll service

    def history(self, projectName=None, build_from=-1, build_to=-1, **kwargs):
        """
        Service to get the history of specified range of builds of a given CI Job

        Parameters:
            projectName (str): name of the CI Job to be queried
            build_from (int): first build number to include in the query
            build_to (int): last build number to include in the query
            buildNumber (int): if provided, will override build_to and build_from, and request data for a single build

        Raises:
            RabitError: if required parameter is missing or
            RabitStatusError: if an unexpected response is received from AutoRABIT
            HTTPError: if HTTP request fails (status other then 20X)

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
        response = requests.get(
            endpoint,
            headers=self._headers,
            params=parameters
        )
        response.raise_for_status()
        result = response.json()
        if 'ciJobHistoryList' in result:
            result = result['ciJobHistoryList']
        else:
            raise RabitStatusError(result)
        return result
    # end of history function

    def update(self, projectName=None, revision=None):
        """
        Service to get the update the configuration of a given CI Job
        Currently only supports the service to update the baseline revision
        If the requested revision is aready set as baseline on the given CI Job, a RabitError exception is raised

        Parameters:
            projectName (str): name of the CI Job to be updated
            revision (str): new baseline revision to be set on a given CI Job

        Raises:
            RabitError: if required parameter is missing or
            RabitStatusError: if a failing status is returned by AutoRABIT
            HTTPError: if HTTP request fails (status other then 20X)

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
            'baseLineRevision': revision
        }
        # call service
        response = requests.post(
            endpoint,
            headers=self._headers,
            json=data
        )
        response.raise_for_status()
        res_body = response.json()
        status = res_body['status']
        if 'Success' != status:
            # TODO: parse if the response indicates the revision was already set
            raise RabitStatusError(status)
        return response.json()
    # end of update function
# end of CIJobService class

class RabitError(Exception):
    """
    Custom AutoRABIT exception type to help with exception handling
    """
    pass
class RabitStatusError(RabitError):
    """
    Custom AutoRABIT exception type to help with exception handling
    """
    pass
