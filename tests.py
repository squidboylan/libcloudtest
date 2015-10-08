from libcloud.compute.types import Provider
from libcloud.compute.providers import get_driver
import sys
import os

class DHCTest():

    def __init__(self, username, password, auth_url, project):
        self.instance_name = 'libcloudtestinst'
        self.security_group_name = 'libcloudtestgroup'
        self.volume_name = "testvolume"

        self.auth_username = username
        self.auth_password = password
        self.auth_url = auth_url
        self.project_name = project
        self.region_name = 'RegionOne'

    def test_all(self):
        self.connect()

        images = self.list_images()
        flavors = self.list_flavors()
        self.list_security_groups()

        image = self.get_image(images[0].id)
        flavor = self.get_flavor(flavors[0].id)
        security_group = self.create_security_group(self.security_group_name)

        self.list_instances()
        instance = self.launch_instance(image, flavor, self.instance_name,
                                        security_group)

        volume = self.create_volume(self.volume_name)

        unused_ip = self.create_floating_ip()
        self.attach_floating_ip(instance, unused_ip)
        self.detach_floating_ip(instance, unused_ip)
        self.delete_floating_ip(unused_ip)

        self.destroy_instance(instance)

        self.delete_security_group(security_group)
        self.destroy_volume(volume)

    # Auth to DreamCompute
    def connect(self):

        provider = get_driver(Provider.OPENSTACK)
        self.conn = provider(self.auth_username,
                        self.auth_password,
                        ex_force_auth_url=self.auth_url,
                        ex_force_auth_version='2.0_password',
                        ex_tenant_name=self.project_name,
                        ex_force_service_region=self.region_name)

    # Get a list of images and return it.
    def list_images(self):
        images = self.conn.list_images()

        return images

    # Get a list of flavors and return it.
    def list_flavors(self):
        flavors = self.conn.list_sizes()

        return flavors

    def list_security_groups(self):
        security_groups = self.conn.ex_list_security_groups()

        return security_groups

    # Get a list of instances and return it.
    def list_instances(self):
        instancelist = self.conn.list_nodes()

        return instancelist

    # Get the image that has the id passed in as an argument and return it
    def get_image(self, image_id):
        image = self.conn.get_image(image_id)

        return image

    # Get the flavor that has the id passed in as an argument and return it
    def get_flavor(self, flavor_id):
        flavor = self.conn.ex_get_size(flavor_id)

        return flavor

    # Launch an instance with the image, flavor, and name passed in as an
    # argument
    def launch_instance(self, image, flavor, name, security_group):
        instance = self.conn.create_node(name=name,
                                        image=image,
                                        size=flavor,
                                        ex_network="private-network")
                                        #ex_security_groups=[security_group])

        # Wait until the instance is running before continuing onto the rest of
        # the script
        self.conn.wait_until_running([instance])
        return instance

    # Create a floating IP from the first ip pool in the list of ip pools.
    # Return this IP so it can be attached to an instance later.
    def create_floating_ip(self):
        try:
            pool = self.conn.ex_list_floating_ip_pools()[0]
            unused_ip = pool.create_floating_ip()

        except:
            sys.exit(1)

        return unused_ip

    # Create a security group with 2 rules and return it.
    def create_security_group(self, security_group_name):
        security_group = self.conn.ex_create_security_group(
                            security_group_name, 'Test security group')

        if not self.conn.ex_create_security_group_rule(security_group, 'TCP',
                80, 80):
            sys.exit(1)

        if not self.conn.ex_create_security_group_rule(security_group, 'TCP',
                22, 22):
            sys.exit(1)

        return security_group

    # Create a 1GB volume and return it.
    def create_volume(self, volume_name):
        volume = self.conn.create_volume(1, volume_name)

        return volume

    # Attach the volume to the instance at /dev/sdb.
    def attach_volume(self, instance, volume):
        if not self.conn.attach_volume(instance, volume, "/dev/sdb"):
            sys.exit(1)

    # Attach the IP passed in as an argument to the instance passed in as an
    # argument
    def attach_floating_ip(self, instance, ip):
        if not self.conn.ex_attach_floating_ip_to_node(instance, ip):
            sys.exit(1)

    # Detach the IP passed in as an argument from the instance passed in as an
    # argument
    def detach_floating_ip(self, instance, ip):
        if not self.conn.ex_detach_floating_ip_from_node(instance, ip):
            sys.exit(1)

    # Detach the volume passed in as an argument from the node it is attached
    # to.
    def detach_volume(self, volume):
        if not self.conn.detach_volume(volume):
            sys.exit(1)

    # Delete the volume passed in as an argument.
    def destroy_volume(self, volume):
        if not self.conn.destroy_volume(volume):
            sys.exit(1)

    # Delete the floating IP passed in as an argument.
    def delete_floating_ip(self, ip):
        if not ip.delete():
            sys.exit(1)

    # Delete the security group passed in as an argument.
    def delete_security_group(self, security_group):
        if not self.conn.ex_delete_security_group(security_group):
            sys.exit(1)

    # Destroy the instance passed in as an argument.
    def destroy_instance(self, instance):
        if not instance.destroy():
            sys.exit(1)

# Grab auth info from environment variables
env = os.environ

username = env['OS_USERNAME']
password = env['OS_PASSWORD']
auth_url = env['OS_AUTH_URL']
project = env['OS_TENANT_NAME']

# many auth_urls include the version. this will strip the version
# declaration from the auth_url
if 'v2.0' in auth_url:
    auth_url = '/'.join(auth_url.split('v2.0')[:-1])

test = DHCTest(username, password, auth_url, project)
test.test_all()
