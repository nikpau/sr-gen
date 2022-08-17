# River/Road Segment Generator

This simple segment generator uses a combination of straight and curved segments to generate an arbirarily looking road or river. 

Currently the package is specialized for rivers, and will by default generate a river like segment with depths and currents flowing in it. 

In order to change the bulding behavior please check the main `build()` function under `src/rivergen/main.py`. In order to adapt for roads just leave out the calls to `depht.depth_map()` and `currents.current_map()`. 