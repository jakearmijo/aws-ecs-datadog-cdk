from aws_cdk import (
    Duration,
    Stack,
    aws_iam as iam,
    aws_ecs as ecs,
    aws_ec2 as ec2,
    aws_autoscaling as asg,
)
from constructs import Construct
import os
from dotenv.main import load_dotenv

load_dotenv()

class AwsEcsDatadogCdkStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        role = iam.Role.from_role_arn(self, "Role", "arn:aws:iam::955785507024:role/ecsTaskExecutionRole",
            mutable=False
        )

        node_example_task_definition = ecs.Ec2TaskDefinition(self, "Node-Example-Task-Definition",
            network_mode=ecs.NetworkMode.BRIDGE,
            execution_role=role,
            family='cdk-node-example'
        )

        node_example_container = node_example_task_definition.add_container("Node-Example-Node-Container",
            # Use an image from DockerHub
            container_name='node-example-container-cdk',
            image=ecs.ContainerImage.from_registry("jakearmijo/example-1"),
            memory_limit_mib=300,
            cpu=256,
            port_mappings=[ecs.PortMapping(container_port=80, host_port=80)]
        )

        datadog_agent_task_definition = ecs.Ec2TaskDefinition(self, "CDK-Datadog-Agent-Task-Definition",
            network_mode=ecs.NetworkMode.BRIDGE,
            execution_role=role,
            family='cdk-datadog-agent'
        )

        data_dog_agent_container = datadog_agent_task_definition.add_container("CDK-Datadog-Agent-Container",
            # Use an image from DockerHub
            container_name='datadog-agent-container-cdk',
            image=ecs.ContainerImage.from_registry("datadog/agent"),
            memory_limit_mib=512,
            cpu=256,
            health_check=ecs.HealthCheck(
                command=["CMD-SHELL", "agent health"],
                # the properties below are optional
                interval=Duration.seconds(30),
                retries=3,
                start_period=Duration.seconds(15),
                timeout=Duration.seconds(5)
            ),
        )
        data_dog_agent_container.add_environment('DD_API_KEY',os.getenv('DD_API_KEY'))
        data_dog_agent_container.add_environment('DD_PROCESS_AGENT_ENABLED','true')
        data_dog_agent_container.add_environment('DD_SITE','datadoghq.com')

        mount_point_docker_sock = ecs.MountPoint(
            container_path="/var/run/docker.sock",
            read_only=True,
            source_volume="docker_sock"
        )
        mount_point_c_group = ecs.MountPoint(
            container_path="/host/sys/fs/cgroup",
            read_only=True,
            source_volume="cgroup"
        )
        mount_point_host_proc = ecs.MountPoint(
            container_path="/host/proc",
            read_only=True,
            source_volume="proc"
        )

        data_dog_agent_container.add_mount_points(mount_point_docker_sock, mount_point_c_group, mount_point_host_proc)

        datadog_agent_task_definition.add_volume(name='docker_sock', host=ecs.Host(
            source_path="/var/run/docker.sock"
        ))
        datadog_agent_task_definition.add_volume(name='proc', host=ecs.Host(
            source_path="/proc/"
        ))
        datadog_agent_task_definition.add_volume(name='cgroup', host=ecs.Host(
            source_path="/sys/fs/cgroup/"
        ))

        # If you have an existing security group you want to use in your CDK application, you would import it like this:
        existing_security_group = ec2.SecurityGroup.from_security_group_id(self, "SG", "sg-12345",
            mutable=False
        )

        # exisiting_cluster = ecs.Cluster.from_cluster_arn(self,id="enter_id_for_cluster", cluster_arn="12345678")
        # exisiting_cluster_with_attributes = ecs.Cluster.from_cluster_attributes(
        #   self,
        #   id="enter_id_for_cluster", 
        #   cluster_arn="enter_cluster_arn", 
        #   security_groups=ec2.SecurityGroup.from_security_group_id(self, "SG", "enter_security_group_id",mutable=False),
        #   vpc=ec2.Vpc.from_lookup(self, "CDK-Datadog-VPC", vpc_name='enter_name_for_vpc'),
        #   autoscaling_group=asg.from_auto_scaling_group_name(scope, id, auto_scaling_group_name)
        # )


        cdk_example_cluster = ecs.Cluster(self, "CDK-Example-Cluster", vpc=ec2.Vpc.from_lookup(self, "CDK-Datadog-VPC", vpc_name='datadog-eval-1'))
        cdk_example_cluster.add_capacity(id='CDK-Example-Cluster-AutoScalingGroup',instance_type=ec2.InstanceType.of(ec2.InstanceClass.T2, ec2.InstanceSize.MICRO))

        cdk_node_example_service = ecs.Ec2Service(self, "CDK-Node-Example-Service", cluster=cdk_example_cluster, task_definition=node_example_task_definition)
        cdk_datadog_agent_example_service = ecs.Ec2Service(self, "CDK-Datadog-Agent-Service", cluster=cdk_example_cluster, task_definition=datadog_agent_task_definition, daemon=True)