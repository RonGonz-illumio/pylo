import pylo


class LabelGroup(pylo.ReferenceTracker, pylo.LabelCommon):

    """
    :type _members: dict[str,pylo.Label|pylo.LabelGroup]
    """

    def __init__(self, name, href, ltype, owner):
        pylo.ReferenceTracker.__init__(self)
        pylo.LabelCommon.__init__(self, name, href, ltype, owner)
        self._members = {}
        self.raw_json = None

    def load_from_json(self):
        # print(self.raw_json)
        if 'labels' in self.raw_json:
            for href_record in self.raw_json['labels']:
                if 'href' in href_record:
                    find_label = self.owner.find_by_href_or_die(href_record['href'])
                    find_label.add_reference(self)
                    self._members[find_label.name] = find_label
                else:
                    raise pylo.PyloEx('LabelGroup member has no HREF')

    def expand_nested_to_array(self):
        results = {}
        for label in self._members.values():
            if isinstance(label, pylo.Label):
                results[label] = label
            elif isinstance(label, pylo.LabelGroup):
                for nested_label in label.expand_nested_to_array():
                    results[nested_label] = nested_label
            else:
                raise pylo.PyloEx("Unsupported object type {}".format(type(label)))
        return list(results.values())


    def is_group(self):
        return True

    def is_label(self):
        return False

