import gzip
import datetime
import struct
import json
import os
from io import BufferedReader

dirname = os.path.dirname(__file__)

# FLAGS YOU SHOULD CHANGE BASED ON WHAT YOU WANT TO DO
EXPORT_JSON = False
LOCALE_IMPORT_PATH = "C:\\Program Files (x86)\\DC Studios\\Kenny vs Spenny - Versusville\\media\\prod\\kvs\\locales\\"
EXPORT_OBJ = True
OBJ_EXPORT_PATH = os.path.join(dirname, "")

# Print out the header
print("Versusville Locale Loader v1.1.0")
print("By: Carson Kompon and MoparJason")
print("")
print("This script will load a Versusville locale file and export it to a JSON file.")
print("There are some flags in the script you can change such as:")
print("EXPORT_JSON: Whether or not to export the map as a JSON file.")
print("LOCALE_IMPORT_PATH: The path of your Versusville \"locales\" folder.")
print("EXPORT_OBJ: Whether or not to also export the map as an OBJ file.")
print("OBJ_EXPORT_PATH: The folder to export OBJ files to.")
print("")

# Get the map ID
loaded_map = -1
while loaded_map < 2 or loaded_map > 7:
    loaded_map = int(input("Enter the map ID you want to load (2-7): "))

# Create OBJ export folder if it doesn't exist
if EXPORT_OBJ:
    if(not os.path.isdir(OBJ_EXPORT_PATH)):
        os.mkdir(OBJ_EXPORT_PATH)
    if(not os.path.isdir(OBJ_EXPORT_PATH + str(loaded_map))):
        os.mkdir(OBJ_EXPORT_PATH + str(loaded_map))
    OBJ_EXPORT_PATH + str(loaded_map)


# Load the main locale file into memory
file_input_stream = open(LOCALE_IMPORT_PATH + str(loaded_map) + "\\" + str(loaded_map) + ".dmg", "rb")
gzip_input_stream = gzip.GzipFile(fileobj=file_input_stream, mode='rb')
buffered_input_stream = BufferedReader(gzip_input_stream)

# Define a ton of functions for reading the locale file
def read_string():
    length = buffered_input_stream.read(2)
    length = int.from_bytes(length, byteorder='big')
    string = buffered_input_stream.read(length)
    return string.decode("utf-8")

def read_int():
    return int.from_bytes(buffered_input_stream.read(4), byteorder='big')

def read_short():
    return int.from_bytes(buffered_input_stream.read(2), byteorder='big')

def read_long():
    return int.from_bytes(buffered_input_stream.read(8), byteorder='big')

def read_bool():
    return buffered_input_stream.read(1) == b'\x01'

def read_float():
    return struct.unpack('>f', buffered_input_stream.read(4))[0]

def read_byte():
    return int.from_bytes(buffered_input_stream.read(1), byteorder='big')

# Recursive function for reading the BSP tree
def read_bsp():
    bsp_node = {}
    bsp_node["version"] = read_byte() # In Versusville, if this is < 4 then it will refuse to load
    bsp_node["node_count"] = read_int()
    bsp_node["ppe"] = []
    bsp_node["n_polys"] = []
    bsp_node["vertex_index"] = []
    bsp_node["front"] = []
    bsp_node["back"] = []
    bsp_node["tex_index"] = []
    bsp_node["i1"] = []
    bsp_node["i2"] = []
    for j in range(bsp_node["node_count"]):
        bsp_node["ppe"].append([read_float(), read_float(), read_float(), read_float()])
        bsp_node["n_polys"].append(read_short())
        vertex_index = []
        tex_index = []
        for k in range(bsp_node["n_polys"][j]):
            vertex_index.append(read_int())
            tex_index.append(read_short())
        bsp_node["vertex_index"].append(vertex_index)
        bsp_node["tex_index"].append(tex_index)
        bsp_node["front"].append(read_int())
        bsp_node["back"].append(read_int())
        bsp_node["i1"].append(read_byte())
        bsp_node["i2"].append(read_byte())
    return bsp_node

# Recursive function for reading the portal tree
def read_portal_vis_node():
    portal_vis_node = {}
    if(read_int() > 0):
        portal_vis_node["name"] = read_string()
    portal_vis_node["a"] = read_int()
    portal_var_size = read_int()
    portal_vis_node["b"] = []
    portal_vis_node["c"] = []
    for k in range(portal_var_size):
        portal_vis_node["b"].append(read_int())
        portal_vis_node["c"].append(read_portal_vis_node())
    return portal_vis_node

