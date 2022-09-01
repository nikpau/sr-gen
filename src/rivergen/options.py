# Breadth and spacing of segments
GP = 76 #  No. of grid points per segment width
BPD = 20 # distance between gridpoints [m]
BREADTH = ((GP-1)*BPD) # [m]

# Print information about the generation 
# process to stdout
VERBOSE: bool = True