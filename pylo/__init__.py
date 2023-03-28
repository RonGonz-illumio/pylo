import os
import sys
from typing import Callable

from .tmp import *
from .Helpers import *

from .Exception import PyloEx, PyloApiEx, PyloApiTooManyRequestsEx, PyloApiUnexpectedSyntax, PyloObjectNotFound
from .SoftwareVersion import SoftwareVersion
from .IPMap import IP4Map
from .ReferenceTracker import ReferenceTracker, Referencer, Pathable
from .API.APIConnector import APIConnector, ObjectTypes
from .API.RuleSearchQuery import RuleSearchQuery, RuleSearchQueryResolvedResultSet
from .API.ClusterHealth import ClusterHealth
from .API.Explorer import ExplorerResultSetV1, RuleCoverageQueryManager
from .API.CredentialsManager import get_credentials_from_file
from .LabelCommon import LabelCommon
from .Label import Label
from .LabelGroup import LabelGroup
from .LabelStore import LabelStore, label_type_app, label_type_env, label_type_loc, label_type_role
from .IPList import IPList, IPListStore
from .AgentStore import AgentStore, VENAgent
from .Workload import Workload, WorkloadInterface
from .WorkloadStore import WorkloadStore
from .VirtualService import VirtualService
from .VirtualServiceStore import VirtualServiceStore
from .Service import Service, ServiceStore, PortMap, ServiceEntry
from .Rule import Rule, RuleServiceContainer, RuleSecurityPrincipalContainer, DirectServiceInRule, RuleHostContainer, RuleActorsAcceptableTypes
from .Ruleset import Ruleset, RulesetScope, RulesetScopeEntry
from .RulesetStore import RulesetStore
from .SecurityPrincipal import SecurityPrincipal, SecurityPrincipalStore
from .Organization import Organization
from .Query import Query


def load_organization(hostname: str, port: int,  api_user: str, api_key: str,
                      organization_id: int, verify_ssl: bool = True,
                      list_of_objects_to_load: Optional[List['pylo.ObjectTypes']] = None,
                      include_deleted_workloads: bool = False) -> Organization:
    """
    Load an organization from the API with parameters provided as arguments.
    """
    api = APIConnector(hostname=hostname, port=port, apiuser=api_user, apikey=api_key, org_id=organization_id,
                       skip_ssl_cert_check=not verify_ssl)
    org = Organization(1)
    org.load_from_api(api, include_deleted_workloads=include_deleted_workloads,
                      list_of_objects_to_load=list_of_objects_to_load)

    return org


def load_organization_using_credential_file(hostname_or_profile_name: str = None,
                                            credential_file: str = None,
                                            list_of_objects_to_load: Optional[List['pylo.ObjectTypes']] = None,
                                            include_deleted_workloads: bool = False,
                                            callback_api_objects_downloaded: Callable = None) -> Organization:
    """
    Credentials files will be looked for in the following order:
    1. The path provided in the credential_file argument
    2. The path provided in the PYLO_CREDENTIAL_FILE environment variable
    3. The path ~/.pylo/credentials.json
    4. Current working directory credentials.json
    :param hostname_or_profile_name:
    :param credential_file:
    :param list_of_objects_to_load:
    :param include_deleted_workloads:
    :param callback_api_objects_downloaded: callback function that will be called after each API has finished downloading all objects
    :return:
    """
    credentials = get_credentials_from_file(hostname_or_profile_name, credential_file)

    api = APIConnector(hostname=credentials['hostname'], port=credentials['port'],
                       apiuser=credentials['api_user'], apikey=credentials['api_key'],
                       org_id=credentials['org_id'],
                       skip_ssl_cert_check=not credentials['verify_ssl'])
    connector = pylo.APIConnector(hostname=credentials['hostname'], port=credentials['port'],
                                  apiuser=credentials['api_user'], apikey=credentials['api_key'],
                                  org_id=credentials['org_id'],
                                  skip_ssl_cert_check=not credentials['verify_ssl'])

    objects = connector.get_pce_objects(list_of_objects_to_load=list_of_objects_to_load,
                                        include_deleted_workloads=include_deleted_workloads)

    if callback_api_objects_downloaded is not None:
        callback_api_objects_downloaded(connector)

    org = Organization(1)
    org.load_from_json(objects,list_of_objects_to_load=list_of_objects_to_load)

    return org


ignoreWorkloadsWithSameName = True

objectNotFound = object()









