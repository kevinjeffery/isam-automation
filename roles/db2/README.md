# db2 Role
The db2 role automates the installation of IBM DB2.  This role has been tested with DB2 v10.5 (Starting with the verion specified in the defaults/main.yml file) and DB2 v11.1.
The following tasks are automated:
- Stage the DB2 binary either from a URL or the Ansible control system to the target system.
- Stage the license file(s) to the target system.
- Extract the binary and license archives.
- Install dependent packages for the target operating system.
- Create any required DB2 Instance and Fenced users
- Disable SELinux on Redhat family operating systems (includes CentOS).
- Ensure the target system IP address and hostname are present in the /etc/hosts file
- Run the DB2 pre-requisite check.
- Create a custom installation response file from the template.
- Install DB2 using the response file.
- License DB2.
- Add the High Capacity license if required (DB2 11.1 only).
- Template the DB2 Fault Monitor service unit file.
- Enable the DB2 Fault Monitor service.
