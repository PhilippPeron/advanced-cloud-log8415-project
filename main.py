"""Script to create and benchmark a standalone MySQL server against a MySQL server cluster."""

import boto3

EC2_RESOURCE = boto3.resource('ec2')
EC2_CLIENT = boto3.client('ec2')


def create_ec2(instance_type, sg_id, key_name):
    """Creates an EC2 instance

    Args:
        instance_type (str): Instance type (m4.large, ...)
        sg_id (str): Security group ID
        key_name (str): SSH key name

    Returns:
        instance: The created instance object
    """
    instance = EC2_RESOURCE.create_instances(
        ImageId='ami-0149b2da6ceec4bb0',
        MinCount=1,
        MaxCount=1,
        InstanceType=instance_type,
        Monitoring={'Enabled': True},
        SecurityGroupIds=[sg_id],
        KeyName=key_name,
        TagSpecifications=[
            {
                'ResourceType': 'instance',
                'Tags': [
                    {
                        'Key': 'Name',
                        'Value': 'lab2-hadoop-instance'
                    },
                ]
            },
        ]
    )[0]
    print(f'{instance} is starting')
    return instance
