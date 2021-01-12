#!/usr/bin/python

# Copyright: (c) 2021, Romulo Scampini <romulo@scampini.com.br>
# GNU General Public License v3.0+ (see COPYING or https://www.gnu.org/licenses/gpl-3.0.txt)
from __future__ import (absolute_import, division, print_function)

from ansible.module_utils.common.text.converters import to_text

DOCUMENTATION = r'''
---
module: grafana_org
author:
  - Romulo Scampini (@romuloscampini)
version_added: "1.0.0"
short_description: Manage Grafana Organizations
description:
  - Create, update and delete Grafana organizations via API
options:
  grafana_url:
    description:
      - Grafana url address
      - A http and https URL is also accepted (since 2.10).
    type: str
  grafana_username:
    description:
      - Grafana user with permission to manipulate organizations (Maybe user that has admin role)
      - GRAFANA API KEY is not supported.
    default: "admin"
    version_added: "1.0.0"
    type: str
  grafana_password:
    description:
      - Grafana password from user to manipulate organizations
    default: "admin"
    version_added: "1.0.0"
    type: str
  state:
    description:
      - State of the organization
    choices: [ absent, present ]
    default: present
    type: str
  org_name:
    description:
      - Organization Name
      - Case sensitive
    type: str
'''

EXAMPLES = r'''
# Create or confirm that organization exists
- name: Create grafana organization
  grafana_org:
    grafana_url: "http://localhost:3000"
    grafana_username: "admin"
    grafana_password: "admin"
    org_name: "organization_example"
    state: present

# Delete or confirm that organization does not exists
- name: Delete grafana organization
  grafana_org:
    grafana_url: "http://localhost:3000"
    grafana_username: "admin"
    grafana_password: "admin"
    org_name: "organization_example"
    state: absent
'''

RETURN = r'''
# These are examples of possible return values, and in general should use other names for return values.
org_id:
    description: Organization ID created or deleted. On check mode or when should be deleted and org does not exists, the return will be -1
    type: int
    returned: always
    sample: 1
org_name:
    description: The name of organization created or deleted
    type: str
    returned: always
    sample: "organization_example"
msg:
    description: The output message of return from operation executed
    type: str
    returned: always
    sample: 'Organization created'
'''

import json
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.urls import fetch_url
from ansible.module_utils.urls import basic_auth_header
from ansible.module_utils.urls import url_argument_spec

__metaclass__ = type


class GrafanaOrganization:
    def __init__(self):
        self.organization_id = -1
        self.organization_name = None
        self.organization_status = -1
        self.message = None

    def get(self):
        return self

    def set(self, **kwargs):
        self.organization_id = kwargs.get('organization_id', -1)
        self.organization_name = kwargs.get('organization_name', 'UNKNOWN')
        self.organization_status = kwargs.get('organization_status', -1)
        self.message = kwargs.get('message', None)


def grafana_headers(data):
    headers = {'content-type': 'application/json; charset=utf8',
               'Authorization': basic_auth_header(data['grafana_username'], data['grafana_password'])}
    return headers


def grafana_org_exists(module, grafana_url, org_name, headers):
    # search organization by name
    uri = '%s/api/orgs/name/%s' % (grafana_url, org_name)
    r, info = fetch_url(module, uri, headers=headers, method='GET')
    grafana_org = GrafanaOrganization()
    # body = json.loads(info.get("body", b'{"message": "Organization could not be created"}'))
    body = None
    if r is not None:
        body = json.loads(r.read())
    else:
        body = json.loads(info.get("body", b'{"message": "Cannot search organization"}'))
    if info['status'] == 200:
        grafana_org.set(organization_id=body['id'], organization_name=body['name'], organization_status=info['status'],
                        message='Organization exists')
    else:
        grafana_org.set(organization_name=org_name, organization_status=info['status'], message=body['message'])
    return grafana_org


