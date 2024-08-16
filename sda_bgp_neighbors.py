#!/usr/bin/python3

# This script is to list the bgp neighbors for each VRF on the access switches.
# The output should be a table of VRF name, neighbor IP address, uptime/status.
# Usage: python3 sda_bgp_neighbors.py --testbed apac_tb.yaml
# Output apac_sda_bgp_status.txt shows the neighbor IP and uptime in each VRF.

import logging
import jinja2
from pyats import aetest
from genie.testbed import load

#TODO: Get the logger for script

log = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

#TODO: Connect to device
class CommonSetup(aetest.CommonSetup):
    @aetest.subsection
    def connect_to_device(self, testbed):
        for device_name, device in testbed.devices.items():
            log.info(f"Connecting to {device_name}")
            device.connect()

#TODO: Parse the cli "show ip bgp all" and write the output to a text file to double check. Make a list of BGP neighbors
class ShowBgp(aetest.Testcase):
    @aetest.test
    def show_bgp_neighbors(self, testbed):
        self.bgp_neighbors = {}
        for device_name, device in testbed.devices.items():
            log.info(f"{device_name} connected status: {device.connected}")
            log.info(f"Running the command 'show ip bgp vpnv4 all summary' for the device {device_name}")
            # Add the result of command to as the value of key "device_name"
            self.bgp_neighbors[device_name] = device.parse("show ip bgp vpnv4 all summary")
        log.info(self.bgp_neighbors)
        # Store the bgp neighbors as variable "bgp_neighbors", to use in other test cases
        self.parent.parameters['bgp_neighbors'] = self.bgp_neighbors
        
        # Output the result of command to a text file
        with open("show ip bgp all.txt", "w") as f:
            f.write(str(self.bgp_neighbors))           

#TODO: Display the BGP neighbors information as a table of VRF name, IP addess and uptime/status
class DisplayBgpNeighbors(aetest.Testcase):
    @aetest.test
    def collect_neighbors_info(self):
        bgp_neighbors = self.parent.parameters.get('bgp_neighbors', {})

        with open("apac_sda_bgp_neighbors.txt", "w") as fh:
            for device, bgp_info in bgp_neighbors.items():
                fh.write(f"******** BGP neighbors of {device} ********\n")
                fh.write("VRF Name            Neighbor IP         Uptime\n")
                fh.write("----------------------------------------------\n")
                bgp_status = []
                for vrf_name, vrf_data in bgp_info['vrf'].items():
                    log.info(f"Found VRF: {vrf_name}")            
                    for neighbor_IP, neighbor_info in vrf_data['neighbor'].items():
                        uptime = neighbor_info['address_family']['vpnv4']['up_down']
                        # Collect VRF, neighbor IP, and uptime/status in to a list
                        bgp_status.append(f"{vrf_name}\t{neighbor_IP}\t{uptime}")
        # Output the status of BGP neighbors    
                for line in bgp_status:
                    vrf_name, neighbor_IP, uptime = line.split('\t')
                    if uptime == 'never':
                        fh.write(f"{vrf_name.ljust(20)}{neighbor_IP.ljust(16)}{uptime.rjust(10)} <==== Need to check\n")
                    else:
                        fh.write(f"{vrf_name.ljust(20)}{neighbor_IP.ljust(16)}{uptime.rjust(10)}\n")
                fh.write("===============================================")
                fh.write(2*"\n")

#TODO: Disconnect to device
class CommonCleanup(aetest.CommonCleanup):
    @aetest.subsection
    def disconnect_from_device(self, testbed):
        for device_name, device in testbed.devices.items():
            log.info(f"Disconnecting from {device_name}")
            device.disconnect()

if __name__ == ("__main__"):
    import argparse
    from pyats.topology import loader

    parser = argparse.ArgumentParser()
    parser.add_argument('--testbed', dest='testbed', type=loader.load)
    args, unknown = parser.parse_known_args()

    aetest.main(**vars(args))

    


