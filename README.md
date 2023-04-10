netbox-kea-dhcp
===============

Connector enabling continuous one-way synchronisation from
[NetBox](https://github.com/netbox-community/netbox) to
[ISC Kea DHCP server](https://www.isc.org/kea/).

NetBox prefixes, IP ranges and combo IP addresses + (vm)interfaces are
respectively exported to DHCP subnets, pools and host reservations.

The connector has two modes of operation:

- Full sync: overwrite current DHCP subnets with new ones exported
  from NetBox.
- Continuous event-driven sync: listen for NetBox webhook events and update
  DHCP configuration accordingly.

Requirements
------------

Python: >= 3.8 (developped on 3.10 but may works down to 3.7).

Netbox: developped for version 3.4.

ISC Kea DHCP: developped for version 2.2.0.

Install
-------

To install run `pip install netbox-kea-connector`.

Alternatively you may clone this repo and run
`python install dist/netbox-kea-connector-VERSION-py3-none-any.whl`.

A virtual environnement is highly recommended:
```sh
python3 -m venv /usr/local/netbox-kea-connector
/usr/local/netbox-kea-connector/bin/pip install --upgrade pip
```

Quick start
-----------

Sync at startup then listen for netbox events:
```sh
netbox-kea-dhcp --netbox-url http://netbox-host \
    --netbox-token 9123456789abcdef0123456789abcdef01234568 \
    --kea-url http://kea-api-host --sync-now --listen -v
```

At least one Netbox webhook needs to be configured for event listening. It has
to notify all actions on DHCP-relevant objects:

- Content types:
  * `IPAM`: `Prefix`, `IP Range`, `IP addresse`.
  * `DCIM`: `Interface`, `Device`.
  * `Virtualization`: `Interface`, `Virtual Machine`.
- Events: `Creations`, `Updates`, `Deletions`.
- HTTP Request:
  * URL: `http://{netbox-connector-host}:{port}/event/{optional-free-text}`
  * HTTP Method: `POST`.

The field `optional-free-text` permits to define several webhooks with same
events. The connector only uses it in logs.

It’s however recommended to set several webhooks with conditions, in order to
filter events and avoid unecessary network and parsing load. Example:

Event 1:

- Content types: `IPAM > Prefix`, `IPAM > IP Range`, `IPAM > IP Address`,
  `DCIM > Device`, `DCIM > Interface`, `Virtualization > Virtual Machine`,
  `Virtualization > Interface`.
- Events: `Updates`
- Conditions: none

Event 2:

- Content types: `IPAM > IP Address`
- Events: `Creations`, `Deletions`
- Conditions:

    ```json
    { "and": [
      { "attr": "status.value", "value": "dhcp" },
      {
        "attr": "assigned_object_type",
        "value": [ "dcim.interface", "virtualization.vminterface" ],
        "op": "in"
      }
    ] }
    ```

Event 3:

- Content types: `IPAM > IP Range`
- Events: `Creations`, `Deletions`
- Conditions (note: you may have to customize status values to add `dhcp`):

    ```json
    { "and": [ { "attr": "status.value", "value": "dhcp"} ] }
    ```

Event 4:

- Content types: `IPAM > Prefix`
- Events: `Creations`, `Deletions`
- Conditions: none, or a custom field

    ```json
    { "and": [ { "attr": "custom_fields.dhcp_enabled", "value": true } ] }
    ```

It’s also recommended to set a TLS-enabled reverse proxy in front of
`netbox-kea-dhcp`.

Contribute
----------

### Unit tests

```sh
cd /path/to/repo
python -m unittest -v
[…]
----------------------------------------------------------------------
Ran xxx tests in 0.123s

OK
```
