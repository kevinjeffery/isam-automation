# gskit Role
The gskit role is automates the installation of upgrade of IBM Global Security Kit (GSKit).
GSKit is required for IBM DB2 and IBM Security Directory Server (ISDS) if you plan on using SSL or TLS.
The gskit role automates 4 tasks:
- Stage the software archive on the target server.
- Extract the archive.
- Install the 64 bit components.
- Install the 32 bit components.

Override these two variables using group or host settings for the current gskit fixpack version:
- gskit_install_version:  "8.0.50.89"
- gskit_install_suffix: "FP0089"
