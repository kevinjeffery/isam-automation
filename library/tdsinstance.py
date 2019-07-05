#!/usr/bin/python

import sys
import os
from os.path import expanduser
from ansible.module_utils.basic import AnsibleModule
#from ldif import LDIFParser

class TDSInstance:
  def __init__(self, module):
    self.module = module

  def parse_params(self):
    self.module.debug("*** Process all Arguments")
    self.logLevel = self.module.params['log']
    self.force = self.module.params['force']
    self.action = self.module.params['action']
    self.instance = self.module.params['instance']
    self.tdshome = self.module.params['tdshome']
    self.tdsapi = self.module.params['tdsapi']
    self.tdsfacts = {}
    self._get_facts()
    self.cmd_start = "idsslapd -I {0} -n".format(self.instance)
    self.cmd_stop  = "idsslapd -I {0} -k".format(self.instance)

  def _get_facts(self):
    inst_name = self.instance
    if os.path.exists(self.tdshome) is False:
      self.module.fail_json(changed=False, msg="tdshome doesn't exist")
    ret_value = {}
    idata = self._get_instance_data()
    self.tdsfacts['instances'] = idata
    self.tdsfacts[inst_name] = {}
    if self.instance in idata:
      self.tdsfacts[inst_name]['created'] = True
      config_file = idata[inst_name]['ids-instanceLocation'] + '/idsslapd-' + inst_name + '/etc/ibmslapd.conf'
      self.tdsfacts[inst_name]['config_file'] = config_file
      idata = self._get_config_data()
      self.tdsfacts[inst_name]['config_data'] = idata
    else:
      self.tdsfacts[inst_name]['created'] = False
    
  def get_config(self):
    self.module.exit_json(changed=False, ansible_facts=self.tdsfacts)


  def idsicrt(self):
    inst_name = self.instance
    self.module.debug("*** Create TDS Instance {0}".format(inst_name))
    if self.tdsapi is None:
      self.module.fail_json(changed=False, msg="tdsapi parameters are required")
    if self.tdsfacts[inst_name]['created']:
      self.module.exit_json(changed=False, msg="Instance exists")
    idsicrt_options = " -I " + inst_name
    if 'seed' in self.tdsapi:
      if len(self.tdsapi['seed']) < 12:
        self.module.fail_json(changed=False, msg="Encryption seed must be 12 or more characters")
      idsicrt_options += " -e " + self.tdsapi['seed']
    else:
      idsicrt_options += " -e EncryptionSeedString"
    if 'salt' in self.tdsapi:
      if len(self.tdsapi['salt']) != 12:
        self.module.fail_json(changed=False, msg="Encryption salt must be exactly 12 characters")
      idsicrt_options += " -g " + self.tdsapi['salt']
    if 'port' in self.tdsapi:
      idsicrt_options += " -p " + str(self.tdsapi['port'])
    else:
      idsicrt_options += " -p 389"
    if 'sslport' in self.tdsapi:
      idsicrt_options += " -s " + str(self.tdsapi['sslport'])
    else:
      idsicrt_options += " -s 636"
    if 'admin_port' in self.tdsapi:
      idsicrt_options += " -a " + str(self.tdsapi['admin_port'])
    else:
      idsicrt_options += " -a 3538"
    if 'admin_ssl_port' in idsicrt_options:
      idsicrt_options += " -c " + str(self.tdsapi['admin_ssl_port'])
    else:
      idsicrt_options += " -c 3539"
    if 'location' in self.tdsapi:
      idsicrt_options += " -l " + self.tdsapi['location']
    idsicrt_options += " -t " + self.instance
    if 'desc' in self.tdsapi:
      idsicrt_options += " -r \"" + self.tdsapi['desc'] + "\""
    if 'ip_addr' in self.tdsapi:
      idsicrt_options += " -i " + self.tdsapi['ip_addr']
    else:
      idsicrt_options += " -i all"
    cmd = "idsicrt"  + idsicrt_options + " -n -q"
    rc, stdout, stderr = self._sbin_command(cmd, "Failed to create instance {0}".format(self.instance))
    self.module.exit_json(changed=True, rc=rc, stdout=stdout, stderr=stderr)

  def idscfgdb(self):
    inst_name = self.instance
    self.module.debug("*** Configure TDS Database {0}".format(inst_name))
    if self.tdsapi is None:
      self.module.fail_json(changed=False, msg="tdsapi parameters are required")
    location = self.tdsfacts['instances'][inst_name]['ids-instanceLocation']
    idscfgdb_options = " -I " + inst_name + " -a " + inst_name + " -t " + inst_name
    if 'dblocation' in self.tdsapi:
      location = self.tdsapi['dblocation']
    db_dir = location + "/" + inst_name + "/NODE0000"
    if os.path.exists(db_dir):
      self.module.exit_json(changed=False, msg="Database is configured")
    if 'password' in self.tdsapi:
      idscfgdb_options += " -w \"" + self.tdsapi['password'] + "\""
    else:
      self.module.fail_json(changed=False, msg="Instance password is required")
    idscfgdb_options += " -l " + location
    if 'storage' in self.tdsapi:
      idscfgdb_options += " -s " + self.tdsapi['storage']
    cmd  = "idscfgdb" + idscfgdb_options + " -n -q"
    rc, stdout, stderr = self._sbin_command(cmd, "Failed to configure database", ignore_stderr=True)
    self.module.exit_json(changed=True, rc=rc, stdout=stdout, stderr=stderr)

  def idsdnpw(self):
    inst_name = self.instance
    self.module.debug("*** Set Admin DN Instance {0}".format(inst_name))
    idsdnpw_options = " -I " + inst_name
    if self.tdsapi is None:
      self.module.fail_json(changed=False, msg="Error, tdsapi parameters are required")
    if self._instance_up():
      self.module.fail_json(changed=False, msg="Error, cannot change Admin DN password when instance up")
    if 'admin_id' in self.tdsapi:
      idsdnpw_options += " -u " + self.tdsapi['admin_id']
    else:
      idsdnpw_options += " -u cn=root"
    if 'admin_pw' in self.tdsapi:
      idsdnpw_options += " -p \"" + self.tdsapi['admin_pw'] + "\""
    else:
      self.module.fail_json(changed=False, msg="Administrator password is required")
    cmd   = "idsdnpw"  + idsdnpw_options + " -n -q"
    rc, stdout, stderr = self._sbin_command(cmd, "Failed to set Admin DN and password")
    self.module.exit_json(changed=True, rc=rc, stdout=stdout, stderr=stderr)

  def idscfgsuf(self):
    inst_name = self.instance
    self.module.debug("*** Set Admin DN Instance {0}".format(inst_name))
    idscfgsuf_options = " -I " + inst_name
    if self.tdsapi is None:
      self.module.fail_json(changed=False, msg="tdsapi parameters are required")
    if 'suffix' in self.tdsapi:
      suffix = self.tdsapi['suffix']
      idscfgsuf_options += " -s " + suffix
    else:
      self.module.fail_json(changed=False, msg="Error, suffix is required")
    if self._instance_up():
      self.module.fail_json(changed=False, msg="Error, suffixes cannot be changed while instance is up")
    config_entry = "cn=Directory, cn=RDBM Backends, cn=IBM Directory, cn=Schemas, cn=Configuration"
    config_attr = "ibm-slapdSuffix"
    if self._has_config_value(config_entry, config_attr, suffix):
      self.module.exit_json(changed=False, msg="Suffix {0} is configured".format(suffix))
    cmd = "idscfgsuf" + idscfgsuf_options + " -n -q"
    rc, stdout, stderr = self._sbin_command(cmd, "Failed to configure suffix {0}".format(suffix))
    self.module.exit_json(changed=True, rc=rc, stdout=stdout, stderr=stderr)

  def start(self):
    inst_name = self.instance
    self.module.debug("*** Start {0}".format(inst_name))
    if not self._instance_up():
      rc, stdout, stderr = self._sbin_command(self.cmd_start, "Error, could not start instance {0}".format(inst_name), ignore_stderr=True)
      self.module.exit_json(changed=True, msg="Instance {0} started".format(self.instance),stderr=stderr, rc=rc, stdout=stdout)
    else:
      self.module.exit_json(changed=False, msg="Instance {0} running".format(inst_name))

  def stop(self):
    inst_name = self.instance
    self.module.debug("*** Stop instance {0}".format(inst_name))
    if self._instance_up():
      # Stop the instance
      rc, stdout, stderr = self._sbin_command(self.cmd_stop, "Error, could not stop {0} instance".format(inst_name), ignore_stderr=True)
      self.module.exit_json(changed=True, msg="Instance stopped",stderr=stderr, rc=rc, stdout=stdout)
    else:
      self.module.exit_json(changed=False, msg="Instance {0} not running".format(inst_name))

  def restart(self):
    inst_name = self.instance
    self.module.debug("*** Restart {0}".format(self.instance))
    if self._instance_up():
      # Stop the instance
      rc, stdout, stderr = self._sbin_command(self.cmd_stop, "Error, could not stop {0} instance".format(inst_name))
    rc, stdout, stderr = self._sbin_command(self.cmd_start, "Error, cound not restart {0} instance".format(inst_name), ignore_stderr=True)
    self.module.exit_json(changed=True, msg="Instance {0} restarted".format(inst_name),stderr=stderr, rc=rc, stdout=stdout)

  def _get_instance_data(self):
    idsinstances = os.path.split(self.tdshome)[0] + "/idsinstinfo/idsinstances.ldif"
    self.tdsfacts['idsinstances.ldif'] = {'path': idsinstances}
    ldif_entries = self._parse_ldif(idsinstances)
    ret_value = {}
    for entry in ldif_entries:
      isInstance = False
      cn = ''
      instance = {}
      for attr in entry:
        attrname = attr['name']
        if attrname == 'cn':
          cn = attr['value']
        if attrname == 'objectClass':
          if attr['value'] == 'ids-instance':
            isInstance = True
          continue
        instance[attrname] = attr['value']
      if isInstance:
        ret_value[cn] = instance
    return ret_value
    
  def _get_config_data(self):
    inst_name = self.instance
    ldif_entries = self._parse_ldif(self.tdsfacts[inst_name]['config_file'])
    ret_value = {}
    for entry in ldif_entries:
      attrlast = ''
      dn = ''
      config_entry = {}
      values = []
      for attr in entry:
        attrname = attr['name']
        attrvalue = attr['value']
        if attrname == 'dn':
          dn = attrvalue
        if attrname == attrlast:
          values.append(attrvalue)
          continue
        else:
          if attrlast == '':
            values = []
            attrlast = attrname
            values.append(attrvalue)
          else:
            if len(values) == 1:
              config_entry[attrlast] = values[0]
            else:
              config_entry[attrlast] = values
            values = []
            attrlast = attrname
            values.append(attrvalue)
        if attrname == 'objectClass':
          continue
      if dn:
        ret_value[dn] = config_entry
    return ret_value

  def _parse_ldif(self, filepath):
    """
    Parse LDIF at given filepath
    Parameters
    ----------
    filepath : str
        Filepath for file to be parsed
    Returns
    -------
    data : list of entries containing list of attribute data {'name':attrname, 'value':attrvalue}
    """
    data = []
    linecount = 0
    entrycount = 0
    with open(filepath, 'rt') as file:
      # Read the first line
      line = file.readline()
      while line: # not EOF
        # check for line starting with dn:
        if not ":" in line:
          line = file.readline()
          continue
        if line.lower().startswith("dn:"):
          # process the entry
          entry = []
          while line: # not EOF
            if line.startswith('#'): # skip comments
              line = file.readline()
              continue
            if ":" in line:
              attrname, attrvalue = line.split(':', 1)
              entry.append({'name': attrname, 'value': attrvalue.strip().rstrip('\n')})
            if line == '\n':
              data.append(entry)
              break
            line = file.readline()
        if line:
          line = file.readline()
      # wend
      file.close()
      return data

  def _sbin_command(self, cmd, error_msg, ignore_stderr=False):
    sbin = self.tdshome + "/sbin/"
    rc, stdout, stderr = self.module.run_command(sbin + cmd, executable="/usr/bin/ksh", use_unsafe_shell=True)
    if ignore_stderr:
      stderr = ''
    if stderr != '' or rc!=0:
      self.module.fail_json(changed=False, msg=error_msg, stderr=stderr, rc=rc, stdout=stdout)
    return rc, stdout, stderr

  def _run_command(self, cmd, error_msg, ignore_stderr=False):
    sbin = self.tdshome + "/sbin/"
    rc, stdout, stderr = self.module.run_command(cmd, executable="/usr/bin/ksh", use_unsafe_shell=True)
    if ignore_stderr:
      stderr = ''
    if stderr != '' or rc!=0:
      self.module.fail_json(changed=False, msg=error_msg, stderr=stderr, rc=rc, stdout=stdout)
    return rc, stdout, stderr

  def _instance_up(self):
    cmd = "ps -u {0} | grep -q ibmslapd".format(self.instance)
    rc, stdout, stderr = self.module.run_command(cmd, executable="/usr/bin/ksh", use_unsafe_shell=True)
    return rc == 0

  def set_config(self, attribute):
    # attribute is a dict: {dn: <dn>, attrname: <attrname>, attrvalue: <str or list of str>}
    # check current values by iterating lists of values both ways.
    # if changed, create a mod ldif either delete extra values or add new values on multi value.
    # if attribute is single valued, do a replace
    # call ldap modify
    #dn = attribute['dn']
    #name = attribute['attrname']
    #value = attribute['attrvalue']
    self.module.fail_json(changed=False, msg=str(attribute))
    
  def add_config(self,attribute):
    # attribute is a dict as above and attrvalue is always string
    # create mod ldif with add values
    self.module.fail_json(changed=False, msg=str(attribute))
    
  def del_config(self,attribute):
    # attribute is a dict as above and attrvalue is always a string
    # create mod ldif with delete value
    self.module.fail_json(changed=False, msg=str(attribute))

  def _has_config_value(self, entry_dn, attr_name, attr_value):
    inst_name = self.instance
    ret_value = False
    if entry_dn in self.tdsfacts[inst_name]['config_data']:
      if attr_name in self.tdsfacts[inst_name]['config_data'][entry_dn]:
        attr_values = self.tdsfacts[inst_name]['config_data'][entry_dn][attr_name]
        if isinstance(attr_values, list):
          for value in attr_values:
            if value.lower() == attr_value.lower():
              ret_value = True
              break
        else:
          if attr_values.lower() == attr_value.lower():
            ret_value = True
    return ret_value

