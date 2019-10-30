#!/usr/bin/python

import sys
import os
from os.path import expanduser
from ansible.module_utils.basic import AnsibleModule

class DB2Database:
  def __init__(self, module):
    self.module = module
    self.facts = {}

  def parse_params(self):
    self.module.debug("*** Process all Arguments")
    self.logLevel = self.module.params['log']
    self.force = self.module.params['force']
    self.action = self.module.params['action']
    self.instance = self.module.params['instance']
    self.dbname = self.module.params['dbname']
    self.db2profile = self._find_db2_profile()
    self.cmd_connect = "db2 connect to {0}>/dev/null; ".format(self.dbname)
    self.cmd_terminate = "; db2 terminate>/dev/null"

  def get_db_cfg(self):
    self.module.debug("*** Get DB CFG: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    config_items = self._get_db_cfg_items(self.dbname)
    lineout = "Items {0}".format(len(config_items))
    self.module.exit_json(changed=False, msg="DB Config: " + lineout, ansible_facts=self.facts)

  def get_db_bufferpools(self):
    self.module.debug("*** Get DB Bufferpools: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    config_items = self._get_db_bp_items()
    lineout = "Items {0}".format(len(config_items))
    self.module.exit_json(changed=False, msg="DB Config: " + lineout, ansible_facts=self.facts)

  def get_db_tablespaces(self):
    self.module.debug("*** Get DB Tablespaces: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    config_items = self._get_db_ts_items()
    lineout = "Items {0}".format(len(config_items))
    self.module.exit_json(changed=False, msg="DB Config: " + lineout, ansible_facts=self.facts)

  def exec_sql(self, command=None, filename=None):
    self.module.debug("*** Execute SQL: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    if command is None:
      cmd = "db2 -tvmf " + filename
    if filename is None:
      cmd = "db2 " + command
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate, cmd + " Failed")
    self.module.exit_json(changed=True, msg=cmd + " Success", rc=rc, stdout=stdout, stderr=stderr)

  def update_db_cfg(self, name, value):
    self.module.debug("*** Set DB CFG: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    cmd = "db2 update db cfg using {0} {1}".format(name, value)
    self.module.debug(cmd)
    if not self.dbname + "_cfg" in self.facts:
      self._get_db_cfg_items()
    if self._check_cfg(self.dbname + "_cfg", name, value):
      self.module.exit_json(changed=False, msg=cmd + " OK")
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate, cmd + " Failed")
    self.module.exit_json(changed=True, msg=cmd + " Success", rc=rc, stdout=stdout, stderr=stderr)

  def create(self, db_path, db_automatic, db_pagesize, db_codeset, db_territory, db_collate, db_comment, db_restrictive):
    self.module.debug("*** Create Database: {0}".format(self.dbname))
    if self._created(): 
      self.module.exit_json(changed=False, msg="Database {0} exists.".format(self.dbname))
    create_cmd = "db2 create database {0} ".format(self.dbname)
    options = ""
    # This is default True
    if not db_automatic:
        options += " automatic storage no"
    if db_path:
      options += " on {0}".format(db_path)
      # Validate if automatic_storage == no then only one path can be used
      if not db_automatic:
        #Validate if path contains a comma separated value
        if "," in db_path:
          self.module.fail_json(changed=False, msg="automatic storage specified, you can't create a Database on more than one path")
    if db_codeset:
      if not db_territory:
        self.module.fail_json(changed=False, msg="territory must be specified with codeset")
      options += " using codeset {0}".format(db_codeset)
    if db_territory:
      if not db_codeset:
        self.module.fail_json(changed=False, msg="codeset must be specified with territory")
      options += " territory {0}".format(db_territory)
    if db_collate:
      options += " collate using {0}".format(db_collate)
    if db_pagesize:
      options += " pagesize {0}".format(db_pagesize)
    if db_restrictive:
      options += " restrictive"
#    if db_comment:
#      options += " with '{0}'".format(db_comment)
    rc, stdout, stderr = self._db2_command(create_cmd + options, "Failed to create database {0}".format(self.dbname))
    self.module.exit_json(changed=True, msg="Database {0} created".format(self.dbname), rc=rc, stdout=stdout, stderr=stderr)

  def create_db_bufferpool(self, bufferpool, pagesize):
    self.module.debug("*** Create Bufferpool: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    fact_name = self.dbname + "_bp"
    if not fact_name in self.facts:
      self._get_db_bp_items()
    if self._check_cfg(fact_name, bufferpool.upper(), None):
      self.module.exit_json(changed=False, msg="Database {0}, Bufferpool {1} exists.".format(self.dbname, bufferpool))
    cmd = "db2 create bufferpool {0} IMMEDIATE PAGESIZE {1}".format(bufferpool, pagesize)
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate, cmd + " Failed")
    self.module.exit_json(changed=True, msg="Database {0}, Bufferpool {1} created.".format(self.dbname, bufferpool), rc=rc, stdout=stdout, stderr=stderr)
    
  def create_db_tablespace(self, tablespace, type, bufferpool, pagesize):
    self.module.debug("*** Create Tablespace: {0}".format(self.dbname))
    if not self._created(): 
      self.module.fail_json(changed=False, msg="Database {0} does not exist.".format(self.dbname))
    fact_name = self.dbname + "_ts"
    if not fact_name in self.facts:
      self._get_db_ts_items()
    if self._check_cfg(fact_name, tablespace.upper(), None):
      self.module.exit_json(changed=False, msg="Database {0}, Tablespace {1} exists.".format(self.dbname, tablespace))
    tablespace_types = ["LARGE", "REGULAR", "SYSTEM TEMPORARY", "USER TEMPORARY"]
    if not type.upper() in tablespace_types:
      self.module.fail_json(changed=False, msg="Unsupported tablespace type")
    cmd = "db2 create {0} tablespace {1} ".format(type, tablespace)
    options = ""
    if pagesize:
      options += " pagesize {0}".format(pagesize)
    if bufferpool:
      options += " bufferpool {0}".format(bufferpool)
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + options + self.cmd_terminate, cmd + " Failed")
    self.module.exit_json(changed=True, msg="Database {0}, Tablespace {1} created.".format(self.dbname, tablespace), rc=rc, stdout=stdout, stderr=stderr)

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
    
  def _get_db_cfg_items(self):
    cmd = "db2 get db cfg".format(self.dbname)
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate, "Error, could not get DB config")
    config_items = []
    config_info=stdout.split('\n')
    for config_line in config_info:
      config_item = self._process_cfg_line(config_line)
      if config_item is None:
        continue
      config_items.append(config_item)
    self.facts[self.dbname + '_cfg'] = config_items
    return config_items

  def _get_db_bp_items(self):
    cmd = "db2 select bpname,pagesize from syscat.bufferpools |grep -e \"^BPNAME\" -e \"^-\" -e \"selected.$\" -v".format(self.dbname)
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate, "Error, could not get DB Bufferpools")
    config_items = []
    config_info=stdout.split('\n')
    for config_line in config_info:
      try:
        bpname,pagesize = config_line.strip().split()
        bpname = bpname.strip()
        pagesize = pagesize.strip()
        if bpname == '' or pagesize == '':
          continue
        config_item = {'name':bpname,'pagesize':pagesize}
        config_items.append(config_item)
      except:
        continue
    self.facts[self.dbname + '_bp'] = config_items
    return config_items

  def _get_db_ts_items(self):
    cmd = "db2 list tablespaces"
    rc, stdout, stderr = self._db2_command(self.cmd_connect + cmd + self.cmd_terminate,"Error, could not get DB Tablespaces")
    config_items = []
    config_item = None
    config_info=stdout.split('\n')
    for config_line in config_info:
      config_attr = self._process_set_line(config_line)
      if config_attr is None:
        continue
      if config_attr['name'] == "Tablespace ID":
        if config_item:
          config_items.append(config_item)
        config_item = {'id': config_attr['value']}
      if config_attr['name'] == "Name":
        config_item['name'] = config_attr['value']
      if config_attr['name'] == "Type":
        config_item['type'] = config_attr['value']
      if config_attr['name'] == "Contents":
        config_item['contents'] = config_attr['value']
      if config_attr['name'] == "State":
        config_item['state'] = config_attr['value']
    if config_item:
      config_items.append(config_item)
    self.facts[self.dbname + '_ts'] = config_items
    return config_items

  def _created(self):
    cmd = "db2 list db directory | grep \"Database name\" | awk '{print $4}'"
    rc, stdout, stderr = self._db2_command(cmd, "Error, Could not get database directory")
    for db in stdout.strip().split('\n'):
      if db == self.dbname.upper():
        return True
    return False

