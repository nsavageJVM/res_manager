import sys
import os

from pip._vendor.distlib.compat import raw_input
from azure.common.credentials import ServicePrincipalCredentials
from azure.mgmt.keyvault import KeyVaultManagementClient
from azure.mgmt.resource.resources import ResourceManagementClient

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

# fix this need create res group first ect ...
def get_res_vault():
    print('\nCreate and then delete a vault')
    kv_client = KeyVaultManagementClient(get_creds(), get_sub_id())
    res_client = get_res_client()
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
    print_item(vault)

    # List the Key vaults
    print('\nList KeyVault')
    for vault in kv_client.vaults.list():
        print_item(vault)

    print('\nDelete Resource Group')
    delete_async_operation = res_client.resource_groups.delete(GROUP_NAME)
    delete_async_operation.wait()
    print("\nDeleted: {}".format(GROUP_NAME))

#endregion

def main(argv):

    while True:
        command = raw_input('command? QQ to quit ').strip()
        if command == 'vault':
            # fix this need create res group first ect ...
            get_res_vault()
        elif command == 'other_thing':
            print('Doing something else')
        elif command == 'QQ':
            break
        else:
            print('Invalid Command.')



if __name__ == "__main__":
	main(sys.argv)