use <fillets3d.scad>;
use <knurledFinishLib.scad>;



cradle_y=15.875;
cradle_wall_thickness=2;
cradle_id=11;
bottom_height = cradle_id/2 + 3; //to bottom of cylinder
cradle_x=cradle_id + cradle_wall_thickness;
cradle_height = bottom_height+(cradle_id/2);




translate([0,0,-0]){
    rotate([0,270,90])
    import("E:/1_2_socket_holder/v2 profile/holders/1-2 inch holder base.STL");
};

topFillet(b=-1, t = cradle_height, r = 2, s = 15){
    difference(){
        translate([0,0,cradle_height/2]){
        cube([cradle_x,cradle_y,cradle_height], center = true);
        };
        translate([0,0,cradle_height- cradle_id/3]){
        rotate([90,90,0])
        cylinder(h=cradle_y,d = cradle_id, center=true);
        }
    }
    
}



