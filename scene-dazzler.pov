#include "colors.inc"
#include "metals.inc"
#default{finish{ambient 0.01}}
#global_settings{assumed_gamma 1.0 max_trace_level 5}

sky_sphere {
  pigment { color MidnightBlue }
}

union {
  union {
    #include "dazzler.sub.pov"
    texture {
      pigment { color rgbf<0.0, 0.0, 0.0, 1.0> }
      finish {
        reflection { 0.10 }
        specular 0.5
        roughness .006
      }
      normal { bumps 0.005 }
    }
  }

  union {
    #include "dazzler.gtl.pov"
    rotate <90, 0, 0>
    translate <0 1.030 0>
    texture {
     pigment {P_Copper2}
     finish {F_MetalA }
    }
  }

  union {
    #include "dazzler.gto.pov"
    rotate <90, 0, 0>
    translate <0 1.031 0>
    texture {
     pigment {White}
    }
  }
  translate <-25, 0, -20>
  rotate <0, clock*30, 0>
  translate <25, 0, 20>
}

light_source{<80, 180, 200> color rgb<.3 .3 .4>}
light_source{<25, 80, 80> color rgb<1.0 0.8 .4>}
