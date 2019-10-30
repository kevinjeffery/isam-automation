#!/usr/bin/python

import sys
import os
from os.path import expanduser
from ansible.module_utils.basic import AnsibleModule

class DB2Instance:
  def __init__(self, module):
    self.module = module
    self.facts = {}

  def parse_params(self):
    self.module.debug("*** Process all Arguments")
    self.logLevel = self.module.params['log']
    self.force = self.module.params['force']
    self.action = self.module.params['action']
    self.instance = self.module.params['instance']
    self.db2profile = self._find_db2_profile()
    self.db2home = self.module.params['db2home']
    self.db2port = self.module.params['db2port']

  def create(self):
    self.module.debug("*** Create DB2 Instance {0}".format(self.instance))
    if os.path.exists(self.db2profile):
      self.module.exit_json(changed=False, msg="Instance exists")
    if self.db2home is None or os.path.exists(self.db2home) is False:
      self.module.fail_json(changed=False, msg="db2home not defined or doesn't exist")
    cmd = "{0}/instance/db2icrt -p {1} -u {2} {2}".format(self.db2home, self.db2port, self.instance)
    rc, stdout, stderr = self.module.run_command(cmd, executable="/usr/bin/ksh", use_unsafe_shell=True)
    if stderr != '' or rc!=0:
      self.module.fail_json(changed=False, msg="Error, could not create instance", stderr=stderr, rc=rc, stdout=stdout)
    self.module.exit_json(changed=True, msg=cmd, rc=rc, stderr=stderr, stdout=stdout)

  def start(self):
    self.module.debug("*** Start {0}".format(self.instance))
    if not self._instance_up():
      self.module.debug("*** Starting {0} DB2 Instance".format(self.instance))
      rc, stdout, stderr = self._db2_command("db2start", "Error, could not start the instance")
      self.module.exit_json(changed=True, msg="Instance started",stderr=stderr, rc=rc, stdout=stdout)
    else:
      self.module.exit_json(changed=False, msg="Instance running")

  def stop(self):
    self.module.debug("*** Stop {0}".format(self.instance))
    if self._instance_up():
      # Stop the instance
      cmd = "db2stop"
      if self.force:
        cmd += " force"
      self.module.debug("*** Stopping {0} DB2 Instance".format(self.instance))
      rc, stdout, stderr = self._db2_command(cmd, "Error, could not stop the instance")
      self.module.exit_json(changed=True, msg="Instance stopped",stderr=stderr, rc=rc, stdout=stdout)
    else:
      self.module.exit_json(changed=False, msg="Instance not running")

  def restart(self):
    self.module.debug("*** Restart {0}".format(self.instance))
    if self._instance_up():
      # Stop the instance
      cmd = "db2stop"
      if self.force:
        cmd += " force"
      self.module.debug("*** Stopping {0} DB2 Instance".format(self.instance))
      rc, stdout, stderr = self._db2_command(cmd, "Error, could not stop the instance")
    cmd = "db2start"
    self.module.debug("*** Restarting {0} DB2 Instance".format(self.instance))
    rc, stdout, stderr = self._db2_command(cmd, "Error, cound not restart the instance")
    self.module.exit_json(changed=True, msg="Instance restarted",stderr=stderr, rc=rc, stdout=stdout)

  def enable_auto(self):
    self.module.debug("*** Enable Instance Autostart")
    cmd = "db2iauto on {0}".format(self.instance)
    rc, stdout, stderr = self._db2_command(cmd, "Error, cound not enable autostart instance")
    self.module.exit_json(changed=True, msg="Autostart enabled",stderr=stderr, rc=rc, stdout=stdout)

  def disable_auto(self):
    self.module.debug("*** Enable Instance Autostart")
    cmd = "db2iauto off {0}".format(self.instance)
    rc, stdout, stderr = self._db2_command(cmd, "Error, cound not disable autostart instance")
    self.module.exit_json(changed=True, msg="Autostart disabled",stderr=stderr, rc=rc, stdout=stdout)


  def get_dbm_cfg(self):
    self.module.debug("*** Get DBM CFG: {0}".format(self.instance))
    config_items = self._get_dbm_cfg_items()
    lineout = "Items {0}".format(len(config_items))
    self.module.exit_json(changed=False, msg="DBM Config: " + lineout, ansible_facts=self.facts)

  def getenv(self):
    self.module.debug("*** Get DBM CFG: {0}".format(self.instance))
    config_items = self._getenv_items()
    lineout = "Items {0}".format(len(config_items))
    self.module.exit_json(changed=False, msg="DBM Config: " + lineout, ansible_facts=self.facts)

  def set_dbm_cfg(self, name, value):
    cmd = "db2 update dbm cfg using {0} {1}".format(name, value)
    self.module.debug(cmd)
    if not "db2_dbm_cfg" in self.facts:
      self._get_dbm_cfg_items()
    if self._check_cfg("db2_dbm_cfg", name, value):
      self.module.exit_json(changed=False, msg=cmd + " OK")
    rc, stdout, stderr = self._db2_command(cmd, cmd + " Failed")
    self.module.exit_json(changed=True, msg=cmd + " Success", rc=rc, stdout=stdout, stderr=stderr)

  def setenv(self, name, value):
    cmd = "db2set {0}={1}".format(name, value)
    self.module.debug(cmd)
    if not "db2set" in self.facts:
      self._getenv_items()
    if self._check_cfg("db2set",name,value):
      self.module.exit_json(changed=False, msg=cmd + " OK")
    rc, stdout, stderr = self._db2_command(cmd, cmd + " Failed")
    rc, stdout, stderr = self.module.exit_json(change=True, msg=cmd + " Success", rc=rc, stdout=stdout, stderr=stderr)

  def _check_cfg(self, fact_name, item_name, item_value=None):
    if fact_name in self.facts:
      for item in self.facts[fact_name]:
        if item['name'] == item_name:
          if item_value is None:
            return True
          if item['value'] == item_value:
            return True
          else:
            return False
    else:
      return False
    return False
  
  def _process_cfg_line(self, line):
    try:
      desc, value = line.split("=")
      desc = self._remove_whitespace(desc)
      value = value.strip()
      if desc == '' or value == '':
        return None
      last_bracket = desc.rfind("(")
      if last_bracket < 1:
        return None
      name = desc[last_bracket + 1:-1]
      desc = desc[0:last_bracket -1]
      last_bracket = value.rfind("(")
      if last_bracket > 0:
        value = value[0:last_bracket]
    except:
      return None
    return {'name':name,'desc':desc,'value':value}

  def _process_set_line(self, line):
    try:
      name, value = line.split("=")
      name = name.strip()
      value = value.strip()
      if name == '' or value == '':
        return None
    except:
      return None
    return {'name':name,'value':value}

  def _instance_up(self):
    rc, stdout, stderr = self._db2_command("ps -ef | grep $DB2INSTANCE | grep db2sysc | grep -v grep | wc -l", "Could not validade if instance is up")
    return '1' == stdout.strip()

  def _find_db2_profile(self):
    user_home = self._find_db2_home()
    return os.path.join(user_home, "sqllib/db2profile")

  def _find_db2_home(self):
    home = expanduser("~" + self.instance)
    return home

  def _remove_whitespace(self, strData):
    ret_value = ""
    space = ""
    try:
      list_words = strData.split()
      for word in list_words:
        ret_value += space + word
        space = " "
    except:
      return ""
    return ret_value
  
  def _db2_command(self, db2_cmd, error_msg):
    cmd = (". %s; " + db2_cmd) % self.db2profile
    rc, stdout, stderr = self.module.run_command(cmd, executable="/usr/bin/ksh", use_unsafe_shell=True)
    if stderr != '' or rc!=0:
      self.module.fail_json(changed=False, msg=error_msg, stderr=stderr, rc=rc, stdout=stdout)
    return rc, stdout, stderr
    
  def _get_dbm_cfg_items(self):
    rc, stdout, stderr = self._db2_command("db2 get dbm cfg", "Error, could not get DBM config")
    config_items = []
    config_info=stdout.split('\n')
    for config_line in config_info:
      config_item = self._process_cfg_line(config_line)
      if config_item is None:
        continue
      config_items.append(config_item)
    self.facts['db2_dbm_cfg'] = config_items
    return config_items  

  def _getenv_items(self):
    rc, stdout, stderr = self._db2_command("db2set", "Error, could not get DB2 Settings")
    config_info=stdout.split('\n')
    config_items = []
    for config_line in config_info:
      config_item = self._process_set_line(config_line)
      if config_item is None:
        continue
      config_items.append(config_item)
    self.facts['db2set'] = config_items
    return config_items

