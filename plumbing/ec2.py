# Built-in modules #
import os

# Internal modules #
from plumbing.cache import property_cached

# Third party modules #
import boto3

###############################################################################
class InstanceEC2(object):
    """An EC2 instance provided by Amazon Web Services."""

    def __init__(self, instance_id, profile=None):
        # Basic attributes #
        self.instance_id  = instance_id
        self.profile      = profile
        # If we want a different profile set it in boto3 #
        if self.profile: boto3.setup_default_session(profile_name=self.profile)
        # Make the object we will use for queries #
        self.ec2 = boto3.client('ec2')

    #------------------------------ Properties -------------------------------#
    @property_cached
    def response(self):
        """Get the state of the instance"""
        return self.ec2.describe_instances(InstanceIds=[self.instance_id])

    @property
    def instance_info(self):
        """Get the information of the instance"""
        return self.response['Reservations'][0]['Instances'][0]

    @property
    def machine_off(self):
        """Is the machine stopped?"""
        return self.instance_info['State']['Code'] == 80

    @property
    def machine_on(self):
        """Is the machine running?"""
        return self.instance_info['State']['Code'] == 16

    @property
    def is_in_transition(self):
        """Is the machine transitioning?"""
        return not self.machine_off and not self.machine_on

    @property
    def dns(self):
        return self.instance_info['PublicDnsName']

    @property
    def tags(self):
        return self.instance_info['Tags']

    @property
    def instance_name(self):
        return [i['Value'] for i in self.tags if i['Key']=='Name'][0]

    #------------------------------- Methods ---------------------------------#
    def refresh_info(self):
        """Update the instance information that we cache."""
        del self.response

    def start_machine(self):
        """Start it up."""
        self.ec2.start_instances(InstanceIds=[self.instance_id])

    def rename(self, name):
        """Set the name of the machine."""
        self.ec2.create_tags(Resources = [self.instance_id],
                             Tags      = [{'Key':   'Name',
                                           'Value':  name}])
        self.refresh_info()

    def update_ssh_config(self, path="~/.ssh/config"):
        """Put the DNS into the ssh config file."""
        # Read the config file #
        import sshconf
        config = sshconf.read_ssh_config(os.path.expanduser(path))
        # In case it doesn't exist #
        if not config.host(self.instance_name): config.add(self.instance_name)
        # Add the new DNS #
        config.set(self.instance_name, Hostname=self.dns)
        # Write result #
        config.write(os.path.expanduser(path))