def grafana_org_create(module, grafana_url, org_name, headers):
    # create organization by name
    uri = '%s/api/orgs' % (grafana_url)
    payload = {'name': org_name}
    data = json.dumps(payload)
    r, info = fetch_url(module, url=uri, data=data, headers=headers, method='POST')
    body = None
    if r is not None:
        body = json.loads(r.read())
    else:
        body = json.loads(info.get("body", b'{"message": "Organization could not be created"}'))
    grafana_org = GrafanaOrganization()
    if info['status'] == 200:
        grafana_org.set(organization_id=body['orgId'], organization_name=org_name, organization_status=info['status'],
                        message=body['message'])
    else:
        grafana_org.set(organization_name=org_name, organization_status=info['status'], message=body['message'])
    return grafana_org


def grafana_org_delete(module, grafana_url, org_name, org_id, headers):
    # delete organization by id
    uri = '%s/api/orgs/%s' % (grafana_url, org_id)
    r, info = fetch_url(module, url=uri, headers=headers, method='DELETE')
    if r is not None:
        body = json.loads(r.read())
    else:
        body = json.loads(info.get("body", b'{"message": "Organization could not be deleted"}'))

    grafana_org = GrafanaOrganization()
    if info['status'] == 200:
        grafana_org.set(organization_id=org_id, organization_name=org_name, organization_status=info['status'],
                        message=body['message'])
    else:
        grafana_org.set(organization_name=org_name, organization_status=info['status'], message=body['message'])
    return grafana_org


def run_module():
    argument_spec = url_argument_spec()
    del argument_spec['force']
    del argument_spec['force_basic_auth']
    del argument_spec['http_agent']

    argument_spec.update(
        grafana_url=dict(type='str', required=True),
        grafana_username=dict(default='admin'),
        grafana_password=dict(default='admin', no_log=True),
        org_name=dict(type='str', required=True),
        state=dict(choices=['present', 'absent'], default='present'),
    )

    result = dict(
        changed=False,
        msg='',
        org_id='',
        org_name='',
    )

    module = AnsibleModule(
        argument_spec=argument_spec,
        supports_check_mode=True,
        required_together=[['grafana_username', 'grafana_password']]
    )

    try:
        header = grafana_headers(module.params)
        url = module.params['grafana_url']
        org_name = module.params['org_name']
        org_exists = grafana_org_exists(module, url, org_name, header)

        if not module.check_mode:
            if module.params['state'] == 'present':
                if org_exists.organization_id == -1:
                    org_create = grafana_org_create(module, url, org_name, header)
                    result['org_id'] = org_create.organization_id
                    result['org_name'] = org_create.organization_name
                    result['msg'] = org_create.message
                    result['changed'] = True
                else:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Organization exists'
                    result['changed'] = False
            else:
                if org_exists.organization_id != -1:
                    org_delete = grafana_org_delete(module, url, org_name, org_exists.organization_id, header)
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_delete.organization_name
                    result['msg'] = org_delete.message
                    result['changed'] = True
                else:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Organization does not exists'
                    result['changed'] = False
        else:
            if module.params['state'] == 'present':
                if org_exists.organization_id == -1:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Running in check mode...Organization will be created. Organization ID will be ' \
                                    'defined at creation '
                    result['changed'] = True
                else:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Organization already exists'
                    result['changed'] = False
            else:
                if org_exists.organization_id != -1:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Running in check mode...Organization will be deleted.'
                    result['changed'] = True
                else:
                    result['org_id'] = org_exists.organization_id
                    result['org_name'] = org_exists.organization_name
                    result['msg'] = 'Organization does not exists'
                    result['changed'] = False
    except Exception as e:
        module.fail_json(
            failed=True,
            msg="error : %s" % to_text(e)
        )
        return

    module.exit_json(
        failed=False,
        **result
    )
    return


def main():
    run_module()


if __name__ == '__main__':
    main()
