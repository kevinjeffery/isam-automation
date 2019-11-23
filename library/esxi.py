#!/usr/bin/python
# library/esxi.py
# @version v1.01_2019-NOV-17
# @author Kevin Jeffery

import sys
import os
import re
import json
import tempfile
from os.path import expanduser
from ansible.module_utils.basic import AnsibleModule

class ESXi:
    def __init__(self, module):
        self.module = module
        self.facts = {}
        self.vmsvc_getallvms = '/bin/vim-cmd vmsvc/getallvms'
        self.vmsvc_power_getstate = '/bin/vim-cmd vmsvc/power.getstate {0}' # vm_id
        self.vmsvc_power_on = '/bin/vim-cmd vmsvc/power.on {0}' # vm_id
        self.vmsvc_power_off = '/bin/vim-cmd vmsvc/power.off {0}' # vm_id
        self.vmsvc_power_shutdown = '/bin/vim-cmd vmsvc/power.shutdown {0}' # vm_id
        self.vmsvc_power_reboot = '/bin/vim-cmd vmsvc/power.reboot {0}' # vm_id
        self.vmsvc_get_summary = '/bin/vim-cmd vmsvc/get.summary {0}' # vm_id
        self.vmsvc_createdummyvm = '/bin/vim-cmd vmsvc/createdummyvm {0} [{1}]' # vm_name vm_datastore
        self.vmsvc_unregister = '/bin/vim-cmd vmsvc/unregister {0}' # vm_id
        self.vmsvc_solo_registervm = '/bin/vim-cmd solo/registervm /vmfs/volumes/{1}/{0}/{0}.vmx {0} {2}' # vm_name vm_datastore [resourcepool(optional)]
        self.vmkfstools_delete = '/bin/vmkfstools -U /vmfs/volumes/{1}/{0}/{0}.vmdk' # vm_name  vm_datastore
        self.vmkfstools_create = '/bin/vmkfstools -c {2}G /vmfs/volumes/{1}/{0}/{0}.vmdk' # vm_name vm_datastore vm_hdd_size
        self.esxcli = 'esxcli --formatter=keyvalue {0} {1} {2}'

    def parse_params(self):
        self.module.debug("*** Process all Arguments")
        self.logLevel = self.module.params['log']
        self.force = self.module.params['force']
        self.action = self.module.params['action']
        self.vm_name = self.module.params['vm_name']
        self.vm_datastore  = self.module.params['vm_datastore']
        self.vm_networks   = self.module.params['vm_networks']
        self.vm_hdd_size   = self.module.params['vm_hdd_size']
        self.vm_mem_size   = self.module.params['vm_mem_size']
        self.vm_cpu_count  = self.module.params['vm_cpu_count']
        self.vm_guest_os   = self.module.params['vm_guest_os']
        self.vm_scsi_type  = self.module.params['vm_scsi_type']
        self.vm_iso_image  = self.module.params['vm_iso_image']
        self.vm_iso_image2 = self.module.params['vm_iso_image2']
        self.facts['version'] = self._get_version()

    def get_version(self):
        self.module.exit_json(changed=False, data=self.facts['version'])

    def get_all_vms(self):
        self.module.exit_json(changed=False, data=self._get_all_vms())

    def get_vm(self, vm_name):
        ret_data = self._search(vm_name)
        if ret_data:
            ret_data['state'] = self._get_vm_state(ret_data['vmid'])
            ret_data['toolsStatus'] = self._get_tools_status(ret_data['vmid'])
        else:
            self.module.fail_json(changed=False, msg="Error, VM not found")
        self.module.exit_json(changed=False, data=ret_data)

    def create_vm(self, vm_name, vm_datastore, vm_guest_os=None, vm_mem_size=None, vm_hdd_size='8', vm_resource_pool='',
                    vm_cpu_count=None, vm_scsi_type=None, vm_networks=None, vm_iso_image=None, vm_iso_image2=None):
        self.module.debug("*** Create VM {0}".format(vm_name))
        vm_info = self._search(vm_name)
        if vm_info is not None:
            self.module.exit_json(changed=False, msg="VM exists")
        # Create dummy VM
        stdout = self._esxi_command(self.vmsvc_createdummyvm.format(vm_name, vm_datastore), "Error, createdummyvm failed: {0}".format(vm_name))[1]
        vmid = stdout.split('\n')[0]
        # unregister VM
        self._esxi_command(self.vmsvc_unregister.format(vmid), "Error, unregistervm failed: {0}".format(vm_name))
        # Delete the hard disk
        self._esxi_command(self.vmkfstools_delete.format(vm_name, vm_datastore), "Error, vmkfstools delete failed: {0}".format(vm_name))
        # recreate the disk with new size
        self._esxi_command(self.vmkfstools_create.format(vm_name, vm_datastore, vm_hdd_size), "Error, vmkfstools create failed: {0}".format(vm_name))
        # process the vmx file
        self._process_vmx_file(vm_name, vm_datastore, vm_guest_os=vm_guest_os, vm_mem_size=vm_mem_size, vm_hdd_size=vm_hdd_size,
            vm_cpu_count=vm_cpu_count, vm_scsi_type=vm_scsi_type, vm_networks=vm_networks, vm_iso_image=vm_iso_image, vm_iso_image2=vm_iso_image2, vm_create=True)
        # register the vm
        stdout = self._esxi_command(self.vmsvc_solo_registervm.format(vm_name, vm_datastore, vm_resource_pool), "Error, registervm failed: {0}".format(vm_name))[1]
        vmid = stdout.split('\n')[0]
        self.module.exit_json(changed=True, data=vmid)

    def set_vm(self, vm_name, vm_datastore, vm_mem_size=None, vm_networks=None, vm_iso_image=None, vm_iso_image2=None):
        changed = False
        ret_data = self._search(vm_name)
        if ret_data:
            vmid = ret_data['vmid']
            if self._get_vm_state(vmid) != 'poweredOff':
                self.module.exit_json(changed=False, warnings=['VM not poweredOff'], data=vmid)
        else:
            self.module.fail_json(changed=False, msg="Error, VM not found: {0}".format(vm_name))
        changed = self._process_vmx_file(vm_name, vm_datastore, vm_mem_size=vm_mem_size, vm_networks=vm_networks, vm_iso_image=vm_iso_image)
        self.module.exit_json(changed=changed, data=vmid)        

    def set_state(self, vm_name, new_state):
        ret_data = self._search(vm_name)
        if ret_data:
            vmid = ret_data['vmid']
            state = self._get_vm_state(vmid)
            toolsStatus = self._get_tools_status(vmid)
            if new_state == 'poweredOff' or new_state == 'shutdown':
                if state == 'poweredOff':
                    self.module.exit_json(changed=False, msg='VM is already poweredOn', data=ret_data)
                elif state == 'poweredOn' and new_state == 'poweredOff':
                    self._esxi_command(self.vmsvc_power_off.format(vmid), 'Error, could not poweroff {0}'.format(vmid))
                    ret_data['state'] = 'poweredOff'
                    if toolsStatus == 'toolsOk':
                        ret_data['toolsStatus'] = 'toolsNotRunning'
                elif state == 'poweredOn' and toolsStatus == 'toolsOk':
                    self._esxi_command(self.vmsvc_power_shutdown.format(vmid), 'Error, could not shutdown {0}'.format(vmid))
                    ret_data['state'] = 'poweredOff'
                    ret_data['toolsStatus'] = 'toolsNotRunning'
                else:
                    self.module.fail_json(changed=False, msg="Error, tools not running: {0} {1}".format(vmid, toolsStatus))
            elif new_state == 'poweredOn':
                if state == 'poweredOn':
                    self.module.exit_json(changed=False, msg='VM is already poweredOn', data=ret_data)
                self._esxi_command(self.vmsvc_power_on.format(vmid), 'Error, could not poweron {0}'.format(vmid))
            elif new_state == 'reboot':
                if state == 'poweredOff':
                    self.module.fail_json(changed=False, msg="Error, VM is not running: {0}".format(vmid))
                elif toolsStatus == 'toolsOk':
                    self._esxi_command(self.vmsvc_power_reboot.format(vmid), 'Error, could not shutdown {0}'.format(vmid))
                else:
                    self.module.fail_json(changed=False, msg="Error, tools not running: {0} {1}".format(vmid, toolsStatus))
            else:
                self.module.fail_json(changed=False, msg='Error, invalid power state')
        else:
            self.module.fail_json(changed=False, msg="Error, VM not found: {0}".format(vm_name))
        self.module.exit_json(changed=True, data=ret_data)

    def _get_vm_state(self, vmid):
        ret_val = "unknown"
        stdout = self._esxi_command(self.vmsvc_power_getstate.format(vmid), "Error, cannot get state {0}".format(vmid))[1]
        info_lines = stdout.split('\n')
        for info_line in info_lines:
            if re.match("Powered on", info_line):
                return 'poweredOn'
            if re.match("Powered off", info_line):
                return 'poweredOff'
        return ret_val

    def _get_tools_status(self, vmid):
        ret_val = "unknown"
        stdout = self._esxi_command(self.vmsvc_get_summary.format(vmid) + " | grep toolsStatus", "Error, cannot get tools status: {0}".format(vmid))[1]
        if re.search(r'toolsNotRunning', stdout):
            return 'toolsNotRunning'
        if re.search(r'toolsOk', stdout):
            return 'toolsOk'
        return ret_val

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

    def _process_vmx_file(self, vm_name, vm_datastore, vm_guest_os=None, vm_mem_size=None, vm_hdd_size=None,
                    vm_cpu_count=None, vm_scsi_type=None, vm_networks=None, vm_iso_image=None, vm_iso_image2=None, vm_create=False):
        changed = vm_create
        try:
            vmx_file = open("/vmfs/volumes/{1}/{0}/{0}.vmx".format(vm_name, vm_datastore), 'r')
            temp_file = tempfile.TemporaryFile('w+')
            for line in vmx_file:
                newline = None
                if re.match(r'^guestOS', line) and vm_guest_os is not None and vm_create:
                    newline = "guestOS = \"{0}\"\n".format(vm_guest_os)
                if re.match(r'^scsi0\.virtualDev', line) and vm_scsi_type is not None and vm_create:
                    newline = "scsi0.virtualDev = \"{0}\"\n". format(vm_scsi_type)
                if re.match(r'^memSize', line) and vm_mem_size is not None:
                    newline = "memSize = \"{0}\"".format(vm_mem_size)
                if re.match(r'^ide1:0\.fileName', line) and vm_iso_image is not None:
                    newline = "ide1:0.fileName = \"{0}\"\n".format(vm_iso_image)
                if re.match(r'^ide1:1\.fileName', line) and vm_iso_image2 is not None:
                    newline = "ide1:1.fileName = \"{0}\"\n".format(vm_iso_image2)
                if re.match(r'^ethernet\d\.networkName', line) and vm_networks is not None:
                    index = int(line[8:9])
                    if index < len(vm_networks):
                        net_device = 'ethernet' + str(index) + '.'
                        newline = net_device + "networkName = \"" + vm_networks[index]['networkName'] + "\"\n"
                if newline is not None:
                    temp_file.write(newline)
                    if line != newline:
                        changed = True
                else:
                    temp_file.write(line)
            vmx_file.close()
            if vm_cpu_count is not None and int(vm_cpu_count) > 1 and vm_create:
                temp_file.write("numvcpus = \"{0}\"\n".format(vm_cpu_count))
                temp_file.write("cpuid.coresPerSocket = \"{0}\"\n".format(vm_cpu_count))
            if vm_mem_size is not None and vm_create:
                temp_file.write("memSize = \"{0}\"\n".format(vm_mem_size))
            if vm_iso_image is not None and vm_create:
                temp_file.write("ide1:0.deviceType = \"cdrom-image\"\n")
                temp_file.write("ide1:0.present = \"TRUE\"\n")
                temp_file.write("ide1:0.fileName = \"{0}\"\n".format(vm_iso_image))
            if vm_iso_image2 is not None and vm_create:
                temp_file.write("ide1:1.deviceType = \"cdrom-image\"\n")
                temp_file.write("ide1:1.present = \"TRUE\"\n")
                temp_file.write("ide1:1.fileName = \"{0}\"\n".format(vm_iso_image2))
            if vm_networks is not None and vm_create:
                card_number = 0
                for network in vm_networks:
                    net_device = 'ethernet' + str(card_number) + '.'
                    temp_file.write(net_device + "present = \"TRUE\"\n")
                    temp_file.write(net_device + "addressType = \"generated\"\n")
                    temp_file.write(net_device + "networkName = \"" + network['networkName'] + "\"\n")
                    if network['virtualDev'] is None:
                        temp_file.write(net_device + "virtualDev = \"e1000\"\n")
                    else:
                        temp_file.write(net_device + "virtualDev = \"" + network['virtualDev'] + "\"\n")
                    card_number = card_number + 1
            if changed:
                temp_file.seek(0)
                vmx_file = open("/vmfs/volumes/{1}/{0}/{0}.vmx".format(vm_name, vm_datastore), 'w')
                vmx_file.writelines(temp_file.readlines())
                vmx_file.close()
            temp_file.close()
        except OSError as err:
            if vmx_file:
                vmx_file.close()
            if temp_file:
                temp_file.close()
            self.module.fail_json(changed=True, msg=str(err))
        return changed

    def _process_keyvalue_line(self, line, label_delimiter=None, label_index=None):
        try:
            key, value = line.split("=")
            value = value.strip()
            if key == '' or value == '':
                return None
            if label_delimiter is None or label_index is None:
                return {'name': key, 'value': value}
            items = key.split(label_delimiter)
            return {'name': items[label_index], 'value': value}
        except:
            return None

    def _esxi_command(self, cmd, error_msg):
        rc, stdout, stderr = self.module.run_command(cmd, use_unsafe_shell=True)
        if stderr != '' or rc != 0:
            self.module.fail_json(changed=False, msg=error_msg, stderr=stderr, rc=rc, stdout=stdout)
        return rc, stdout, stderr

    def _get_version(self):
        stdout = self._esxi_command(self.esxcli.format('system', 'version', 'get'), "Error, could not get ESXi version")[1]
        version = {}
        config_info = stdout.split('\n')
        for config_line in config_info:
            config_item = self._process_keyvalue_line(config_line, '.', 1)
            if config_item is None:
                continue
            version[config_item['name'].lower()] = config_item['value']
        return version

    def _version_compare(self, version):
        def normalize(v):
            v = re.sub(r'_b\d+$', '', v)
            return [int(x) for x in re.sub(r'(\.0+)*$', '', v).split(".")]

        if normalize(self.facts['version']['version']) == normalize(version):
            return 0
        elif normalize(self.facts['version']['version']) > normalize(version):
            return 1
        elif normalize(self.facts['version']['version']) < normalize(version):
            return -1

    def _get_all_vms(self):
        vm_list = []
        vm_object = {}
        is_header = True
        stdout = self._esxi_command(self.vmsvc_getallvms, 'Error, could not get VM list.')[1]
        info_lines = stdout.split('\n')
        for info_line in info_lines:
            info_line = info_line.strip()
            if is_header:
                is_header = False
                continue
            if info_line == '':
                continue
            items = info_line.split('[')  # Index 0 has vmid and name
            if len(items) == 1: # continuation of annotation item
                vm_object['annotation'] = vm_object['annotation'] + '\n' + info_line
                continue
            if vm_object:
                vm_list.append(vm_object)
            vm_object = {}
            # index 0 has datastore, file, guestos; index 1 has hardware version, annotation
            items_2 = items[1].split('vmx-')
            items_3 = items_2[0].split()
            vmid = items[0][:7].strip()
            name = items[0][7:].strip()
            datastore = items_3[0]
            datastore = datastore[:len(datastore) - 1]
            vmxfile = items_3[1].strip()
            guestos = items_3[2].strip()
            version = items_2[1][:2]
            annotation = items_2[1][2:].strip()
            vm_object['vmid'] = vmid
            vm_object['name'] = name
            vm_object['datastore'] = datastore
            vm_object['vmxfile'] = vmxfile
            vm_object['guestos'] = guestos
            vm_object['version'] = version
            vm_object['annotation'] = annotation
        if vm_object:
            vm_list.append(vm_object)
        return vm_list

    def _search(self, vm_name):
        for vm_info in self._get_all_vms():
            if vm_info['name'] == vm_name:
                return vm_info
        return None

