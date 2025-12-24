import argparse
import subprocess
import os
import re
#python clampHolder.py --id_start 1 --id_end 25.4 --increment .5 --nut_size 15.875
# Function to find openscad executable
def find_openscad():
    search_folders = ['C:\\Program Files', 'C:\\Program Files (x86)']
    for folder in search_folders:
        for root, dirs, files in os.walk(folder):
            if 'openscad.exe' in files:
                return os.path.join(root, 'openscad.exe')
    return None
    
def generate_openscad_code(inner_diameter, nut_size):
    code = f"""
    use <fillets3d.scad>;

    cradle_y={nut_size};
    cradle_wall_thickness=3;
    cradle_id={inner_diameter};
    bottom_height = cradle_id/2 + 3; //to bottom of cylinder
    cradle_x=cradle_id + cradle_wall_thickness;
    cradle_height = bottom_height+(cradle_id/2);

    translate([0,0,-0]){{
        rotate([0,270,90])
        import(\"E:/1_2_socket_holder/v2 profile/holders/1-2 inch holder base.STL\");
    }};
    topFillet( t = cradle_height, r = 2, s = 15){{
        difference(){{
            translate([0,0,cradle_height/2]){{
                cube([cradle_x,cradle_y,cradle_height], center = true);
            }};
            translate([0,0,cradle_height - cradle_id/3]){{
                rotate([90,90,0])
                cylinder(h=cradle_y, d = cradle_id, center=true);
            }}
        }}
    }}
    """
    return code

def main():
    parser = argparse.ArgumentParser(description="Generate STL files from OpenSCAD with different engravings.")
    parser.add_argument("--id_start", type=float, required=True, help="inner diameter of holder")
    parser.add_argument("--id_end", type=float, required=True, help="inner diameter of holder")
    parser.add_argument("--increment", type=float, required=True, help="inner diameter of holder")
    parser.add_argument("--nut_size", type=float, required=True, help="size of the nut")

    
    args = parser.parse_args()

    # Locate openscad executable
    openscad_path = find_openscad()
    if openscad_path is None:
        print("Could not find openscad.exe")
        return

    inner_diameter = args.id_start
    while inner_diameter < args.id_end:
        
        scad_filename = f"holder_{inner_diameter}mm.scad"
        stl_filename = f"holder_{inner_diameter}mm.stl" #for labeled
        

        with open(scad_filename, "w") as file:
            file.write(generate_openscad_code(inner_diameter, args.nut_size,))

        subprocess.run([openscad_path, "-o", stl_filename, scad_filename])
        os.remove(scad_filename)
        inner_diameter += args.increment

if __name__ == "__main__":
    main()
