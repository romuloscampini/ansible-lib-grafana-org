# Ansible Library: Grafana Organization
Create, update and delete Grafana Organization

Example:

- Create organization
```
- name: create grafana organization
  grafana_org:
    grafana_url: "http://localhost:3000"
    grafana_username: "admin"
    grafana_password: "admin"
    org_name: "example"
    state: present
```

- Delete organization
```
- name: delete grafana organization
  grafana_org:
    grafana_url: "http://localhost:3000"
    grafana_username: "admin"
    grafana_password: "admin"
    org_name: "example"
    state: absent

```

Return:
```
{"changed": true, "msg": "Organization created", "org_id": 1, "org_name": "example"}
```