def main():
    module = AnsibleModule(
        argument_spec=dict(
        log=dict(required=False, default='INFO', choices=['DEBUG', 'INFO', 'ERROR', 'CRITICAL']),
        force=dict(required=False, default=False, type='bool'),
        action=dict(required=True),
        vm_name=dict(required=False, type='str'),
        vm_datastore=dict(required=False, type='str'),
        vm_networks=dict(required=False, type='list'),
        vm_hdd_size=dict(required=False, type='int'),
        vm_mem_size=dict(required=False, type='int'),
        vm_cpu_count=dict(required=False, type='str'),
        vm_guest_os=dict(required=False, type='str', choices=[
            'centos-64', # CentOS 4/5/6/7 (64-bit) 5.5.0
            'centos7-64', # CentOS 7 (64-bit) - 6.5.0
            'other3xlinux-64', # Other 3.x Linux (64-bit) 6.5.0
            'other26xlinux-64', # Other 2.6 Linux (64-bit)
            'other', #
            'ubuntu-64', # Ubuntu Linux (64-bit) 5.5.0
            'windows8srv-64' # Microsoft Windows Server 2008,2012 (64-bit)
        ]),
        vm_scsi_type=dict(require=False, type='str', choices=['buslogic', 'lsilogic', 'pvscsi']),
        vm_iso_image=dict(required=False, type='str'),
        vm_iso_image2=dict(required=False, type='str')
        ),
        supports_check_mode=False,
        # required_together=[['vm_networks', 'vm_hdd_size',
        #                     'vm_mem_size', 'vm_cpu_count', 'vm_guest_os']]
    )

    module.debug('Started esxi module')

    esxi_inst = ESXi(module)
    esxi_inst.parse_params()

    if esxi_inst.action == "get_version":
        esxi_inst.get_version()

    if esxi_inst.action == 'get_all':
         esxi_inst.get_all_vms()
    
    # These methods require vm_name
    if esxi_inst.vm_name is None:
        module.fail_json(changed=False, msg="Error, vm_name is required")

    if esxi_inst.action == 'get':
        esxi_inst.get_vm(esxi_inst.vm_name)

    if esxi_inst.action == 'poweron':
        esxi_inst.set_state(esxi_inst.vm_name, 'poweredOn')

    if esxi_inst.action == 'poweroff':
        esxi_inst.set_state(esxi_inst.vm_name, 'poweredOff')

    if esxi_inst.action == 'shutdown':
        esxi_inst.set_state(esxi_inst.vm_name, 'shutdown')

    if esxi_inst.action == 'reboot':
        esxi_inst.set_state(esxi_inst.vm_name, 'reboot')

     # These methods require vm_datastore
    if esxi_inst.vm_datastore is None:
         module.fail_json(changed=False, msg="Error, vm_datastore is required")

    if esxi_inst.action == 'create':
        esxi_inst.create_vm(
            esxi_inst.vm_name,
            esxi_inst.vm_datastore,
            vm_hdd_size=esxi_inst.vm_hdd_size,
            vm_mem_size=esxi_inst.vm_mem_size,
            vm_guest_os=esxi_inst.vm_guest_os,
            vm_cpu_count=esxi_inst.vm_cpu_count,
            vm_scsi_type=esxi_inst.vm_scsi_type,
            vm_networks=esxi_inst.vm_networks,
            vm_iso_image=esxi_inst.vm_iso_image,
            vm_iso_image2=esxi_inst.vm_iso_image2
        )

    if esxi_inst.action == 'set':
        esxi_inst.set_vm(
            esxi_inst.vm_name,
            esxi_inst.vm_datastore,
            vm_mem_size=esxi_inst.vm_mem_size,
            vm_networks=esxi_inst.vm_networks,
            vm_iso_image=esxi_inst.vm_iso_image,
            vm_iso_image2=esxi_inst.vm_iso_image2
        )

    module.fail_json(changed=False, msg="Error, Invalid action: {0}".format(esxi_inst.action))


if __name__ == '__main__':
    main()
