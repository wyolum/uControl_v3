inch = 25.4;

module nix(){
  translate([0, 0, -3])
  rotate(a=-45, v=[0, 0, 1])
    intersection(){
    cylinder(r=5, h=62 + 3 - l);
    cube([50, 50, 100]);
  }
}

nix();
intersection(){
  difference(){
    translate([0, -4, -6.])cube([15, 8, 10.]);
    translate([0, -4-1, -2.])cube([12.85, 10, 2]);
    translate([0, 0, -1])cylinder(r=17/2, h=20);
  }
  translate([0, 0, -20])
  rotate(a=-45, v=[0, 0, 1])
    intersection(){
    cylinder(r=50, h=62);
    cube([50, 50, 100]);
  }
  
}

d = 3.81;
D = 6;
l = 15;

translate([d/2, 0, 62 - 2 * l])
union(){
  translate([0, 0, l])cylinder(r=d/2, h=l);
  translate([0, 0, 0])cylinder(r=D/2, h=l);
}
