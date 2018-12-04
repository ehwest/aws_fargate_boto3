from shared_functions import parse_arguments
import sys
import json
import boto3
import time
import os


def remove_alb(arn):
    r = elb_client.delete_load_balancer(
        LoadBalancerArn=arn
    )


def remove_cluster(cluster_name, servce_name):
    s = 60
    ecs_client.update_service(
        desiredCount=0,
        service=servce_name,
        cluster=cluster_name
    )
    print("Lets wait {} second for stopping tasks".format(s))
    time.sleep(s)
    ecs_client.delete_service(
        cluster=cluster_name,
        service=servce_name,
        force=True
    )
    ecs_client.delete_cluster(
        cluster=cluster_name
    )


def remove_task_definition(task_arn):
    ecs_client.deregister_task_definition(
        taskDefinition=task_arn
    )


def remove_tg(tg_arn):
    elb_client.delete_target_group(
        TargetGroupArn=tg_arn
    )


def remove_vpc(vpcid):
    ec2 = boto3.resource('ec2',
                         region_name=region,
                         aws_access_key_id=access_key,
                         aws_secret_access_key=secret_key)
    ec2client = ec2.meta.client
    vpc = ec2.Vpc(vpcid)
    for gw in vpc.internet_gateways.all():
        vpc.detach_internet_gateway(InternetGatewayId=gw.id)
        gw.delete()
    for rt in vpc.route_tables.all():
        for rta in rt.associations:
            if not rta.main:
                rta.delete()
    for subnet in vpc.subnets.all():
        for instance in subnet.instances.all():
            instance.terminate()
    for ep in ec2client.describe_vpc_endpoints(
            Filters=[{
                'Name': 'vpc-id',
                'Values': [vpcid]
            }])['VpcEndpoints']:
        ec2client.delete_vpc_endpoints(VpcEndpointIds=[ep['VpcEndpointId']])
    for sg in vpc.security_groups.all():
        if sg.group_name != 'default':
            sg.delete()
    for vpcpeer in ec2client.describe_vpc_peering_connections(
            Filters=[{
                'Name': 'requester-vpc-info.vpc-id',
                'Values': [vpcid]
            }])['VpcPeeringConnections']:
        ec2.VpcPeeringConnection(vpcpeer['VpcPeeringConnectionId']).delete()
    for netacl in vpc.network_acls.all():
        if not netacl.is_default:
            netacl.delete()
    for subnet in vpc.subnets.all():
        for interface in subnet.network_interfaces.all():
            interface.delete()
        subnet.delete()
    ec2client.delete_vpc(VpcId=vpcid)


region, access_key, secret_key, state_file, _ = parse_arguments()
if not state_file:
    print("For destroying infrastructure you must set --state-file which contains needed information")
    sys.exit(1)

ecs_client = boto3.client('ecs',
                          region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
ec2_client = boto3.client('ec2',
                          region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)
elb_client = boto3.client('elbv2',
                          region_name=region,
                          aws_access_key_id=access_key,
                          aws_secret_access_key=secret_key)

data = json.load(open(state_file))

print("Remove ALB")
remove_alb(data["albARN"])
print("Remove ECS cluster")
remove_cluster(data["clusterName"], data["serviceName"])
print("Remove task definition")
remove_task_definition(data["taskARN"])
print("Remove target group")
remove_tg(data["tgARN"])
print("Remove VPC")
s = 60
print("Lets wait {} seconds".format(s))
time.sleep(s)
remove_vpc(data["vpcID"])
print("Romove state file")
os.remove(state_file)