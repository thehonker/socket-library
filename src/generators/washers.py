import subprocess
import os
import re
import shutil

from os import makedirs

import textwrap
import yaml

USE_COLORSCAD_DOCKER = True
COLORSCAD_DOCKER_IMAGE = "ghcr.io/thehonker/colorscad:latest"


# Function to find openscad executable
def find_openscad():
    search_folders = [
        "/usr/bin",
        "/usr/local/bin" "C:\\Program Files",
        "C:\\Program Files (x86)",
        "/Applications/OpenSCAD.app/Contents/MacOS/",
    ]
    for folder in search_folders:
        for root, dirs, files in os.walk(folder):
            if "openscad" in files:
                return os.path.join(root, "openscad")
            if "openscad.exe" in files:
                return os.path.join(root, "openscad.exe")
            if "OpenSCAD" in files:
                return os.path.join(root, "OpenSCAD")
    return None


def text_to_metric(text):
    # Remove all letters from the text
    text = re.sub(r"[A-Za-z]", "", text)
    if text.find("/") == -1:
        return float(text)
    parts = text.split()
    if len(parts) == 2:
        whole_number = int(parts[0])
        numerator, denominator = map(int, parts[1].split("/"))
        inches = whole_number + numerator / denominator
    elif len(parts) == 1 and "/" in parts[0]:
        numerator, denominator = map(int, parts[0].split("/"))
        inches = numerator / denominator
    else:
        inches = float(parts[0])
    return inches * 25.4


def calculateWidth(engrave_text, min_width, adjust_for_socket, wall_thickness):
    inputWidth = min_width
    if adjust_for_socket:
        inputWidth = text_to_metric(engrave_text)
    width = inputWidth + (2 * wall_thickness)
    if inputWidth < min_width:
        width = min_width + (2 * wall_thickness)
    print(width)
    return width


def generate_openscad_code(
    lib_dir,
    config,
):
    width = calculateWidth(
        config["engrave_text"],
        config["min_width"],
        config["adjust_for_socket"],
        config["wall_thickness"],
    )
    code = textwrap.dedent(
        f"""\
        // use <{lib_dir}/fillets3d.scad>;

        edge_thickness = {config["edge_thickness"]};
        engrave_depth = {config["engrave_depth"]};;
        engrave_text = "{config["engrave_text"]}";
        height = {config["height"]};
        hole_diameter = {config["hole_diameter"]};
        letter_offset = {config["letter_offset"]};
        thickness = {config["thickness"]};
        width = {width};

        module plate() {{
            difference() {{
                union() {{
                    translate([0, 0, (thickness * 2)])
                        cube([width, height, thickness]);
                    translate([0, height, (thickness * 2)])
                        cube([width, edge_thickness, (edge_thickness * 2)]);
                    translate([0, -edge_thickness, (thickness * 2)])
                        cube([width, edge_thickness, (edge_thickness * 2)]);
                }}
                translate([(width / 2), (height / 2), (thickness * 2)])
                    cylinder(r=(hole_diameter / 2), h=(thickness * 2.2), center=true);
            }}
        }}

        module text1() {{
            translate([(width/2), letter_offset, (thickness*2)])
            linear_extrude(height = engrave_depth)
            mirror(v=[0,1,0])
            text(engrave_text, valign="center", halign="center", size=8, font = "Calibri:style=Bold");
        }}

        module text2() {{
            translate([(width/2), height-letter_offset, (thickness*2)])
            rotate([0, 0, 180])
            linear_extrude(height = engrave_depth)
            mirror(v=[0,1,0])
            text(engrave_text, valign="center", halign="center", size=8, font = "Calibri:style=Bold");
        }}

        module rectangle_with_hole() {{
            union() {{
                translate([0, 0, 0])
                color([0,0,0])
                    plate();
                translate([0, 0, 0])
                color([1,1,1])
                    text1();
                translate([0, 0, 0])
                color([1,1,1])
                    text2();
            }}
        }}
        rectangle_with_hole();
    """
    )
    return code


def main():
    # Locate openscad executable
    openscad_path = find_openscad()
    if openscad_path is None:
        print("Could not find openscad binary")
        return

    script_dir = os.path.dirname(os.path.abspath(__file__))

    with open(os.path.join(script_dir, "washers.yaml"), "r") as file:
        config = yaml.safe_load(file)

    # Iterate over the configuration to find the drive configuration
    for drive_config in config["washers"]:  # Updated this line to iterate over the list
        if "params" in drive_config and "texts" in drive_config:
            name = drive_config["name"]
            params = drive_config["params"]
            texts = drive_config["texts"]

            stl_out_dir = os.path.join(script_dir, "out", name)
            scad_out_dir = os.path.join(script_dir, "out", name, "scad")

            if config.get("options", {}).get("clear_output_dir", False):
                if os.path.exists(stl_out_dir):
                    shutil.rmtree(stl_out_dir)

            makedirs(stl_out_dir, exist_ok=True)
            makedirs(scad_out_dir, exist_ok=True)

            for text in texts:
                sanitized_text = text.replace(" ", "_").replace("/", "_")
                scad_filename = f"washer_{sanitized_text}.scad"
                scad_filepath = f"{scad_out_dir}/{scad_filename}"
                stl_filename = f"washer_{sanitized_text}.stl"
                stl_filepath = f"{stl_out_dir}/{stl_filename}"

                washer_config = {
                    "adjust_for_socket": params.get("adjust_for_socket", False),
                    "edge_thickness": params.get("edge_thickness"),
                    "engrave_depth": params.get("engrave_depth"),
                    "engrave_text": text,
                    "height": params.get("height"),
                    "hole_diameter": params.get("hole_diameter"),
                    "letter_offset": params.get("letter_offset"),
                    "min_width": params.get("min_width"),
                    "thickness": params.get("thickness"),
                    "wall_thickness": params.get("wall_thickness"),
                }

                if USE_COLORSCAD_DOCKER:
                    with open(scad_filepath, "w") as file:
                        file.write(
                            generate_openscad_code(
                                "/workspace/lib",
                                washer_config,
                            )
                        )
                    output_filename = f"washer_{sanitized_text}.3mf"
                    subprocess.run(
                        [
                            "docker",
                            "run",
                            "--rm",
                            "--pull=always",
                            f"-v{script_dir}:/workspace:rw",
                            COLORSCAD_DOCKER_IMAGE,
                            "/bin/bash",
                            "-c",
                            textwrap.dedent(
                                f"""\
                                    /usr/local/bin/colorscad \\
                                        -i /workspace/out/{name}/scad/{scad_filename} \\
                                        -o /workspace/out/{name}/{output_filename}
                                """
                            ),
                        ]
                    )


if __name__ == "__main__":
    main()
