# Playbooks

Sample playbooks for building the Tutorial environment with some enhancements for specific usage patterns.  
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)

| Playbook | Description |
| --- | --- |
| [ansible_control_4_isam.yml](#ansiblecontrol4isam) | This playbook builds out an Ansible control server for the ISAM automation plays. |
| [isds_installation.yml](#isdsinstallation) | Playbook to install IBM Security Directory Server v6.4 and pre-requisites |
| [isamldap_instance.yml](#isamldapinstance) | Playbook to automate the creation and configuration of the ISDS instance for ISAM |
| [winrm_kerberos_installation.yml](#winrmkerberosinstallation) | Playbook to automate the installation of WinRM Kerberos libraries and wrapper |
| [winrm_kerberos_configuration.yml](#winrmkerberosconfiguration) | Playbook to configure the Kerberos client for WinRM kerberos authentication |

<!-- markdownlint-disable MD033 -->
<a id="ansiblecontrol4isam" name="ansiblecontrol4isam"></a>
<!-- markdownlint-enable MD033 -->

## ansible_control_4_isam.yml

This playbook assumes a minimal Linux server installation, so the first step is to install some useful packages.  You can define your own list of what you find useful, but I installed "open-vm-tools", "bind-utils", "unzip" and "rsync" in the sample inventory.
The next step is to install pip using the package manager and then use it to update itself to the current version.
The latest version of the IBM Security Python Library is installed next from Git Hub.
To make use of the Ansible server for configuration of the ISDS LDAP server, I install the dependent packages required for python-ldap, the Open LDAP clients for troubleshooting and then python-ldap.  This step simplifies the deployment of ISDS by not 
requiring python-ldap on the target server.  If you would rather install python-ldap on the ISDS server (or are required to do so), you will have to edit the tasks in the isamldap role to remove the delegate: localhost entries.
The last task in the playbook is the install/update of the IBM Security Ansible roles for ISAM. 

<!-- markdownlint-disable MD033 -->
<a id="isdsinstallation" name="isdsinstallation"></a>
<!-- markdownlint-enable MD033 -->

## isds_installation.yml

This playbook is responsible for installation of the ISDS software, fixpack and its dependencies.  The process is loosely based on the support document for DB2 11.1 support in ISDS: https://www-01.ibm.com/support/docview.wss?uid=ibm10792557.  The software binaries can come from either a URL or the file system of the Ansible Server.

<!-- markdownlint-disable MD033 -->
<a id="isamldapinstance" name="isamldapinstance"></a>
<!-- markdownlint-enable MD033 -->

## isamldap_instance.yml

This playbook automates the configuration of the ISAM ISDS instance with most command line options supported.

<!-- markdownlint-disable MD033 -->
<a id="esxiisamva" name="esxiisamva"></a>
<!-- markdownlint-enable MD033 -->

## esxi_isamva.yml

This playbook automates provisioning of the ISAM Virtual Appliance on ESXi standalone.  Tested on ESXi v6.5.  The playbook expects the ESXi server to be in the esxi hosts group and have ssh connectivity enabled (the free license only has a readonly rest API).
See the sample.yml inventory file for the variables used in the play.  Up to three network interfaces supported by the template file.

<!-- markdownlint-disable MD033 -->
<a id="esxiisamvatemplate" name="esxiisamvatemplate"></a>
<!-- markdownlint-enable MD033 -->

### esxi_isamva_template.yml

This tasks file is called for each item in the isamva_list variable to create the autoconfig metadata file, the autoconfig ISO image and the VM vmx file.  All ISO image files are copied to the ESXi server along with the ISAM Firmware ISO image.

<!-- markdownlint-disable MD033 -->
<a id="esxiisamvaprovision" name="esxiisamvaprovision"></a>
<!-- markdownlint-enable MD033 -->

### esxi_isamva_provision.yml

This tasks file is called for each item in the isamva_list variable to create the VM directory, transfer the vmx file, create the virtual disk, register the VM and power it on to install the firmware.  There is a three minute delay at the end of the file to allow the firmware installation to complete and power off.

<!-- markdownlint-disable MD033 -->
<a id="esxiisamvaautoconfig" name="esxiisamvaautoconfig"></a>
<!-- markdownlint-enable MD033 -->

### esxi_isamva_autoconfig.yml

This tasks file is called for each item in the isamva_list variable to swap the ISAM firmware ISO for the autoconfig ISO on a powered off VM.  If the VM is powered off AND the image is swapped, the VM is powered back on to apply the configuration.

<!-- markdownlint-disable MD033 -->
<a id="winrmkerberosinstallation" name="winrmkerberosinstallation"></a>
<!-- markdownlint-enable MD033 -->

### winrm_kerberos_installation.yml

This playbook installs the WinRM libraries and Python wrapper required for Kerberos Authentication to Windows servers.  Currenty RedHat 7, CentOS 7, Debian and Ubuntu are support.  The dependecies for both Python 2 and Python 3 are installed.  



<!-- markdownlint-disable MD033 -->
<a id="winrmkerberosconfiguration" name="winrmkerberosconfiguration"></a>
<!-- markdownlint-enable MD033 -->

### winrm_kerberos_configuration.yml

Playbook to configure to Kerberos client for a specific MSAD domain.  The playbook assumes that the winrm_kerberos_config variable is defined as shown below:

```yaml
winrm_kerberos_config:
  domain: "sample.com"
  kdc:
  - "dc1.sample.com"
  - "dc2.sample.com"
```

Credits
---------------------
The initial idea for the ISDS installation and configuration came from work done by Bernardo Vale.
https://github.com/bernardoVale/ansible-role-db2

The initial idea for the ESXi Standalone automation came from the bootstrap_local role in the IBM Security Ansible Roles for ISAM.
https://github.com/IBM-Security/isam-ansible-roles/tree/master/bootstrap_local
