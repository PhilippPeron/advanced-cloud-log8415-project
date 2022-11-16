"""Script to create and benchmark a standalone MySQL server against a MySQL server cluster."""

import time
import argparse
import subprocess
from subprocess import CREATE_NEW_CONSOLE
from os import path
import boto3
from botocore.exceptions import ClientError


parser = argparse.ArgumentParser(description='Instance setup.')
parser.add_argument('--kill', action='store_true', default=False, help='Kill all running instances and exit')
args = parser.parse_args()

EC2_RESOURCE = boto3.resource('ec2')
EC2_CLIENT = boto3.client('ec2')


def create_ec2(instance_type, sg_id, key_name, instance_name, user_data=None):
    """Creates an EC2 instance

    Args:
        instance_type (str): Instance type (m4.large, ...)
        sg_id (str): Security group ID
        key_name (str): SSH key name
        instance_name (str): Name of the machine instance
        user_data (str): Script that gets executed on instance at start up

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
        UserData=user_data,
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


def create_key_pair(key_name, private_key_filename):
    """Generates a key pair to access our instance

    Args:
        key_name (str): key name
        private_key_filename (str): filename to save the private key to
    """
    response = EC2_CLIENT.describe_key_pairs()
    kp = [kp for kp in response['KeyPairs'] if kp['KeyName'] == key_name]
    if len(kp) > 0 and not path.exists(private_key_filename):
        print(
            f'{key_name} already exists distantly, but the private key file has not been downloaded. Either delete the remote key or download the associate private key as {private_key_filename}.')
        exit(1)

    print(f'Creating {private_key_filename}')
    if path.exists(private_key_filename):
        print(f'Private key {private_key_filename} already exists, using this file.')
        return

    response = EC2_CLIENT.create_key_pair(KeyName=key_name)
    with open(private_key_filename, 'w+') as f:
        f.write(response['KeyMaterial'])
    print(f'{private_key_filename} written.')


def retrieve_instance_ip(instance_id, silent=False):
    """Retrieves an instance's public IP

    Args:
        instance_id (str): instance id
        silent (bool): if function prints something

    Returns:
        str: Instance's public IP
    """
    instance_config = EC2_CLIENT.describe_instances(InstanceIds=[instance_id])
    instance_ip = instance_config["Reservations"][0]['Instances'][0]['PublicIpAddress']
    if not silent:
        print(f'Retrieving instance {instance_id} public IP...')
        print(f'Public IP : {instance_ip}')
    return instance_ip


def terminate_all_running_instances():
    """Terminate all currently running instances.
    """
    response = EC2_CLIENT.describe_instances()
    instance_ids = [instance['Instances'][0]['InstanceId'] for instance in response['Reservations']
        if instance['Instances'][0]['State']['Name'] == 'running']
    print(f'Terminating : {instance_ids}')
    try:
        EC2_CLIENT.terminate_instances(InstanceIds=[instance_id for instance_id in instance_ids])
    except ClientError as e:
        print('Failed to terminate the instances.')
        print(e)


def run_ssh_commands(commands, instance_ip):
    """Create subprocess and run ssh commands

    Args:
        commands (list): list of commands as strings
        instance_ip (str): ip of instance"""
    print("Running SSH commands...")
    ssh_commands = ["ssh", "-tt", "-i", private_key_filename, f"ubuntu@{instance_ip}"]
    # Connect via SSH and run commands
    sshProcess = subprocess.Popen(ssh_commands,
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE,
                                  universal_newlines=True,
                                  bufsize=0,
                                  creationflags=CREATE_NEW_CONSOLE)
    for command in commands:
        sshProcess.stdin.write(command + "\n")
    sshProcess.stdin.close()

    for line in sshProcess.stdout:
        if line == "ENDING\n":
            break
        print(f"    {line}", end="")
    # # to catch the lines up to logout
    # for line in sshProcess.stdout:
    #     print(line, end="")


def start_standalone_instance():
    """Starts the instance for the MySQL standalone machine"""
    # Create the instance with the key pair
    instance = create_ec2('t2.micro', sg_id, key_name, 'standalone-mysql', user_data="")
    print(f'Waiting for instance {instance.id} to be running...')
    instance.wait_until_running()
    # Get the instance's IP
    instance_ip = retrieve_instance_ip(instance.id, silent=True)

    # Wait until instance is reachable
    wait_time = 10
    print(f"Waiting {wait_time}s to make sure instance is reachable")
    time.sleep(wait_time)
    print(
        f'Access standalone instance with: \'ssh -i {private_key_filename} ubuntu@{instance_ip}\'')
    commands = [
        f"sudo git clone https://github.com/PhilippPeron/cloud-log8415-project\n"
        f"cd cloud-log8415-project/remote/\n",
        f"sudo chmod +x setup_standalone_mysql.sh\n",
        f"sudo sh setup_standalone_mysql.sh\n",
        f"echo ENDING\n"
    ]
    run_ssh_commands(commands, instance_ip)

    print('Run benchmark with: ')
    return instance


def get_user_data(instance_type):
    """Creates user data script

    Args:
        instance_type (str): master or slave"""
    user_data = f"""#!/bin/bash
    cd /home/ubuntu/
    sudo git clone https://github.com/PhilippPeron/cloud-log8415-project
    cd /home/ubuntu/cloud-log8415-project/remote/"""
    # sudo chmod +x setup_{instance_type}_mysql.sh
    # sudo sh setup_{instance_type}_mysql.sh"""
    return user_data


def start_cluster_instances():
    """Starts the instances for the MySQL cluster

    Returns:
        dict: Dictionary with one master and three slave instances"""
    mysql_cluster = {}
    mysql_cluster_ips = {}
    # Create the instance with the key pair
    mysql_cluster['master'] = create_ec2('t2.micro', sg_id, key_name, 'master-mysql', get_user_data('master'))
    for slave_id in range(3):
        mysql_cluster[f'slave_{slave_id}'] = create_ec2('t2.micro', sg_id, key_name, f'slave_{slave_id}', get_user_data('slave'))

    print(f'Waiting for cluster instances to be running...')
    with open('env_variables.txt', 'w+') as f:
        for key, instance in mysql_cluster.items():
            instance.wait_until_running()
            # Get the instance's IP
            instance_ip = retrieve_instance_ip(instance.id, silent=True)
            mysql_cluster_ips[key] = instance_ip
            print(
                f'Access {key} instance with: \'ssh -i {private_key_filename} ubuntu@{instance_ip}\'')
            f.write(f'{key.upper()}={instance_ip}\n')
        f.write(f'PRIVATE_KEY_FILE={private_key_filename}\n')
    print('Wrote instance\'s IP and private key filename to env_variables.txt')

    print('Run benchmark with: ')
    return mysql_cluster, mysql_cluster_ips


if __name__ == "__main__":
    if args.kill:
        terminate_all_running_instances()
        exit(0)
    # Create key pair
    key_name = 'PROJECT_KEY'
    private_key_filename = f'./private_key_{key_name}.pem'
    create_key_pair(key_name, private_key_filename)

    # Create a security group
    sg_id = create_security_group()
    print("")
    standalone_instance = start_standalone_instance()
    # mysql_cluster = start_cluster_instances()
