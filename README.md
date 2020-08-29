# isam-automation
Ansible automation for IBM Security Access Manager

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
## Sample Inventory and Playbooks for building and automating ISAM
* [Sample Ansible Control server on CentOS 7](#ansible-control-server)
* Playbook to install ISDS and dependencies (GSKit, JavaSDK, DB2)
* Playbook to configure the ISAM ISDS instance
* Playbook to build ISAM Virtual Appliances on a stand-alone ESXi host
* [Ansible module to manage VMs on a stand-alone ESXi host](#esxi-module)

## Ansible Control Server
The inventory and playbooks to support building an Ansible control server on an existing CentOS 7 server and install packages and roles required for the IBM Security Python Library and Ansible Roles.

[Ansible Control Server](https://techlink.microknight.com/2019/06/23/ansible-control-system-for-isam/)

## ESXi Module
Ansible module for creating and controlling VMs on Stand-Alone ESXI.

[Ansible ESXi Module](https://techlink.microknight.com/2019/11/19/ansible-esxi-module/)

## HVDB Cleanup
Cleanup scripts and procedures for the ISAM External HVDB Database on DB2.

[ISAM HVDB Cleanup](https://techlink.microknight.com/2020/08/29/isam-hvdb-cleanup/)

## License

The contents of this repository are open-source under the Apache 2.0 licence.

```
Copyright 2019-2020 Kevin Jeffery

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
```