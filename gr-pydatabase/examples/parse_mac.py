import json

def get_subtype_ctrl(subtype):
    switcher = {
        0: "Reserved",
        1: "Reserved",
        2: "Trigger",
        3: "TACK",
        4: "Beamforming Report Poll",
        5: "VHT/HE NDP Announcement",
        6: "Control Frame Extension",
        7: "Control Wrapper",
        8: "Block Ack Request (BAR)",
        9: "Block Ack (BA)",
        10: "PS-Poll",
        11: "RTS",
        12: "CTS",
        13: "ACK",
        14: "CF-End",
        15: "CF-End + CF-ACK",
    }
    return switcher.get(subtype, "Unknown")

def get_type(frame_type, frame_subtype):
    if frame_type == 0:
        frame_type_str = "Management"
        frame_subtype_str = get_subtype_mgmt(frame_subtype)
    elif frame_type == 1:
        frame_type_str = "Control"
        frame_subtype_str = get_subtype_ctrl(frame_subtype)
    elif frame_type == 2:
        frame_type_str = "Data"
        frame_subtype_str = get_subtype_data(frame_subtype)
    else:
        frame_type_str = "Extension"
        frame_subtype_str = get_subtype_extn(frame_subtype)
    return frame_type_str, frame_subtype_str


header_vector = [212, 0, 0, 0, 255, 255, 255, 255, 255, 255]

hex_list = [hex(i) for i in header_vector]

frame_ctrl = str(hex_list[0])
frame_ctrl_bin = format(int(frame_ctrl, 16), "08b")

frame_subtype = int(frame_ctrl_bin[:4], 2)
frame_type = int(frame_ctrl_bin[5:6], 2)
version = int(frame_ctrl_bin[7:], 2)

frame_type_str = get_type(frame_type, frame_subtype)
duration = int(header_vector[2] + header_vector[3])
addr1 = ":".join([i.lstrip("0x") for i in hex_list[4:10]])
addr2 = ":".join([i.lstrip("0x") for i in hex_list[10:16]])
addr3 = ":".join([i.lstrip("0x") for i in hex_list[16:22]])

header_dict = dict()
header_dict["frame_subtype"] = frame_subtype
header_dict["frame_type"] = frame_type
header_dict["version"] = version
header_dict["duration"] = duration
header_dict["addr1"] = addr1        # Receiver
header_dict["addr2"] = addr2        # Sender
header_dict["addr3"] = addr3        # Filtering

header_json = json.dumps(header_dict)