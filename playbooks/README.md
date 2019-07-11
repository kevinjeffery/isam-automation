# Playbooks
Sample playbooks for building the Tutorial environment with some enhancements for specific usage patterns.

| Playbook | Description |
| --- | --- |
| ansible_control_4_isam.yml | This playbook builds out an Ansible control server for the ISAM automation plays.
| isds_installation.yml | Playbook to install IBM Security Directory Server v6.4 and pre-requisites
| isamldap_instance.yml | Playbook to automate the creation and configuration of the ISDS instance for ISAM

## ansible_control_4_isam.yml
This playbook assumes a minimal Linux server installation, so the first step is to install some useful packages.  You can define your own list of what you find useful, but I installed "open-vm-tools", "bind-utils", "unzip" and "rsync" in the sample inventory.
The next step is to install pip using the package manager and then use it to update itself to the current version.
The latest version of the IBM Security Python Library is installed next from Git Hub.
To make use of the Ansible server for configuration of the ISDS LDAP server, I install the dependent packages required for python-ldap, the Open LDAP clients for troubleshooting and then python-ldap.  This step simplifies the deployment of ISDS by not 
requiring python-ldap on the target server.  If you would rather install python-ldap on the ISDS server (or are required to do so), you will have to edit the tasks in the isamldap role to remove the delegate: localhost entries.
The last task in the playbook is the install/update of the IBM Security Ansible roles for ISAM. 

## isds_installation.yml
This playbook is responsible for installation of the ISDS software, fixpack and its dependencies.  The process is loosely based on the support document for DB2 11.1 support in ISDS: https://www-01.ibm.com/support/docview.wss?uid=ibm10792557.  The software binaries can come from either a URL or the file system of the Ansible Server.

## isamldap_instance.yml
This playbook automates the configuration of the ISAM ISDS instance with most command line options supported.

Credits
---------------------
The initial idea for the ISDS installation and configuration came from work done by Bernardo Vale.
https://github.com/bernardoVale/ansible-role-db2