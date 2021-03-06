import numpy as np
from scipy.special import erfinv
import h5py
import params

"""Here we shall re-assign values as set in params"""

no_of_particles      = params.no_of_particles
choice_integrator    = params.choice_integrator
collision_operator   = params.collision_operator

plot_spatial_temperature_profile = params.plot_spatial_temperature_profile

if(plot_spatial_temperature_profile == "true"):
  x_zones_temperature = params.x_zones_temperature
  y_zones_temperature = params.y_zones_temperature

elif(collision_operator == "potential-based"):
  potential_steepness     = params.potential_steepness
  potential_amplitude     = params.potential_amplitude
  order_finite_difference = params.order_finite_difference

elif(collision_operator == "montecarlo"):
  x_zones_montecarlo = params.x_zones_montecarlo
  y_zones_montecarlo = params.y_zones_montecarlo
  
mass_particle      = params.mass_particle
boltzmann_constant = params.boltzmann_constant
T_initial          = params.T_initial
wall_condition_x   = params.wall_condition_x
wall_condition_y   = params.wall_condition_y
wall_condition_z   = params.wall_condition_z

if(wall_condition_x == "thermal"):
  T_left_wall  = params.T_left_wall
  T_right_wall = params.T_right_wall

if(wall_condition_y == "thermal"):
  T_top_wall = params.T_top_wall
  T_bot_wall = params.T_bot_wall

if(wall_condition_z == "thermal"):
  T_front_wall = params.T_front_wall
  T_back_wall  = params.T_back_wall

fields_enabled   = params.fields_enabled

if(fields_enabled == "true"):
  spread            = params.spread
  ghost_cells       = params.ghost_cells
  speed_of_light    = params.speed_of_light
  charge            = params.charge
  x_zones_field     = params.x_zones_field
  y_zones_field     = params.y_zones_field

left_boundary    = params.left_boundary
right_boundary   = params.right_boundary
length_box_x     = params.length_box_x

bottom_boundary  = params.bottom_boundary
top_boundary     = params.top_boundary
length_box_y     = params.length_box_y

back_boundary    = params.back_boundary
front_boundary   = params.front_boundary
length_box_z     = params.length_box_z

""" 
This file is used in providing the initial velocities and positions to the particles.
The distribution of your choice may be obtained by modifying the options that have been 
provided below. Although the choice of function must be changed from this file, the parameter 
change must be made at params.py so that the same values are reflected across all the modules
"""

""" Initializing the positions for the particles """

initial_position_x = left_boundary   + length_box_x * np.random.rand(no_of_particles)
initial_position_y = bottom_boundary + length_box_y * np.random.rand(no_of_particles)
initial_position_z = back_boundary   + length_box_z * np.random.rand(no_of_particles)

""" Initializing velocities to the particles """

# Declaring the random variable which shall be used to sample velocities:
R1 = np.random.rand(no_of_particles)
R2 = np.random.rand(no_of_particles)
R3 = np.random.rand(no_of_particles)

# Sampling velocities corresponding to Maxwell-Boltzmann distribution at T_initial
initial_vel_x = np.sqrt(2*boltzmann_constant*T_initial/mass_particle)*erfinv(2*R1-1)
initial_vel_y = np.sqrt(2*boltzmann_constant*T_initial/mass_particle)*erfinv(2*R2-1)
initial_vel_z = np.sqrt(2*boltzmann_constant*T_initial/mass_particle)*erfinv(2*R3-1)

""" Time parameters for the simulation """

# Any time parameter changes that need to be made for the simulation should be edited here:
box_crossing_time_scale = (length_box_x/np.max(initial_vel_x))
final_time              = 20 * box_crossing_time_scale
dt                      = 0.001 * box_crossing_time_scale
time                    = np.arange(0, final_time, dt)

""" Parameters for fields """

# The following lines define the staggered set of points which shall be used in solving of electric and magnetic fields

if(fields_enabled == "true"):
  dx       = length_box_x/x_zones_field
  dy       = length_box_y/y_zones_field

  x_center = np.linspace(-ghost_cells*dx, length_box_x + ghost_cells*dx, x_zones_field + 1 + 2*ghost_cells)
  y_center = np.linspace(-ghost_cells*dy, length_box_y + ghost_cells*dy, y_zones_field + 1 + 2*ghost_cells)

  """ Setting the offset spatial grids """

  x_right = np.linspace(-ghost_cells*(dx/2), length_box_x + (2*ghost_cells + 1)*(dx/2), x_zones_field + 1 + 2*ghost_cells)
  y_top   = np.linspace(-ghost_cells*(dy/2), length_box_y + (2*ghost_cells + 1)*(dy/2), y_zones_field + 1 + 2*ghost_cells)

  final_time = 2
  dt         = np.float(dx / (2 * speed_of_light))
  time       = np.arange(0, final_time, dt)

""" Writing the data to a file which can be accessed by a solver"""

h5f = h5py.File('data_files/initial_conditions/initial_data.h5', 'w')
h5f.create_dataset('time',          data = time)
h5f.create_dataset('x_coords', data = initial_position_x)
h5f.create_dataset('y_coords', data = initial_position_y)
h5f.create_dataset('z_coords', data = initial_position_z)
h5f.create_dataset('vel_x',    data = initial_vel_x)
h5f.create_dataset('vel_y',    data = initial_vel_y)
h5f.create_dataset('vel_z',    data = initial_vel_z)

if(fields_enabled == "true"):
  h5f.create_dataset('x_center',      data = x_center)
  h5f.create_dataset('y_center',      data = y_center)
  h5f.create_dataset('x_right',       data = x_right)
  h5f.create_dataset('y_top',         data = y_top)

h5f.close()
