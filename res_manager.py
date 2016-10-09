import sys
import os
import json

from pip._vendor.distlib.compat import raw_input
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient

from haikunator import Haikunator
from azure.mgmt.resource.resources.models import DeploymentMode

#region constants
WEST_EUROPE = 'westeurope'
GROUP_NAME = 'eddy-tools-group'
KV_NAME = 'keyvault-eddy-tools'
#endregion

#region print_item
def print_item(group):
    """Print an instance."""
    print("\tName: {}".format(group.name))
    print("\tId: {}".format(group.id))
    print("\tLocation: {}".format(group.location))
    print("\tTags: {}".format(group.tags))
#endregion

#region cred functions
def get_creds():
    credentials = ServicePrincipalCredentials(
        client_id=os.environ['AZURE_CLIENT_ID'], secret=os.environ['AZURE_CLIENT_SECRET'], tenant=os.environ['AZURE_TENANT_ID'])
    return credentials

def get_sub_id():
    subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID', '0')
    return subscription_id

def get_res_client():
    resource_client = ResourceManagementClient(get_creds(), get_sub_id())
    resource_client.providers.register('Microsoft.KeyVault')
    print('\nCreate Resource Group')
    resource_group_params = {'location': WEST_EUROPE}
    print_item(resource_client.resource_groups.create_or_update(GROUP_NAME, resource_group_params))
    return resource_client

#endregion

def get_resource_list(res_client):
    print('resources in the eddy-tools group')
    for item in res_client.resource_groups.list_resources(GROUP_NAME):
        print_item(item)

#region get_res_vault
def get_res_vault():
    print('\nCreate vault')
    kv_client = KeyVaultManagementClient(get_creds(), get_sub_id())
    res_client = get_res_client()

    # region   vault = kv_client.vaults.create_or_update(
    vault = kv_client.vaults.create_or_update(
        GROUP_NAME,
        KV_NAME,
        {
            'location': WEST_EUROPE,
            'properties': {
                'sku': {
                    'name': 'standard'
                },
                'tenant_id': os.environ['AZURE_TENANT_ID'],
                'access_policies': [{
                    'tenant_id': os.environ['AZURE_TENANT_ID'],
                    'object_id': os.environ['AZURE_TENANT_ID'],
                    'permissions': {
                        'keys': ['all'],
                        'secrets': ['all']
                    }
                }]
            }
        }

    )
    # endregion

    print_item(vault)

    # List the Key vaults
    print('\nList KeyVault')
    for vault in kv_client.vaults.list():
        print_item(vault)
    return res_client

#endregion

#region get_res_vault
def del_res_vault(res_client):

    print('\nDelete Resource Group')
    delete_async_operation = res_client.resource_groups.delete(GROUP_NAME)
    delete_async_operation.wait()
    print("\nDeleted: {}".format(GROUP_NAME))

#endregion

#region deploy_vm
name_generator = Haikunator()
def deploy_vm(res_client):
    pub_ssh_key_path = os.path.expanduser('~/.ssh/id_rsa.pub')
    with open(pub_ssh_key_path, 'r') as pub_ssh_file_fd:
        pub_ssh_key = pub_ssh_file_fd.read()
    template_path = os.path.join(os.path.dirname(__file__), 'templates', 'template.json')
    with open(template_path, 'r') as template_file_fd:
        template = json.load(template_file_fd)
    dns_label_prefix = name_generator.haikunate()
    parameters = {
            'sshKeyData': pub_ssh_key,
            'vmName': 'eddy-tools-vm',
            'dnsLabelPrefix': dns_label_prefix
        }
    parameters = {k: {'value': v} for k, v in parameters.items()}

    deployment_properties = {
        'mode': DeploymentMode.incremental,
        'template': template,
        'parameters': parameters
    }
    deployment_async_operation = res_client.deployments.create_or_update(
         GROUP_NAME,
        'eddy-tools',
        deployment_properties
    )
    deployment_async_operation.wait()
    return dns_label_prefix

#endregion


def main(argv):
    global res_client
    while True:
        command = raw_input('command? QQ to quit\n ').strip()

        if command == 'c-vault':
            res_client =  get_res_vault()

        elif command == 'd-group':
            try:
                res_client
            except NameError:
                res_client = get_res_client()
            del_res_vault(res_client)

        elif command == 'vm':
            try:
                res_client
            except NameError:
                res_client = get_res_client()

            remote_ssh_url = deploy_vm(res_client)
            # SSH_AUTH_SOCK=0 for Agent admitted failure to sign using the key error
            print("remote url: `SSH_AUTH_SOCK=0 ssh eddyTools@{}.{}.cloudapp.azure.com`".format(remote_ssh_url, WEST_EUROPE))

        elif command == 'r-display':
            try:
                res_client
            except NameError:
                res_client = get_res_client()

            get_resource_list(res_client)


        elif command == 'QQ':
            break
        else:
            print('Invalid Command\n')



if __name__ == "__main__":
	main(sys.argv)