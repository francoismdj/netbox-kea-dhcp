netbox-kea-dhcp
===============

Enable use of [NetBox](https://github.com/netbox-community/netbox) as a subnet
configuration source for [ISC Kea DHCP server](https://www.isc.org/kea/).

`netbox-kea-dhcp` is a one-way sync daemon that exports NetBox prefixes, IP
ranges and IP addresse/interface pairs to respectively DHCP subnets, pools
and host reservations. It listens for NetBox webhook events, and each time a
change occured, it queries NetBox for the full changed data and update Kea
throught its API.

The program has two modes of operation:

- Full sync at program startup: overwrite current DHCP subnets with new ones
  exported from NetBox.
- Continuous event-driven sync: listen for NetBox webhook events and update
  DHCP configuration accordingly.

Key features
------------

- Automatic sync from Netbox to Kea DHCP with virtualy no delay.
- Update Kea configuration throught its control agent API: no direct
  configuration file overwrites, let’s the control agent manage the runtime
  and permanent configuration.
- Only use open source Kea API commands (no ISC paid subscription required).
- Submit new exported configuration to Kea check before applying it to runtime
  configuration.
- Query NetBox only for the objects concerned by the event (incremental
  sync).
- Get all NetBox data throught the well maintained
  [`pynetbox`](https://github.com/netbox-community/pynetbox) library: unique
  interface, loose dependency with NetBox internals (only with its API),
  reduced code to maintain.
- Customizable NetBox query filters.
- Customizable mapping between Netbox prefix fields and subnets options.

Requirements
------------

Python: >= 3.8 (developped on 3.10 but may works down to 3.7).

Netbox: developped for API version 3.4.

ISC Kea DHCP: developped for version 2.2.0.

Install
-------

### With pip

`netbox-kea-dhcp` is available on
[PyPi](https://pypi.org/project/netbox-kea-dhcp/) and can be installed
with `pip install netbox-kea-dhcp`.

### With pipx

A convenient way is to use [pipx](https://pypa.github.io/pipx/) to install the
application in an isolated environnement.

Install `pipx` (below is for Linux, see
[pipx homepage](https://pypa.github.io/pipx/) for other systems):

```sh
python3 -m pip install --user pipx
python3 -m pipx ensurepath
```

Install `netbox-kea-dhcp` from PyPi in a isolated environnement:

```sh
pipx install netbox-kea-dhcp
```

Run:

```
netbox-kea-dhcp --help
```

Quick start
-----------

Sync at startup then listen for netbox events:
```sh
netbox-kea-dhcp --netbox-url http://netbox-host \
    --netbox-token 0123456789ABCDEF \
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
  * URL: `http://{netbox-connector-host}:{port}/event/{free-text}/`
  * HTTP Method: `POST`.

The field `free-text` is necessary to define several webhooks with same events.
The connector only uses it in logs.

More help with `netbox-kea-dhcp --help` and in the configuration file example
under `examples/` (or under
`~/.local/pipx/venvs/netbox-kea-dhcp/lib/python3.10/site-packages/examples/` if
app was installed with pipx).

Recommended Netbox webhooks
---------------------------

It’s recommended to set several webhooks with conditions and restricted body
template, in order to filter events and avoid unecessary network and CPU load:

Common to all webhooks:

- HTTP Request:
  * URL: `http://{netbox-connector-host}:{port}/event/{optional-free-text}/`
  * HTTP Method: `POST`.
- Body template:

    ```json
    { "event": "{{ event }}",
      "model": "{{ model }}",
      "data": { "id": {{ data["id"] }} }
    }
    ```

Webhook 1:

- Content types: `IPAM > Prefix`, `IPAM > IP Range`, `IPAM > IP Address`,
  `DCIM > Device`, `DCIM > Interface`, `Virtualization > Virtual Machine`,
  `Virtualization > Interface`.
- Events: `Updates`
- Conditions: none

Webhook 2:

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

Webhook 3:

- Content types: `IPAM > IP Range`
- Events: `Creations`, `Deletions`
- Body template: `{"event": event, "model": model, "data": {"id": data["id"]}}`
- Conditions (note: you may have to customize status values to add `dhcp`):

    ```json
    { "and": [ { "attr": "status.value", "value": "dhcp"} ] }
    ```

Webhook 4:

- Content types: `IPAM > Prefix`
- Events: `Creations`, `Deletions`
- Body template: `{"event": event, "model": model, "data": {"id": data["id"]}}`
- Conditions: none, or a custom field

    ```json
    { "and": [ { "attr": "custom_fields.dhcp_enabled", "value": true } ] }
    ```

It’s also recommended to set a TLS-enabled reverse proxy in front of
`netbox-kea-dhcp`.

Limitations
-----------

- When a change occured, the whole DHCP configuration is gotten from Kea,
  modified, and sent back. This is a limitation of Kea open source commands. A
  better update granularity would require an ISC paid subscription.
- Every event received triggers one or more queries to Netbox, even if event
  payload holds the information. This allows to have a unique  point where
  filters are applied and attributes are read.
- Kea internal subnet `id` keys are not preserved, as they induce conflicts
  when configuration is pushed back to the DHCP server.
- When Kea URI is of the form `file:///path/to/kea-config`, config is written
  to the file in an unsafe manner: if the write fails, the file will be
  inconsistent. This is because the file feature was coded for testing purpose.
