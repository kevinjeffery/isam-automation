# tds Role
The tds role automates the deployment and installation of ISDS by performing the following tasks:
- Create the required ISDS instance users.
- Disable the DB2 prerequisite check for when DB2 v11.1 will be used.
- Deploy the ISDS GA ISO image to the target system.
- Deploy and extract the current fixpack.
- Mount the ISO image.
- Install the ISDS license and binaries.
- Update the license and install the fixpack when required.
- Template the ldapdb.properties file for the installed DB2 version.
- Unmount the ISO image.