def main():
    module = AnsibleModule(
        argument_spec=dict(
            log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
            instance=dict(required=True, type='str'),
            action=dict(required=True),
            force=dict(required=False, default=False, type='bool'),
            db2home=dict(required=False, type='str'),
            db2port=dict(required=False, type='str'),
            db2api=dict(required=False, type='dict')
        ),
        supports_check_mode=False,
        required_together=[['db2home', 'db2port']]
    )

    module.debug('Started db2instance module')
    
    db2inst = DB2Instance(module)
    db2inst.parse_params()

    if db2inst.action == "create":
      db2inst.create()
    
    if db2inst.action == "start":
      db2inst.start()
    
    if db2inst.action == "stop":
      db2inst.stop()

    if db2inst.action == "restart":
      db2inst.restart()

    if db2inst.action == "disable_auto":
      db2inst.disable_auto()

    if db2inst.action == "enable_auto":
      db2inst.enable_auto()

    if db2inst.action == "get_dbm_cfg":
      db2inst.get_dbm_cfg()
      
    if db2inst.action == "getenv":
      db2inst.getenv()
      
    if db2inst.action == "setenv":
      if isinstance(module.params['db2api'], dict):
        for key, value in module.params['db2api'].iteritems():
          if key == "name":
            name = value
          if key == "value":
            newvalue = value
        db2inst.setenv(name,newvalue)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    if db2inst.action == "set_dbm_cfg":
      if isinstance(module.params['db2api'], dict):
        for key, value in module.params['db2api'].iteritems():
          if key == "using":
            using = value
          if key == "value":
            newvalue = value
        if using is None or newvalue is None:
          module.fail_json(changed=False, msg="Missing one or more db2api parameters")
        db2inst.set_dbm_cfg(using, newvalue)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(db2inst.action))

if __name__ == '__main__':
  main()
