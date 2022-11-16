"""Script to create and benchmark a standalone MySQL server against a MySQL server cluster."""

import boto3
from botocore.exceptions import ClientError

EC2_RESOURCE = boto3.resource('ec2')
EC2_CLIENT = boto3.client('ec2')


def create_ec2(instance_type, sg_id, key_name, instance_name):
    """Creates an EC2 instance

    Args:
        instance_type (str): Instance type (m4.large, ...)
        sg_id (str): Security group ID
        key_name (str): SSH key name
        instance_name (str): Name of the machine instance

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
                        'Value': instance_name
                    },
                ]
            },
        ]
    )[0]
    print(f'{instance} is starting')
    return instance


def create_security_group():
    """Creates a security group

    Returns:
        security_group_id: The created security group ID
    """
    sec_group_name = 'project-security-group'
    security_group_id = None
    try:
        response = EC2_CLIENT.create_security_group(
            GroupName=sec_group_name,
            Description='Security group for the ec2 instances used in the final project'
        )
        security_group_id = response['GroupId']
        print(f'Successfully created security group {security_group_id}')
        sec_group_rules = [
            {'IpProtocol': 'tcp',
             'FromPort': 22,
             'ToPort': 22,
             'IpRanges': [{'CidrIp': '0.0.0.0/0'}]}
        ]
        data = EC2_CLIENT.authorize_security_group_ingress(GroupId=security_group_id,
                                                           IpPermissions=sec_group_rules)
        print(f'Successfully updated security group rules with : {sec_group_rules}')
        return security_group_id
    except ClientError as e:
        try:  # if security group exists already, find the security group id
            response = EC2_CLIENT.describe_security_groups(
                Filters=[
                    dict(Name='group-name', Values=[sec_group_name])
                ])
            security_group_id = response['SecurityGroups'][0]['GroupId']
            print(f'Security group already exists with id {security_group_id}.')
            return security_group_id
        except ClientError as e:
            print(e)
            exit(1)