# Recursive function for reading the light tree
def read_light_tree():
    light_tree = {}
    light_tree["light_count"] = read_short()
    light_tree["light_list"] = []
    for j in range(light_tree["light_count"]):
        light_tree["light_list"].append(read_short())
    light_tree["x_mid"] = read_int()
    light_tree["y_mid"] = read_int()
    light_tree["z_mid"] = read_int()
    light_tree["light_quads"] = []
    for j in range(8):
        if(read_bool()):
            light_tree["light_quads"].append(read_light_tree())
    return light_tree

# Define function for exporting an OBJ from a map cell
def export_obj(map_cell):
    count = 0
    
    # Export Cell Materials at .mtl Files
    materialLines = []
    for tex in map_cell["texture_list"]:
        materialLines.append("newmtl " + tex.split("\\")[-1].split('.')[0])
        materialLines.append("Kd 1.000 1.000 1.000")
        materialLines.append(f"map_Kd {tex}")

    with open(OBJ_EXPORT_PATH + str(loaded_map) + '\\c' + str(i) + '.mtl', 'w') as f:
        for line in materialLines:
            f.write(line + "\n")
    print("Cell " + str(i) + " materials exported as " + OBJ_EXPORT_PATH + "c" + str(i) + ".mtl")

    # Get the faces
    faces = []
    current_face = 0
    for j in range(len(map_cell["texture_list"])):
        faces.append([])
    j = 0
    for k in range(0, len(map_cell["vertex"]), 3):
        if(current_face < len(map_cell["texture_list"])-1 and j == map_cell["face_start"][current_face + 1]):
            current_face += 1
        faces[current_face].append([k+1, k+2, k+3])
        j += 1

    # Export Cell as .obj
    with open(OBJ_EXPORT_PATH + str(loaded_map) + '\\c' + str(i) + '.obj', 'w') as f:
        f.write("mtllib c" + str(i) + ".mtl\n")

        for j in range(len(map_cell["texture_list"])):
            tex = map_cell["texture_list"][j]
            face_start = map_cell["face_start"][j]
            face_count = map_cell["face_count"][j]

            # Write the vertices
            for k in range(3*face_start, 3*face_start + 3*face_count):
                vertex = map_cell["vertex"][k]
                f.write(f"v {vertex[0]} {vertex[1]} {vertex[2]}\n")

        for j in range(len(map_cell["texture_list"])):
            tex = map_cell["texture_list"][j]
            face_start = map_cell["face_start"][j]
            face_count = map_cell["face_count"][j]

            if (j == 0):
                vertex = map_cell["vertex"]
                texcoord = map_cell["texcoord"]

            # Write the texture coordinates
            texcoord_jdd = []
            for k in range(2*face_start, 2*face_start + 2*face_count):
                # print(k)
                texcoord = map_cell["texcoord"][k]
                texcoord_jdd.append(texcoord[0])
                texcoord_jdd.append(texcoord[1])
                texcoord_jdd.append(texcoord[2])
                # print(len(texcoord))
            for k in range(len(texcoord_jdd) // 2):
                f.write(f"vt {texcoord_jdd[2*k]} {texcoord_jdd[2*k+1]}\n")


        for j in range(len(map_cell["texture_list"])):
            tex = map_cell["texture_list"][j]
            face_start = map_cell["face_start"][j]
            face_count = map_cell["face_count"][j]

            # Write the vertex colors
            for k in range(3*face_start, 3*face_start + (3*face_count)):
                color = map_cell["vertex_color"][k]
                f.write(f"vc {color[0]} {color[1]} {color[2]}\n")

        for j in range(0, len(map_cell["texture_list"])):
            tex = map_cell["texture_list"][j]
            face_start = map_cell["face_start"][j]
            face_count = map_cell["face_count"][j]

            #f.write("mtllib " + tex.split('\\')[-1].split('.')[0] + ".mtl\n")
            f.write("usemtl " + tex.split('\\')[-1].split('.')[0] + "\n")
            f.write("o " + tex.split('\\')[-1].split('.')[0] + "\n")
            f.write(" g " + tex.split('\\')[-1].split('.')[0] + "\n")

            # Write the faces
            for k in range(face_count):
                f.write(f"f {faces[j][k][0]}/{count+1} {faces[j][k][1]}/{count+2} {faces[j][k][2]}/{count+3}\n")
                count += 3


    print("Cell " + str(i) + " model exported as " + OBJ_EXPORT_PATH + "c" + str(i) + ".obj")

# Initialize map data object
map_data = {}

# Locale Data Version
# In Versusville, if this value is not 805 AND < 793, it will refuse to load the map.
map_data["locale_data_version"] = read_short()

# Locale ID
map_data["locale_id"] = read_int()

# World Name
map_data["world_name"] = read_string()

# Game Name (?)
map_data["game_name"] = ""
if(map_data["locale_data_version"] >= 800):
    map_data["game_name"] = read_string()

# Creation Date
map_data["creation_date"] = datetime.datetime.fromtimestamp(read_long() / 1000).strftime('%Y-%m-%d %H:%M:%S')

# Cell List Size
map_data["cell_list_size"] = read_int()

# Center Point
map_data["center_point"] = {
    "x": read_int(),
    "y": read_int(),
    "z": read_int()
}

# Width/Height/Depth
map_data["width"] = read_int()
map_data["height"] = read_int()
map_data["depth"] = read_int()

# Background Music
if(read_bool()):
    map_data["background_music"] = read_string()

# Channel Name
if(read_bool()):
    map_data["channel_name"] = read_string()

# Ban Mask
if(read_bool()):
    map_data["ban_mask"] = read_string()

# Channel Topic
if(read_bool()):
    map_data["channel_topic"] = read_string()

# Channel Settings (?)
map_data["max_irc_users"] = read_int()
map_data["is_private_channel"] = read_bool()
map_data["is_secret_channel"] = read_bool()
map_data["is_invite_only_channel"] = read_bool()
map_data["is_quiet_channel"] = read_bool()

# World Entries
world_entries_size = read_int()
world_entries = []
for i in range(world_entries_size):
    # World Entry
    world_entry = {}
    world_entry["name"] = read_string()
    world_entry["position"] = {
        "x": read_float(),
        "y": read_float(),
        "z": read_float()
    }
    world_entry["rotation"] = {
        "x": read_float(),
        "y": read_float(),
        "z": read_float()
    }
    world_entry["cell"] = read_string()
    world_entry["type"] = read_int()
    world_entries.append(world_entry)
map_data["world_entries"] = world_entries

# Ambient Light
map_data["ambient_light"] = {
    "r": read_float(),
    "g": read_float(),
    "b": read_float(),
    "a": read_float()
}

# Light Count
light_count = read_short()
if(light_count > 0):
    # Check if the map has lights and lightmaps
    map_data["has_lights"] = read_bool()
    if(map_data["locale_data_version"] >= 802):
        map_data["has_lightmaps"] = read_bool()
    else:
        map_data["has_lightmaps"] = map_data["has_lights"]

    lights = []
    for i in range(light_count):
        # Light
        light = {}
        light["type"] = read_byte()
        light["position"] = {
            "x": read_int(),
            "y": read_int(),
            "z": read_int()
        }
        light["intensity"] = read_float()
        light["color"] = {
            "r": read_short(),
            "g": read_short(),
            "b": read_short()
        }
        light["near"] = read_short()
        light["far"] = read_short()
        light["shadows"] = read_byte()
        light["name"] = read_string()
        excluded_cell_count = read_byte()
        if(excluded_cell_count > 0):
            light["excluded_cells"] = []
            for j in range(excluded_cell_count):
                light["excluded_cells"].append(read_string())
        lights.append(light)
    map_data["lights"] = lights

# Waypoint Count
waypoint_count = read_int()
if(waypoint_count > 0):
    waypoints = []
    for i in range(waypoint_count):
        # Waypoint
        waypoint = {}
        waypoint["list_index"] = i
        waypoint["position"] = {
            "x": read_float(),
            "y": read_float(),
            "z": read_float()
        }
        waypoint["cell_id"] = read_int()

        if(map_data["locale_data_version"] > 793):
            waypoint["sequence"] = read_int()
        
        if(map_data["locale_data_version"] > 800):
            linked_indices_count = read_int()
            if(linked_indices_count > 0):
                waypoint["link_indices"] = []
                for j in range(linked_indices_count):
                    waypoint["link_indices"].append(read_int())
        
        if(map_data["locale_data_version"] > 802):
            waypoint["group_id"] = read_int()
        
        if(map_data["locale_data_version"] > 804):
            waypoint["leading_id"] = read_int()
            waypoint["trailing_id"] = read_int()
            waypoint["racing_offset"] = read_float()
            waypoint["overtaking_offset"] = read_float()
        
        waypoint["type_flags"] = read_long()
        type_flag_string = ""
        addedFlag = False
        if(waypoint["type_flags"] & 1):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "NEVER_LINK"
            addedFlag = True
        if(waypoint["type_flags"] & 2):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "OBSTACLE"
            addedFlag = True
        if(waypoint["type_flags"] & 4):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "GOAL"
            addedFlag = True
        if(waypoint["type_flags"] & 8):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "FINISH"
            addedFlag = True
        if(waypoint["type_flags"] & 16):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "DEPART"
            addedFlag = True
        if(waypoint["type_flags"] & 32):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "DESTINATION"
            addedFlag = True
        if(waypoint["type_flags"] & 64):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "DETOUR"
            addedFlag = True
        if(waypoint["type_flags"] & 128):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "NEVER_COMPILE"
            addedFlag = True
        if(waypoint["type_flags"] & 256):
            if(addedFlag):
                type_flag_string += "| "
            type_flag_string += "SECTOR_NODE"
            addedFlag = True
        if(addedFlag == False):
            type_flag_string = "<none>"
        waypoint["type_flag_string"] = type_flag_string

        waypoints.append(waypoint)
    map_data["waypoints"] = waypoints

# Map Cells
map_cells = []

# Load all Map Cell files
for i in range(map_data["cell_list_size"]):
    # Load Map Cell file into stream
    file_input_stream = open(LOCALE_IMPORT_PATH + str(loaded_map) + "\\c" + str(i) + ".dmg", "rb")
    gzip_input_stream = gzip.GzipFile(fileobj=file_input_stream, mode='rb')
    buffered_input_stream = BufferedReader(gzip_input_stream)

    # Map Cell
    map_cell = {}

    # Map Cell Version
    # In Versusville, if this value is < 1297, the map cell is not loaded
    map_cell["map_cell_version"] = read_short()

    # Map Cell Position
    map_cell["position"] = {
        "x": read_int(),
        "y": read_int(),
        "z": read_int()
    }

    # Map Cell Size
    map_cell["width"] = read_int()
    map_cell["height"] = read_int()
    map_cell["depth"] = read_int()

    # Not quite sure what these are yet
    map_cell["xl"] = read_int()
    map_cell["xr"] = read_int()
    map_cell["yt"] = read_int()
    map_cell["yb"] = read_int()
    map_cell["zb"] = read_int()
    map_cell["zf"] = read_int()

    # Map Cell ID
    map_cell["id"] = read_int()

    # Map Cell Name
    map_cell["name"] = read_string()

    # Map Cell Face Information
    map_cell["total_face_count"] = read_int()
    map_cell["total_reg_faces"] = read_int()
    map_cell["total_alpha_faces"] = read_int()
    
    # Map Cell Texture Information
    map_cell["texture_count"] = read_short()
    map_cell["texture_alpha_count"] = read_short()
    
    # Map Cell Portal Count
    map_cell["portal_count"] = read_int()

    # Generic Map Cell Information
    if(map_cell["map_cell_version"] >= 1296):
        map_cell["gravity"] = read_float()
        map_cell["enable_combat"] = read_bool()
        map_cell["irc_channel"] = read_string()
    else:
        map_cell["gravity"] = 9.81
        map_cell["enable_combat"] = True
        map_cell["irc_channel"] = ""
    
    # Map Cell Face Start and Count
    map_cell["face_start"] = []
    map_cell["face_count"] = []
    map_cell["texture_list"] = []

    for j in range(map_cell["texture_count"]):
        map_cell["texture_list"].append("texture\\" + read_string())
        map_cell["face_start"].append(read_int())
        map_cell["face_count"].append(read_int())

    # Map Cell Alpha Face Start and Count
    map_cell["alpha_texture_list"] = []
    map_cell["alpha_face_count"] = []
    if(map_cell["texture_alpha_count"] > 0):
        for j in range(map_cell["texture_alpha_count"]):
            map_cell["alpha_texture_list"].append("texture\\" + read_string())
            map_cell["alpha_face_count"].append(read_int())
    
    # Vertex
    vertex_count = (map_cell["total_reg_faces"] + map_cell["portal_count"] * 2) * 9
    map_cell["vertex"] = []
    for j in range(0, vertex_count, 3):
        map_cell["vertex"].append([
            read_float(),
            read_float(),
            read_float()
        ])
    
    # Texcoord
    texcoord_count = map_cell["total_reg_faces"] * 6
    map_cell["texcoord"] = []
    for j in range(0, texcoord_count, 3):
        map_cell["texcoord"].append([
            read_float(),
            read_float(),
            read_float()
        ])
    
    # Vertex Color
    vertex_color_count = map_cell["total_reg_faces"] * 9
    map_cell["vertex_color"] = []
    if map_cell["map_cell_version"] >= 1298:
        for j in range(0, vertex_color_count, 3):
            map_cell["vertex_color"].append([
            read_float(),
            read_float(),
            read_float()
        ])
    else:
        for j in range(0, vertex_color_count, 3):
            map_cell["vertex_color"].append([
                read_float(),
                read_float(),
                read_float()
            ])
    
    # Alpha Vertex
    alpha_vertex_count = map_cell["total_alpha_faces"] * 9
    map_cell["alpha_vertex"] = []
    for j in range(0, alpha_vertex_count, 3):
        map_cell["alpha_vertex"].append([
            read_float(),
            read_float(),
            read_float()
        ])
    
    # Alpha Texcoord
    alpha_texcoord_count = map_cell["total_alpha_faces"] * 6
    map_cell["alpha_texcoord"] = []
    for j in range(0, alpha_texcoord_count, 3):
        map_cell["alpha_texcoord"].append([
            read_float(),
            read_float(),
            read_float()
        ])
    
    # Alpha Vertex Color
    alpha_vertex_color_count = map_cell["total_alpha_faces"] * 9
    map_cell["alpha_vertex_color"] = []
    if map_cell["map_cell_version"] >= 1298:
        for j in range(0, alpha_vertex_color_count, 3):
            map_cell["alpha_vertex_color"].append([
                read_float(),
                read_float(),
                read_float()
            ])
    else:
        for j in range(0, alpha_vertex_color_count, 3):
            map_cell["alpha_vertex_color"].append([
                read_float(),
                read_float(),
                read_float()
            ])
    
    # Load BSP Node
    if(read_bool()):
        map_cell["bsp_node"] = read_bsp()
    
    # Load Alpha BSP Node
    if(read_bool()):
        map_cell["alpha_bsp_node"] = read_bsp()

    # Portal Information
    map_cell["portal_plane"] = []
    map_cell["portal_center"] = []
    map_cell["portal_radius"] = []
    map_cell["portal_link"] = []
    map_cell["portal_name"] = []
    map_cell["portal_vis_node_list"] = []
    for j in range(map_cell["portal_count"]):
        map_cell["portal_plane"].append({
            "x": read_float(),
            "y": read_float(),
            "z": read_float(),
            "w": read_float()
        })
        map_cell["portal_center"].append({
            "x": read_float(),
            "y": read_float(),
            "z": read_float()
        })
        map_cell["portal_radius"].append(read_float())
        map_cell["portal_link"].append(read_int())
        map_cell["portal_name"].append(read_string())

        # Portal Vis Node
        map_cell["portal_vis_node_list"].append(read_portal_vis_node())

    # Light Tree
    if(read_bool()):
        map_cell["light_tree"] = read_light_tree()
    
    # Lightmap
    lightmap_count = read_int()
    map_cell["lightmap_list"] = []
    for j in range(lightmap_count):
        lightmap_n = read_int()
        current_list = []
        for k in range(65536):
            current_list.append(read_short())

        map_cell["lightmap_list"].append(current_list)
    if(len(map_cell["lightmap_list"]) > 0):
        l = map_cell["reg_face_count"] * 6
        map_cell["lightmap_texcoord"] = []
        for j in range(0, l, 3):
            map_cell["lightmap_texcoord"].append([
                read_float(),
                read_float(),
                read_float()
            ])
        map_cell["lightmap_tex_index"] = []
        for j in range(map_cell["texture_count"]):
            map_cell["lightmap_tex_index"].append(read_short())

        l = map_cell["alpha_face_count"] * 6
        map_cell["alpha_lightmap_texcoord"] = []
        for j in range(0, l, 3):
            map_cell["alpha_lightmap_texcoord"].append([
                read_float(),
                read_float(),
                read_float()
            ])
        map_cell["alpha_lightmap_tex_index"] = read_short()
    else:
        map_cell["lightmap_texcoord"] = map_cell["texcoord"]
        map_cell["alpha_lightmap_texcoord"] = map_cell["alpha_texcoord"]


    # Export OBJ
    if EXPORT_OBJ:
        export_obj(map_cell)

    map_cells.append(map_cell)
map_data["cells"] = map_cells

if(EXPORT_JSON):
    print("Now wait a few moments while the JSON file is constructed...")

    with open("map_data_" + str(loaded_map) + ".json", "w") as f:
        json.dump(map_data, f, indent=4)

    print("Map Data Saved Successfully as map_data_" + str(loaded_map) + ".json")