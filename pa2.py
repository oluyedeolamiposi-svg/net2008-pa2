# Name: Olamiposi Oluyede  Student ID: 041263044
import sys
import json
import xml.etree.ElementTree as ET 
from pathlib import Path
import yaml


class InputFileError(Exception):
    """Exception for file input errors"""
    pass
class Device:
    """a device in a network"""
    def __init__(self, device_id, a_role, an_os, an_owner, inter_faces):
        """device atribute"""
        self.device_id = device_id
        self.a_role = a_role
        self.an_os = an_os
        self.an_owner = an_owner
        self.inter_faces = inter_faces
    
    
    def count_interfaces(self):
        """count all interface status"""
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








def compare_versions(found, required):
    """Compare 2 dotted os versions"""
    found_parts = [int(part) for part in found.split(".")]
    required_parts = [int(part) for part in required.split(".")]

    while len(found_parts) < len(required_parts):
        found_parts.append(0)

    while len(required_parts) < len(found_parts):
        required_parts.append(0)

    return found_parts >= required_parts
    

def main():

    """run audit"""
    if len(sys.argv) != 3:
        print("usage: python pa2.py DEVICES.xml POLICY.yaml")
        sys.exit(2)

    xml_path = Path(sys.argv[1])
    yaml_path = Path(sys.argv[2])
    
    #Initiate counters and lists
    skipped_devices = 0
    interface_up = 0
    interface_down = 0
    other = 0
    total_interfaces = 0
    role_counts = {}
    devices = []
    unknown_role = []
    violations = []

    #xml part
    tree = ET.parse(xml_path)
    root = tree.getroot()

    root_site = root.get("site") 

    for child in root.findall("device"):

        child_id = child.get("id")

        if not child_id or not child_id.strip():
            skipped_devices += 1
            continue

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


 # yaml part 
    with open(yaml_path, "r") as file:
        data = yaml.safe_load(file)

    if data is None:
        data = {}

    if not isinstance(data, dict):
        raise InputFileError("Policy must be a YAML mapping")

    min_os = data.get("min_os")


    # Check device roles and OS versions
    for sub_device in devices:

        sub_role = sub_device.a_role


        if min_os is not None:

            if sub_role in min_os:
                required_os = min_os.get(sub_role)

                if not compare_versions(sub_device.an_os, required_os):
                    violations.append({
                        "device": sub_device.device_id,
                        "type": "os_outdated",
                        "found": sub_device.an_os,
                        "required": required_os
                    })

            else:
            
                unknown_role.append(sub_role)

                violations.append({
                    "device": sub_device.device_id,
                    "type": "unknown_role",
                    "role": sub_role
                })


        if data.get("require_owner") is True:
            if not sub_device.an_owner or not sub_device.an_owner.strip():
                violations.append({
                    "device": sub_device.device_id,
                    "type": "missing_owner"
                })

         # Check down interfaces
        max_down = data.get("max_down_interfaces")

        if max_down is not None:
            up, down, other_status = sub_device.count_interfaces()

            if down > max_down:
                violations.append({
                    "device": sub_device.device_id,
                    "type": "too_many_down",
                    "down": down
                })
    
 # Find devices with no violations
    devices_with_violations = []

    for violation in violations:
        devices_with_violations.append(violation["device"])

    compliant = []



    for device in devices:
        if device.device_id not in devices_with_violations:
            compliant.append(device.device_id)

    compliant.sort()
      # Create audit report
    audit_report = {
        "site": root_site,
        "total_devices": len(devices),
        "skipped_devices": skipped_devices,
        "roles": role_counts,
        "interfaces": {
            "up": interface_up,
            "down": interface_down,
            "other": other
        },
        "violations": violations,
        "compliant": compliant
    }
    #json
    with open("audit.json", "w") as file:
        json.dump(audit_report, file, indent=4)
     #print summary
    print("\nAudit complete.")
    print("Total devices:", len(devices))
    print("Violations:", len(violations))
    print("Compliant devices:", len(compliant))

if __name__ == "__main__":
    try:
        main()

    except FileNotFoundError as error:
        print(f"Error: file not found: {error.filename}")
        sys.exit(1)

    except ET.ParseError:
        print(f"Error: invalid XML file: {sys.argv[1]}")
        sys.exit(1)

    except yaml.YAMLError:
        print(f"Error: invalid YAML file: {sys.argv[2]}")
        sys.exit(1)
    except InputFileError as error:
        print(f"Error: {sys.argv[2]}: {error}")
        sys.exit(1)