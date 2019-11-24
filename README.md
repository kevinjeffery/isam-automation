# isam-automation
Ansible automation for IBM Security Access Manager

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
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

