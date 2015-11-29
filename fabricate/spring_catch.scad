include <springs.scad>
inch = 25.4;
$fn=25;

module nix(){
  translate([0, 0, -3])
  rotate(a=-45, v=[0, 0, 1])
    intersection(){
    //cylinder(r=5, h=62 + 3 - l);
    //cube([50, 50, 100]);
  }
}

nix();
intersection(){
  difference(){
    translate([0, -4, -6.])cube([15, 8, 10.]);
    translate([0, -4-1, -2.])cube([12.85, 10, 2]);
    translate([0, 0, -1])cylinder(r=17/2, h=20);
    translate([-5, -5, -10])cube([10,10, 10]);
  }
}

translate([15, 0, -6])
difference(){
  cylinder(r=4, h=10); 
  translate([-8, -4, -.1])cube([8, 8, 11]);
}

translate([0, 0, -3.8])rotate(a=90, v=[0, 1, 0])cylinder(r1=4/2, r2=3.5/2, h=10);
translate([3./2, 0, -6])cylinder(r1=3.5/2, r2=3.5/2, h=67.15);
difference(){
  translate([3./2, 0, -1])cylinder(r1=4.5/2, r2=3.5/2, h=4);
  translate([3./2, 0, -4.5])comp_spring([ 4.83,    .5, 38, 22]);
}
