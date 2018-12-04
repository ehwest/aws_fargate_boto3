from shared_functions import parse_arguments
import boto3
import os
import json
import time


def write_state(vpcID=None,
                albARN=None,
                tgARN=None,
                clusterARN=None,
                clusterName=None,
                taskARN=None,
                serviceARN=None,
                serviceName=None):
    if os.path.isfile(states_dir + global_identifier):
        print("WARNING: State {} already exists!".format(global_identifier))
        return
    else:
        with open(states_dir + global_identifier, "w") as newfile:
            result = {"vpcID": vpcID,
                      "albARN": albARN,
                      "tgARN": tgARN,
                      "clusterARN": clusterARN,
                      "clusterName": clusterName,
                      "taskARN": taskARN,
                      "serviceARN": serviceARN,
                      "serviceName": serviceName}
            newfile.write(json.dumps(result))
            print("SUCCESS: State {} save on disk".format(states_dir + global_identifier))


def create_network():
    vpc = ec2_client.create_vpc(CidrBlock='192.168.0.0/16')
    vpcID = vpc["Vpc"]["VpcId"]
    ig = ec2_client.create_internet_gateway()
    igID = ig["InternetGateway"]["InternetGatewayId"]
    ec2_client.attach_internet_gateway(InternetGatewayId=igID,
                                       VpcId=vpcID)
    #rt = ec2_client.create_route_table(VpcId=vpcID)
    #rtID = rt["RouteTable"]["RouteTableId"]
    all_rt = ec2_client.describe_route_tables(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [
                    vpcID,
                ]
            },
        ],
    )
    rtID = all_rt["RouteTables"][0]["Associations"][0]["RouteTableId"]
    ec2_client.create_route(DestinationCidrBlock='0.0.0.0/0',
                            GatewayId=igID,
                            RouteTableId=rtID)
    subnet_a = ec2_client.create_subnet(
        AvailabilityZone=region + "a",
        CidrBlock='192.168.1.0/24',
        VpcId=vpcID)
    ec2_client.modify_subnet_attribute(MapPublicIpOnLaunch={'Value': True},
                                       SubnetId=subnet_a["Subnet"]["SubnetId"])
    subnet_b = ec2_client.create_subnet(
        AvailabilityZone=region + "b",
        CidrBlock='192.168.2.0/24',
        VpcId=vpcID)
    ec2_client.modify_subnet_attribute(MapPublicIpOnLaunch={'Value': True},
                                       SubnetId=subnet_b["Subnet"]["SubnetId"])
    return vpcID, [subnet_a["Subnet"]["SubnetId"], subnet_b["Subnet"]["SubnetId"]]


def create_security_group(vpcID):
    conteinerSG = ec2_client.create_security_group(
        Description='upw for ssh',
        GroupName='upw-ssh',
        VpcId=vpcID)
    containerSGID = conteinerSG["GroupId"]
    ec2_client.authorize_security_group_ingress(GroupId=containerSGID,
                                                FromPort=22,
                                                ToPort=80,
                                                IpProtocol="tcp",
                                                CidrIp="192.168.0.0/16")

    albSG = ec2_client.create_security_group(
        Description='upw for http',
        GroupName='upw-hhtp',
        VpcId=vpcID)
    albSGID = albSG["GroupId"]
    ec2_client.authorize_security_group_ingress(GroupId=albSGID,
                                                FromPort=80,
                                                ToPort=80,
                                                IpProtocol="tcp",
                                                CidrIp="0.0.0.0/0")
    return [containerSGID, albSGID]


def create_target_group(name, vpcID):
    tg = elb_client.create_target_group(
        Name=name,
        Port=80,
        Protocol='HTTP',
        VpcId=vpcID,
        TargetType='ip'
    )
    return tg["TargetGroups"][0]["TargetGroupArn"]


def create_alb(name, sg, subnets, tgARN):
    alb = elb_client.create_load_balancer(
        Type="application",
        Name=name,
        Subnets=subnets,
        SecurityGroups=[sg,]
    )
    albARN = alb["LoadBalancers"][0]["LoadBalancerArn"]
    dns = alb["LoadBalancers"][0]["DNSName"]
    listener = elb_client.create_listener(LoadBalancerArn=albARN,
                                          Protocol="HTTP",
                                          Port=80,
                                          DefaultActions=[
                                              {
                                                  'Type': 'forward',
                                                  'TargetGroupArn': tgARN
                                              }
                                          ])
    print(dns)
    return albARN


