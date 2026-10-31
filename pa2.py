# Name: Olamiposi Oluyede  Student ID: 041263044
import sys
import json
import xml.etree.ElementTree as ET 
from pathlib import Path
import yaml

skipped_devices = 0
interface_up = 0
interface_down = 0
other = 0
total_interfaces = 0
role_counts = {}
devices = []

class InputFileError(Exception):
    """Exception for file input errors"""
    pass
class Device:
    """a device with its attributes"""
    def __init__(self, device_id, a_role, an_os, an_owner, inter_faces):
        self.device_id = device_id
        self.a_role = a_role
        self.an_os = an_os
        self.an_owner = an_owner
        self.inter_faces = inter_faces
    
    
    def count_interfaces(self):
        int_up = 0
        int_down = 0
        other_anyway = 0
        for inter_face in self.inter_faces:
            status = inter_face.get("status")
            if status == "up":
                int_up += 1
            elif status == "down":
                int_down +=1
            else:
                other_anyway +=1

        return int_up, int_down, other_anyway
         

#xml part
xml_path = Path("PA2_sample.xml")
tree = ET.parse(xml_path)
root = tree.getroot()

root_site = root.get("site") 

for child in root.findall("device"):

    child_id = child.get("id")

    if not child_id or not child_id.strip():
        skipped_devices += 1
        continue

    print(child_id)
    
    child_role = child.get("role")
    child_os = child.get("os")
    child_owner = child.findtext("owner")
    child_interfaces = child.findall("interface")

    device = Device(
        child_id,
        child_role,
        child_os,
        child_owner,
        child_interfaces
    )

    devices.append(device)

    role_counts[child_role] = role_counts.get(child_role, 0) + 1

    total_interfaces += len(child_interfaces)

    up, down, other_status = device.count_interfaces()

    interface_up += up
    interface_down += down
    other += other_status
    


  
 
# Print inventory summary
print("\n--- TIER 1 INVENTORY SUMMARY ---")
print("Site:", root_site)
print("Valid devices:", len(devices))
print("Skipped devices:", skipped_devices)

print("\nDevice roles:")
for role, count in role_counts.items():
    print(f"{role}: {count}")


print("\nTotal interfaces:", total_interfaces)
print("Up:", interface_up)
print("Down:", interface_down)
print("Other:", other)



    