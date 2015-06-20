from mastermind.query import Query, LazyDataObject


class GroupsQuery(Query):
    def __init__(self, client):
        super(GroupsQuery, self).__init__(client)
        self._filter = {}

    def __getitem__(self, key):
        return Group(self.client, key)

    def next_group_ids(self, count=1):
        """Fetch some free group ids.

        Elliptics groups are identified by integer group ids. Mastermind provides
        a sequence of increasing group ids for assigning to new groups added to storage.

        Args:
          count: number of group ids to fetch.
        """
        return self.client.request('get_next_group_number', count)

    def __iter__(self):
        groups = self.client.request('get_groups_list', [self._filter])
        for g_data in groups:
            gq = Group(self.client, GroupDataObject._raw_id(g_data))
            gq._set_raw_data(g_data)
            yield gq


class GroupDataObject(LazyDataObject):
    def _fetch_data(self):
        return self.client.request('get_group_info', self.id)

    @staticmethod
    def _raw_id(raw_data):
        return raw_data['id']

    @property
    @LazyDataObject._lazy_load
    def status(self):
        return self._data['status']

    @property
    @LazyDataObject._lazy_load
    def status_text(self):
        return self._data['status_text']


class GroupQuery(Query):
    def __init__(self, client, id):
        super(GroupQuery, self).__init__(client)
        self.id = id

    @property
    def meta(self):
        """Reads metakey for group.

        Returns:
          Group metakey, already unpacked.
        """
        return self.client.request('get_group_meta', [self.id, None, True])['data']

    def move(self, uncoupled_groups=None, force=False):
        """Create group move job.

        Job will move group's node backend to uncoupled group's node backend.
        Uncoupled group will be replaces, source group node backend will be disabled.

        Args:
          uncoupled_groups: list of uncoupled group that should be merged together
            and replaced by source group.
          force: cancel all pending jobs of low priority (e.g. recover-dc and defragmentation).

        Returns:
          A json of created job (or a dict with a single error key and value).
        """
        uncoupled_groups = [GroupQuery._object(self.client, g) for g in uncoupled_groups or []]
        return self.client.request('move_group',
                                   [self.id,
                                    {'uncoupled_groups': [g.id for g in uncoupled_groups]},
                                    force])


class Group(GroupQuery, GroupDataObject):
    pass