def main():
    module = AnsibleModule(
        argument_spec=dict(
            log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
            instance=dict(required=True, type='str'),
            dbname=dict(required=True, type='str'),
            action=dict(required=True),
            force=dict(required=False, default=False, type='bool'),
            db2api=dict(required=False, type='dict')
        ),
        supports_check_mode=False,
    )

    module.debug('Started db2database module')
    
    db2db = DB2Database(module)
    db2db.parse_params()
    
    if db2db.action == "get_db_cfg":
      db2db.get_db_cfg()

    if db2db.action == "get_db_bufferpools":
      db2db.get_db_bufferpools()

    if db2db.action == "get_db_tablespaces":
      db2db.get_db_tablespaces()

    if db2db.action == "update_db_cfg":
      if isinstance(module.params['db2api'], dict):
        for key, value in module.params['db2api'].iteritems():
          if key == "using":
            using = value
          if key == "value":
            newvalue = value
        if using is None or newvalue is None:
          module.fail_json(changed=False, msg="Missing one or more db2api parameters")
        db2db.update_db_cfg(using, newvalue)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    if db2db.action == "create_db_bufferpool":
      if isinstance(module.params['db2api'], dict):
        for key, value in module.params['db2api'].iteritems():
          if key == "bufferpool":
            bufferpool = value
          if key == "pagesize":
            pagesize = value
        if bufferpool is None or pagesize is None:
          module.fail_json(changed=False, msg="Missing one or more db2api parameters")
        db2db.create_db_bufferpool(bufferpool, pagesize)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    if db2db.action == "create_db_tablespace":
      if isinstance(module.params['db2api'], dict):
        bufferpool = None
        pagesize = None
        for key, value in module.params['db2api'].iteritems():
          if key == "tablespace":
            tablespace = value
          if key == "type":
            type = value
          if key == "bufferpool":
            bufferpool = value
          if key == "pagesize":
            pagesize = value
        if tablespace is None or type is None:
          module.fail_json(changed=False, msg="Missing one or more db2api parameters")
        db2db.create_db_tablespace(tablespace, type, bufferpool, pagesize)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    if db2db.action == "create":
      if isinstance(module.params['db2api'], dict):
        path = None
        automatic = True
        pagesize = None
        codeset = None
        territory = None
        collate = None
        comment = None
        for key, value in module.params['db2api'].iteritems():
          if key == "path":
            path = value
          if key == "automatic":
            automatic = value
          if key == "pagesize":
            pagesize = value
          if key == "codeset":
            codeset = value
          if key == "territory":
            territory = value
          if key == "collate":
            collate = value
          if key == "comment":
            comment = value
          if key == "restrictive":
            restrictive = value
        db2db.create(path, automatic, pagesize, codeset, territory, collate, comment, restrictive)
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")
    
    if db2db.action == "exec_sql":
      if isinstance(module.params['db2api'], dict):
        filename = None
        command = None
        for key, value in module.params['db2api'].iteritems():
          if key == "filename":
            filename = value
          if key == "command":
            command = value
        if filename is None and command is None:
          module.fail_json(changed=False, msg="Missing db2api parameters")
        if filename is None:
          db2db.exec_sql(command=command)
        if command is None:
          db2db.exec_sql(filename=filename)
        module.fail_json(changed=False, msg="Cannot specify command and filename together")
      else:
        module.fail_json(changed=False, msg="Missing db2api parameters")

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(db2db.action))
    
if __name__ == '__main__':
  main()
