from typing import Dict, List, Any
import pylo
from pylo import log
from .Helpers import *
from typing import *


class PortMap:
    def __init__(self):
        self._tcp_map = []
        self._udp_map = []
        self._protocol_map = {}

    def add(self, protocol, start_port: int, end_port: int = None, skip_recalculation=False):

        proto = None

        if type(protocol) is str:
            lower = protocol.lower()
            if lower == 'tcp':
                proto = 6
            elif lower == 'udp':
                proto = 17
            else:
                raise pylo.PyloEx("Unsupported protocol name '{}'".format(protocol))
        else:
            proto = protocol

        if proto != 6 and proto != 17:
            self._protocol_map[proto] = True
            return

        if start_port is None:
            end_port = start_port

        new_entry = [start_port, end_port]

        if not skip_recalculation:
            self.merge_overlapping_maps()

    def merge_overlapping_maps(self):
        self._sort_maps()

        new_map = []

        cur_entry = None

        for original_entry in self._tcp_map:
            if cur_entry is None:
                cur_entry = original_entry
                continue

            cur_start = cur_entry[0]
            cur_end = cur_entry[1]
            new_start = original_entry[0]
            new_end = original_entry[1]

            if new_start > cur_end + 1:
                new_map.append(cur_entry)
                continue

            if new_end > cur_end:
                cur_entry[1] = new_end

        if cur_entry is not None:
            self._tcp_map = []
        else:
            new_map.append(cur_entry)
            self._tcp_map = new_map

        new_map = []

        for original_entry in self._udp_map:
            if cur_entry is None:
                cur_entry = original_entry
                continue

            cur_start = cur_entry[0]
            cur_end = cur_entry[1]
            new_start = original_entry[0]
            new_end = original_entry[1]

            if new_start > cur_end + 1:
                new_map.append(cur_entry)
                continue

            if new_end > cur_end:
                cur_entry[1] = new_end

        if cur_entry is not None:
            self._udp_map = []
        else:
            new_map.append(cur_entry)
            self._udp_map = new_map

    def _sort_maps(self):
        def first_entry(my_list):
            return my_list[0]

        self._tcp_map.sort(key=first_entry)
        self._udp_map.sort(key=first_entry)


class ServiceEntry:
    def __init__(self, protocol: int, port: int = None, to_port: Optional[int] = None, icmp_code: Optional[int] = None,
                 icmp_type: Optional[int] = None):
        self.protocol = protocol
        self.port: int = port
        self.to_port: Optional[int] = to_port
        self.icmp_type: Optional[int] = icmp_type
        self.icmp_code: Optional[int] = icmp_code

    @staticmethod
    def create_from_json(data: Dict):
        protocol = data['proto']
        if protocol == 1:
            icmp_code = data['icmp_code']
            icmp_type = data['icmp_type']
            entry = ServiceEntry(protocol, icmp_code=icmp_code, icmp_type=icmp_type)
        elif protocol == 17 or protocol == 6:
            port = data['port']
            to_port = data.get('to_port')
            entry = ServiceEntry(protocol, port=port, to_port=to_port)
        else:
            entry = ServiceEntry(protocol)

        return entry

    def is_tcp(self) -> bool:
        return self.protocol == 6

    def is_udp(self) -> bool:
        return self.protocol == 17

    def to_string_standard(self, protocol_first=True) -> str:

        if self.protocol == -1:
            return 'All Services'

        if protocol_first:
            if self.protocol == 17:
                if self.to_port is None:
                    return 'udp/' + str(self.port)
                return 'udp/' + str(self.port) + '-' + str(self.to_port)
            elif self.protocol == 6:
                if self.to_port is None:
                    return 'tcp/' + str(self.port)
                return 'tcp/' + str(self.port) + '-' + str(self.to_port)

            return 'proto/' + str(self.protocol)

        if self.protocol == 17:
            if self.to_port is None:
                return str(self.port) + '/udp'
            return str(self.port) + '-' + str(self.to_port) + '/udp'
        elif self.protocol == 6:
            if self.to_port is None:
                return str(self.port) + '/tcp'
            return str(self.port) + '-' + str(self.to_port) + '/tcp'

        return str(self.protocol) + '/proto'


class Service(pylo.ReferenceTracker):

    def __init__(self, name: str, href: str, owner: 'pylo.ServiceStore'):
        pylo.ReferenceTracker.__init__(self)

        self.owner: 'pylo.ServiceStore' = owner
        self.name: str = name
        self.href: str = href

        self.entries: List['pylo.ServiceEntry'] = []

        self.description: Optional[str] = None
        self.processName: Optional[str] = None

        self.deleted: bool = False

        self.raw_json = None

    def load_from_json(self, data):
        self.raw_json = data
        self.description = data['description']

        self.processName = data['process_name']

        service_ports = data.get('service_ports')
        if service_ports is not None:
            for entry_data in data['service_ports']:
                entry = ServiceEntry.create_from_json(entry_data)
                self.entries.append(entry)

        if data['deleted_at'] is not None:
            self.deleted = True

    def get_api_reference_json(self):
        return {'service': {'href': self.href}}

    def get_entries_str_list(self, protocol_first=True) -> List[str]:
        result: List[str] = []
        for entry in self.entries:
            result.append(entry.to_string_standard(protocol_first=protocol_first))
        return result


class ServiceStore(pylo.Referencer):
    itemsByName: Dict[str, Service]
    itemsByHRef: Dict[str, Service]

    def __init__(self, owner):
        """:type owner: pylo.Organization"""
        pylo.Referencer.__init__(self)
        self.owner = owner
        self.itemsByHRef = {}
        self.itemsByName = {}

        self.special_allservices = pylo.Service('All Services', '/api/v1/orgs/1/sec_policy/draft/services/1', self)

    def load_services_from_json(self, json_list):
        for json_item in json_list:
            if 'name' not in json_item or 'href' not in json_item:
                raise Exception("Cannot find 'value'/name or href for service in JSON:\n" + nice_json(json_item))
            new_item_name = json_item['name']
            new_item_href = json_item['href']

            new_item = pylo.Service(new_item_name, new_item_href, self)
            new_item.load_from_json(json_item)

            if new_item_href in self.itemsByHRef:
                raise Exception("A service with href '%s' already exists in the table", new_item_href)

            self.itemsByHRef[new_item_href] = new_item
            self.itemsByName[new_item_name] = new_item

            log.debug("Found service '%s' with href '%s'", new_item_name, new_item_href)