def create_fargate_cluster(name):
    cluster = ecs_client.create_cluster(clusterName=name)
    return cluster["cluster"]["clusterArn"]


def create_fargate_task_definition():
    task = ecs_client.register_task_definition(
        family=task_definition_name,
        # taskRoleArn='string',
        # executionRoleArn='string',
        networkMode='awsvpc',  # 'bridge'|'host'|'awsvpc'|'none'
        containerDefinitions=[
            {
                'name': container_name,
                'image': container_image,
                # 'repositoryCredentials': {
                #    'credentialsParameter': 'string'
                # },
                'cpu': 256,
                'memory': 512,
                # 'memoryReservation': 123,
                # 'links': [
                #    'string',
                # ],
                'portMappings': [
                    {
                        'containerPort': 80,
                        # 'hostPort': 80, # or you can remove it because its not in use
                        'protocol': 'tcp'
                    },
                ],
                'essential': True,
                # 'entryPoint': [
                #    'string',
                # ],
                #'command': [
                #    ''
                #],
                # 'environment': [
                #    {
                #        'name': 'string',
                #        'value': 'string'
                #    },
                # ],
                ######################################
                #'mountPoints': [
                #    {
                #       'sourceVolume': 'database',
                #       'containerPath': '/var/lib/mysql',
                #       'readOnly': False     # True|False
                #    },
                #    {
                #        'sourceVolume': 'database-logs',
                #        'containerPath': '/var/log/mysql',
                #        'readOnly': False     # True|False
                #    },
                #    {
                #        'sourceVolume': 'apache-logs',
                #        'containerPath': '/var/log/apache2',
                #        'readOnly': False     # True|False
                #    },
                #],
                ################################################
                # 'volumesFrom': [
                #    {
                #        'sourceContainer': 'string',
                #        'readOnly': True|False
                #    },
                # ],
                # 'linuxParameters': {
                #    'capabilities': {
                #        'add': [
                #            'string',
                #        ],
                #        'drop': [
                #            'string',
                #        ]
                #    },
                #    'devices': [
                #        {
                #            'hostPath': 'string',
                #            'containerPath': 'string',
                #            'permissions': [
                #                'read'|'write'|'mknod',
                #                ]
                #        },
                #    ],
                #    'initProcessEnabled': True|False,
                #    'sharedMemorySize': 123,
                #    'tmpfs': [
                #        {
                #            'containerPath': 'string',
                #            'size': 123,
                #            'mountOptions': [
                #                'string',
                #            ]
                #        },
                #    ]
                # },
                # 'secrets': [
                #    {
                #        'name': 'string',
                #        'valueFrom': 'string'
                #    },
                # ],
                # 'hostname': 'string',
                # 'user': 'string',
                # 'workingDirectory': 'string',
                # 'disableNetworking': True|False,
                # 'privileged': True|False,
                # 'readonlyRootFilesystem': True|False,
                # 'dnsServers': [
                #    'string',
                # ],
                # 'dnsSearchDomains': [
                #    'string',
                # ],
                # 'extraHosts': [
                #    {
                #        'hostname': 'string',
                #        'ipAddress': 'string'
                #    },
                # ],
                # 'dockerSecurityOptions': [
                #    'string',
                # ],
                # 'interactive': True|False,
                # 'pseudoTerminal': True|False,
                # 'dockerLabels': {
                #    'string': 'string'
                # },
                # 'ulimits': [
                #    {
                #        'name': 'core'|'cpu'|'data'|'fsize'|'locks'|'memlock'|'msgqueue'|'nice'|'nofile'|'nproc'|'rss'|'rtprio'|'rttime'|'sigpending'|'stack',
                #        'softLimit': 123,
                #        'hardLimit': 123
                #    },
                # ],
                # 'logConfiguration': {
                #    'logDriver': 'json-file'|'syslog'|'journald'|'gelf'|'fluentd'|'awslogs'|'splunk',
                #    'options': {
                #        'string': 'string'
                #    }
                # },
                # 'healthCheck': {
                #    'command': [
                #        'string',
                #    ],
                #    'interval': 123,
                #    'timeout': 123,
                #    'retries': 123,
                #    'startPeriod': 123
                # },
                # 'systemControls': [
                #    {
                #        'namespace': 'string',
                #        'value': 'string'
                #    },
                # ]
            },
        ],
        #############################################
        #volumes=[
        #    {
        #        'name': 'database',
        #        'host': {},
        #    },
        #    {
        #        'name': 'database-logs',
        #        'host': {},
        #    },
        #    {
        #        'name': 'apache-logs',
        #        'host': {},
        #    },
        #],
        #################################################
        #            'sourcePath': 'string'
        #        },
        #        'dockerVolumeConfiguration': {
        #            'scope': 'task'|'shared',
        #            'autoprovision': True|False,
        #            'driver': 'string',
        #            'driverOpts': {
        #                'string': 'string'
        #            },
        #            'labels': {
        #                'string': 'string'
        #            }
        #        }
        #    },
        #],
        # placementConstraints=[
        #    {
        #        'type': 'memberOf',
        #        'expression': 'string'
        #    },
        # ],
        requiresCompatibilities=[
            'FARGATE',  # 'EC2'|'FARGATE',
        ],
        cpu='256',
        memory='512',
        # tags=[
        #    {
        #        'key': 'string',
        #        'value': 'string'
        #    },
        # ],
        # pidMode='host'|'task',
        # ipcMode='host'|'task'|'none'
    )
    return task["taskDefinition"]["taskDefinitionArn"]


