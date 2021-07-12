import os
from azure.cosmos import exceptions, CosmosClient, PartitionKey

# Initialize the Cosmos client
ENDPOINT = os.getenv('AZ_COSMOS_ENDPOINT')
KEY = os.getenv('AZ_COSMOS_KEY')
client = CosmosClient(ENDPOINT, KEY)

DATABASE_NAME = 'AutoDelete'
database = client.create_database_if_not_exists(id=DATABASE_NAME)

CONTAINER_NAME = 'Settings'
container = database.create_container_if_not_exists(
    id=CONTAINER_NAME,
    partition_key=PartitionKey(path="/id")
)


def get_all_info():
    return container.read_all_items()


def init_bot(guild, channel):
    data = {
        'id': f'{channel}',
        'guild': f'{guild}',
        'channel': f'{channel}',
        'archive': None,
        'timeout': 180
    }
    container.upsert_item(body=data)
    return True


def get_info(channel):
    try:
        item = container.read_item(item=f"{channel}", partition_key=f"{channel}")
        return item
    except exceptions.CosmosResourceNotFoundError:
        return False


def set_timeout(channel, timeout):
    item = container.read_item(item=f"{channel}", partition_key=f"{channel}")
    data = {
        'id': item["channel"],
        'guild': item["guild"],
        'channel': item["channel"],
        'archive': item["archive"],
        'timeout': timeout
    }
    container.upsert_item(body=data)
    return True


def set_archive(channel, archive):
    item = container.read_item(item=f"{channel}", partition_key=f"{channel}")
    data = {
        'id': item["channel"],
        'guild': item["guild"],
        'channel': item["channel"],
        'archive': f'{archive}',
        'timeout': item["timeout"]
    }
    container.upsert_item(body=data)
    return True


def get_is_autodelete_active(channel):
    try:
        item = container.read_item(item=f"{channel}", partition_key=f"{channel}")
        return item["timeout"]
    except exceptions.CosmosResourceNotFoundError:
        return False


def get_archive(channel):
    try:
        item = container.read_item(item=f"{channel}", partition_key=f"{channel}")
        return item["archive"]
    except exceptions.CosmosResourceNotFoundError:
        return False


def reset_channel(channel):
    container.delete_item(item=f"{channel}", partition_key=f"{channel}")
    return True