def main():
    module = AnsibleModule(
        argument_spec=dict(
            log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
            instance=dict(required=True, type='str'),
            action=dict(required=True, type='str'),
            force=dict(required=False, default=False, type='bool'),
            tdshome=dict(required=False, default='/opt/ibm/ldap/V6.4', type='str'),
            tdsapi=dict(required=False, type='dict')
        ),
        supports_check_mode=False
    )

    module.debug('Started db2instance module')
    
    tdsinst = TDSInstance(module)
    tdsinst.parse_params()

    if tdsinst.action == "get_config":
      tdsinst.get_config()

    if tdsinst.action == "idsicrt":
      tdsinst.idsicrt()
    
    if tdsinst.action == "idsdnpw":
      tdsinst.idsdnpw()
    
    if tdsinst.action == "idscfgdb":
      tdsinst.idscfgdb()
    
    if tdsinst.action == "idscfgsuf":
      tdsinst.idscfgsuf()
    
    if tdsinst.action == "idsucfgdb":
      tdsinst.idsucfgdb()
    
    if tdsinst.action == "start":
      tdsinst.start()
    
    if tdsinst.action == "stop":
      tdsinst.stop()

    if tdsinst.action == "restart":
      tdsinst.restart()
    
    if tdsinst.action == "set_config":
      if 'tdsapi' in module.params:
        if 'config_settings' in tdsinst.tdsapi:
          tdsinst.set_config(tdsinst.tdsapi['config_settings'])
        else:
          module.fail_json(changed=False, msg="Error, config_settings is required")
      else:
        module.fail_json(changed=False, msg="Error, tdsapi is required")

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(tdsinst.action))

if __name__ == '__main__':
  main()