def create_fargate_service(tgARN, subnets, sgID):
    service = ecs_client.create_service(
        cluster=cluster_name,
        serviceName=service_name,
        taskDefinition=task_definition_name,
        loadBalancers=[
            {
                'targetGroupArn': tgARN,
                # 'loadBalancerName': lb_name,
                'containerName': container_name,
                'containerPort': 80
            },
        ],
        # serviceRegistries=[
        #    {
        #        'registryArn': 'string',
        #        'port': 123,
        #        'containerName': 'string',
        #        'containerPort': 123
        #    },
        # ],
        desiredCount=1,
        # clientToken='string',
        launchType='FARGATE',  # 'EC2'|'FARGATE'
        platformVersion='LATEST',
        # role='string',
        # deploymentConfiguration={
        #    'maximumPercent': 123,
        #    'minimumHealthyPercent': 123
        # },
        # placementConstraints=[
        #    {
        #        'type': 'distinctInstance'|'memberOf',
        #        'expression': 'string'
        #    },
        # ],
        # placementStrategy=[
        #    {
        #        'type': 'random'|'spread'|'binpack',
        #        'field': 'string'
        #    },
        # ],
        networkConfiguration={
            'awsvpcConfiguration': {
                'subnets': subnets,
                'securityGroups': [
                    sgID,
                ],
                'assignPublicIp': 'ENABLED'  # 'ENABLED'|'DISABLED'
            }
        },
        healthCheckGracePeriodSeconds=60,
        schedulingStrategy='REPLICA',  # 'REPLICA'|'DAEMON'
        # deploymentController = {
        #    'type': 'ECS', #'ECS'|'CODE_DEPLOY'
        # },
        # tags=[
        #    {
        #        'key': 'string',
        #        'value': 'string'
        #    },
        # ],
        # enableECSManagedTags=True|False,
        # propagateTags='TASK_DEFINITION'|'SERVICE'
    )
    return service["service"]["serviceArn"]


global_identifier = str(int(time.time()))
states_dir = "states/"

cluster_name = "upw-test"
service_name = cluster_name + "-service"
task_definition_name = cluster_name + "-task-definition"
container_name = "mysql-phpmyadmin"
container_image = "wnameless/mysql-phpmyadmin:latest"
region, access_key, secret_key, _, _ = parse_arguments()


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

print("Create Network (VPC, Subnets)")
vpcID, subnets = create_network()
print("Create Security Groups")
containerSGID, albSGID = create_security_group(vpcID)
print("Create Target Group")
tgARN = create_target_group("upw-test", vpcID)
print("Create ALB")
albARN = create_alb("upw-test", albSGID, subnets, tgARN)
print("Create cluser")
clusterARN = create_fargate_cluster(cluster_name)
print("Create task definition")
taskARN = create_fargate_task_definition()
print("Create service")
serviceARN = create_fargate_service(tgARN, subnets, containerSGID)

write_state(vpcID=vpcID,
            albARN=albARN,
            tgARN=tgARN,
            clusterARN=clusterARN,
            clusterName=cluster_name,
            taskARN=taskARN,
            serviceARN=serviceARN,
            serviceName=service_name)

# to delete: VPC, ALB, TG, CLUSTER (need stop all tasks), task defenition

