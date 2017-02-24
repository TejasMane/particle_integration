import numpy as np
import h5py
import params
import arrayfire as af
import time as timer

print(af.device.device_info())

start = timer.time()

#print('Start time',start)
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
  spread              = params.spread
  ghost_cells         = params.ghost_cells
  speed_of_light      = params.speed_of_light
  charge              = params.charge
  x_zones_field       = params.x_zones_field
  y_zones_field       = params.y_zones_field
  k_fourier           = params.k_fourier
  Amplitude_perturbed = params.Amplitude_perturbed

left_boundary    = params.left_boundary
right_boundary   = params.right_boundary
length_box_x     = params.length_box_x

bottom_boundary  = params.bottom_boundary
top_boundary     = params.top_boundary
length_box_y     = params.length_box_y

back_boundary    = params.back_boundary
front_boundary   = params.front_boundary
length_box_z     = params.length_box_z

# Here we complete import of all the variable from the parameters file

# Now we shall read the data that was generated by initialize.py
# This would provide us our initial conditions(at t = 0) for the simulation

h5f           = h5py.File('data_files/initial_conditions/initial_data.h5', 'r')

x_initial     = h5f['x_coords'][:]
x_initial     = af.to_array(x_initial)

y_initial     = h5f['y_coords'][:]
y_initial     = (af.to_array(y_initial)).as_type(af.Dtype.f64)

vel_x_initial = h5f['vel_x'][:]
vel_x_initial = af.to_array(0.2*vel_x_initial)

vel_y_initial = h5f['vel_y'][:]
vel_y_initial = af.to_array(0.2*vel_y_initial)

time          = h5f['time'][:]
print('time length', time.size)
x_center      = h5f['x_center'][:]
x_center      = af.to_array(x_center)

y_center      = h5f['y_center'][:]
y_center      = af.to_array(y_center)

x_right       = h5f['x_right'][:]
x_right        = af.to_array(x_center)

y_top         = h5f['y_top'][:]
y_top         = af.to_array(y_center)

z_initial     = h5f['z_coords'][:]
z_initial     = af.to_array(z_initial)

vel_z_initial = h5f['vel_z'][:]
vel_z_initial     = af.to_array(0.2*vel_z_initial)

h5f.close()

# Considering a non-adaptive time-stepping, the time-step size for the entire simulation would be
dt = time[1] - time[0]

"""Declaring data variables which shall be used in post-processing"""

# These variables will be written to file at the end of every 100 time-steps
# This frequency of writing to the disc may be changed below

#momentum_x     = np.zeros(time.size)
#momentum_y     = np.zeros(time.size)
#momentum_z     = np.zeros(time.size)
#kinetic_energy = np.zeros(time.size)
#pressure       = np.zeros(time.size)
#heatflux_x     = np.zeros(time.size)
#heatflux_y     = np.zeros(time.size)
#heatflux_z     = np.zeros(time.size)

if(collision_operator == "potential-based"):
  potential_energy = np.zeros(time.size)

"""Choice for integrators"""

if(choice_integrator == "verlet"):
  from integrators.verlet import integrator

"""Setting the wall options"""

if(wall_condition_x == "thermal"):
  from wall_options.thermal import wall_x
elif(wall_condition_x == "hardwall"):
  from wall_options.hard_wall import wall_x
elif(wall_condition_x == "periodic"):
  from wall_options.periodic import wall_x

if(wall_condition_y == "thermal"):
  from wall_options.thermal import wall_y
elif(wall_condition_y == "hardwall"):
  from wall_options.hard_wall import wall_y
elif(wall_condition_y == "periodic"):
  from wall_options.periodic import wall_y

if(wall_condition_z == "thermal"):
  from wall_options.thermal import wall_z
elif(wall_condition_z == "hardwall"):
  from wall_options.hard_wall import wall_z
elif(wall_condition_z == "periodic"):
  from wall_options.periodic import wall_z

"""Collision Options"""

if(collision_operator == "montecarlo"):
  from collision_operators.monte_carlo import collision_operator

# We shall define a collision operator for the potential based model and collisionless models as well,
# Although integrator takes care of the scattering itself. The operator shall return the values as is
# This is to avoid condition checking inside the time-loop

if(collision_operator == "potential-based"):
  from collision_operators.potential import collision_operator

if(collision_operator == "collisionless"):
  from collision_operators.collisionless import collision_operator

if(fields_enabled == "true"):
  from fields.fdtd import fdtd
  from integrators.magnetic_verlet import integrator
  from fields.current_depositor import dcd, current_b0_depositor, charge_b0_depositor
  Ez = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  Bx = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  By = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)

  Bz = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  Ex = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  Ey = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  
  Ez_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)
  Bx_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)
  By_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)

  Bz_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)
  Ex_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)
  Ey_particle = af.data.constant(0,no_of_particles, dtype=af.Dtype.f64)

  Jx = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  Jy = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)
  Jz = af.data.constant(0,y_center.elements(),x_center.elements(), dtype=af.Dtype.f64)

  X_center_physical = af.tile(af.reorder(x_center[ghost_cells:-ghost_cells],1),y_center[ghost_cells:-ghost_cells].elements(),1)

  X_right_physical  = af.tile(af.reorder(x_right[ghost_cells:-ghost_cells],1),y_center[ghost_cells:-ghost_cells].elements(),1)

  Y_center_physical = af.tile(y_center[ghost_cells:-ghost_cells], 1, x_center[ghost_cells:-ghost_cells].elements())

  Y_top_physical    = af.tile(y_top[ghost_cells:-ghost_cells], 1, x_center[ghost_cells:-ghost_cells].elements())

  ## Initializing the fields:

  dx = length_box_x/x_zones_field
  dy = length_box_y/y_zones_field

  # Ey[ghost_cells:-ghost_cells, ghost_cells:-ghost_cells] = 0.2*af.arith.sin(2*np.pi*(-X_right_physical))
  # Bz[ghost_cells:-ghost_cells, ghost_cells:-ghost_cells] = 0.2*af.arith.sin(2*np.pi*((dx/2)-X_right_physical))
  Ex [ghost_cells:-ghost_cells, ghost_cells:-ghost_cells] = Amplitude_perturbed * no_of_particles * \
                                                            af.arith.cos(k_fourier*(-X_right_physical))

# Now we shall proceed to evolve the system with time:
from fields.interpolator import zone_finder, fraction_finder

for time_index,t0 in enumerate(time):

  loop_entering = timer.time()
  #print('Entering time index loop',loop_entering-start)
  if(time_index%100==0):
    print("Computing for Time Index = ", time_index)
  #print("Physical Time            = ", t0)
  #print() # This is to print a blank line
  
  if(time_index == time.size-1):
    break

  if(time_index!=0):
    x_initial     = old_x
    y_initial     = old_y
    z_initial     = old_z
    vel_x_initial = old_vel_x
    vel_y_initial = old_vel_y
    vel_z_initial = old_vel_z

  """ 
  We shall use the integrator that accounts only for collisions in the case of potential-based model
  and acts as a pure particle pusher for all other cases, in the absence of electric and magnetic fields
  With the presence of fields, we need to integrate over the motion of the particle known as the Boris
  Algorithm to avoid rise in the energy of the system. 
  Future revisions shall try to include these features into a single integrator option
  """

  if(fields_enabled == "false"):

    (x_coords, y_coords, z_coords, vel_x, vel_y, vel_z) = integrator(x_initial,     y_initial,     z_initial,\
                                                                     vel_x_initial, vel_y_initial, vel_z_initial, dt\
                                                                    )
  
  elif(fields_enabled == "true"):

    #print('Before Entering Current depositer Fields ',timer.time()-loop_entering)
    Jx[:, :], Jy[:, :], Jz[:, :] = 0, 0, 0
    
    if(time_index==0):
      Jx, Jy, Jz = dcd( charge, no_of_particles, x_initial-vel_x_initial*(dt/2), y_initial-vel_z_initial*(dt/2), \
                        z_initial-vel_z_initial*(dt/2), vel_x_initial, vel_y_initial, vel_z_initial, x_center, \
                        y_center, current_b0_depositor, ghost_cells,length_box_x, length_box_y, dx, dy \
                      )
    else:

      Jx, Jy, Jz = dcd( charge, no_of_particles, x_coords-vel_x*(dt/2), y_coords-vel_y*(dt/2), z_coords-vel_z*(dt/2),\
                        vel_x, vel_y, vel_z, x_center, y_center, current_b0_depositor, ghost_cells,\
                        length_box_x, length_box_y, dx, dy \
                      )

    #print('\n\n\n After Entering Current depositer Fields',timer.time()-loop_entering)

    #print('Before updating Fields',timer.time()-loop_entering)

    Ex_updated, Ey_updated, Ez_updated, Bx_updated, By_updated, Bz_updated = fdtd(Ex, Ey, Ez, Bx, By, Bz, speed_of_light, length_box_x,length_box_y, ghost_cells, Jx, Jy, Jz)

    #print('After updating Fields ',timer.time()-loop_entering)
    ## Updated fields info: Electric fields at (n+1)dt, and Magnetic fields at (n+0.5)dt from (E at ndt and B at (n-0.5)dt)

    ## E at ndt and B averaged at ndt to push v at (n-0.5)dt
    #print(' Before Zone finding ',timer.time()-loop_entering)


    if(time_index==0):
      # print('yolo',x_initial,'yyyyyyyyy', y_initial)
      fracs_Ex_x, fracs_Ex_y = fraction_finder(x_initial, y_initial, x_right, y_center)

      fracs_Ey_x, fracs_Ey_y = fraction_finder(x_initial, y_initial, x_center, y_top)

      fracs_Ez_x, fracs_Ez_y = fraction_finder(x_initial, y_initial, x_center, y_center)

      fracs_Bx_x, fracs_Bx_y = fraction_finder(x_initial, y_initial, x_center, y_top)

      fracs_By_x, fracs_By_y = fraction_finder(x_initial, y_initial, x_right, y_center)

      fracs_Bz_x, fracs_Bz_y = fraction_finder(x_initial, y_initial, x_right, y_top)

    else:
      fracs_Ex_x, fracs_Ex_y = fraction_finder(x_coords, y_coords, x_right, y_center)

      fracs_Ey_x, fracs_Ey_y = fraction_finder(x_coords, y_coords, x_center, y_top)

      fracs_Ez_x, fracs_Ez_y = fraction_finder(x_coords, y_coords, x_center, y_center)

      fracs_Bx_x, fracs_Bx_y = fraction_finder(x_coords, y_coords, x_center, y_top)

      fracs_By_x, fracs_By_y = fraction_finder(x_coords, y_coords, x_right, y_center)

      fracs_Bz_x, fracs_Bz_y = fraction_finder(x_coords, y_coords, x_right, y_top)

    #print(' After Zone finding ',timer.time()-loop_entering)

    #print(' Before Interpolation  ',timer.time()-loop_entering)


      Ex_particle = af.signal.approx2(Ex, fracs_Ex_y, fracs_Ex_x)

      Ey_particle = af.signal.approx2(Ey, fracs_Ey_y, fracs_Ey_x)

      Ez_particle = af.signal.approx2(Ez, fracs_Ez_y, fracs_Ez_x)

      Bx_particle = af.signal.approx2(Bx, fracs_Bx_y, fracs_Bx_x)

      By_particle = af.signal.approx2(By, fracs_By_y, fracs_By_x)

      Bz_particle = af.signal.approx2(Bz, fracs_Bz_y, fracs_Bz_x)


    #print(' After Interpolation  ',timer.time()-loop_entering)
    #print('Before Particle pushing',timer.time()-loop_entering)
    (x_coords, y_coords, z_coords, vel_x, vel_y, vel_z) = integrator(x_initial, y_initial, z_initial,\
                                                                     vel_x_initial, vel_y_initial, vel_z_initial, dt, \
                                                                     Ex_particle, Ey_particle, Ez_particle,\
                                                                     Bx_particle, By_particle, Bz_particle\
                                                                    )
    #print('After Particle pushing',timer.time()-loop_entering)
    Ex, Ey, Ez, Bx, By, Bz= Ex_updated, Ey_updated, Ez_updated, Bx_updated, By_updated, Bz_updated
  


  (x_coords, vel_x, vel_y, vel_z) = wall_x(x_coords, vel_x, vel_y, vel_z)
  (y_coords, vel_x, vel_y, vel_z) = wall_y(y_coords, vel_x, vel_y, vel_z)
  (z_coords, vel_x, vel_y, vel_z) = wall_z(z_coords, vel_x, vel_y, vel_z)


  # (x_coords, y_coords, z_coords, vel_x, vel_y, vel_z) = collision_operator(x_initial,     y_initial,     z_initial, \
  #                                                                          vel_x_initial, vel_y_initial, vel_z_initial, dt\
  #                                                                         )

  ## Here, we shall set assign the values to variables which shall be used as a starting point for the next time-step

  old_x = x_coords
  old_y = y_coords
  old_z = z_coords

  old_vel_x = vel_x
  old_vel_y = vel_y
  old_vel_z = vel_z
  
  #""" Assigning values for the post processing variables """

  #if(plot_spatial_temperature_profile == "true" and time_index%100 == 0):
    #particle_xzone   = (x_zones/length_box_x) * (x_coords - left_boundary)
    #particle_yzone   = (y_zones/length_box_y) * (y_coords - bottom_boundary)
    #particle_xzone   = particle_xzone.astype(int)
    #particle_yzone   = particle_yzone.astype(int)
    #particle_zone    = x_zones * particle_yzone + particle_xzone
    #zonecount        = np.bincount(particle_zone)
    
    #temperature_spatial = np.zeros(zonecount.elements())
  
    #for i in range(x_zones*y_zones):
      #indices = np.where(particle_zone == i)[0]
      #temperature_spatial[i] = 0.5*np.sum(vel_x[indices]**2 + vel_y[indices]**2)
    
    #temperature_spatial = temperature_spatial/zonecount
    #temperature_spatial = temperature_spatial.reshape(x_zones,y_zones)
  
  #"""Calculation of the functions which will be used to post-process the results of the simulation run"""

  #momentum_x[time_index]     = mass_particle * np.sum(vel_x)
  #momentum_y[time_index]     = mass_particle * np.sum(vel_y)
  #momentum_z[time_index]     = mass_particle * np.sum(vel_z)

  #kinetic_energy[time_index] = 0.5*mass_particle*np.sum(vel_x**2 + vel_y**2 + vel_z**2)
  
  #pressure[time_index]       = np.sum(vel_x**2 + vel_y**2 + vel_z**2)/no_of_particles
  
  #heatflux_x[time_index]     = np.sum(vel_x*(vel_x**2 + vel_y**2 + vel_z**2))/no_of_particles
  #heatflux_y[time_index]     = np.sum(vel_y*(vel_x**2 + vel_y**2 + vel_z**2))/no_of_particles
  #heatflux_z[time_index]     = np.sum(vel_z*(vel_x**2 + vel_y**2 + vel_z**2))/no_of_particles

  #if(collision_operator == "potential-based"):
    #from collision_operators.potential import calculate_potential_energy
    #potential_energy = calculate_potential_energy(sol)

  ## Writing the data to file every 100 time steps
  ## Make changes to this write frequency if necessary
  ## This data will then be post-processed to generate results
  
  ##if((time_index%10)==0):
    ##h5f = h5py.File('data_files/timestepped_data/solution_'+str(time_index)+'.h5', 'w')
    ##h5f.create_dataset('x_coords',   data = x_coords)
    ##h5f.create_dataset('y_coords',   data = y_coords)
    ##h5f.create_dataset('z_coords',   data = z_coords)
    ##h5f.create_dataset('vel_x',      data = vel_x)
    ##h5f.create_dataset('vel_y',      data = vel_y)
    ##h5f.create_dataset('vel_z',      data = vel_z)
    ##h5f.create_dataset('momentum_x', data = momentum_x)
    ##h5f.create_dataset('momentum_y', data = momentum_y)
    ##h5f.create_dataset('momentum_z', data = momentum_z)
    ##h5f.create_dataset('heatflux_x', data = heatflux_x)
    ##h5f.create_dataset('heatflux_y', data = heatflux_y)
    ##h5f.create_dataset('heatflux_z', data = heatflux_z)
    
    ##h5f.create_dataset('kinetic_energy', data = kinetic_energy)
    ##h5f.create_dataset('pressure',       data = pressure)
    ##h5f.create_dataset('time',           data = time)

    ##if(collision_operator == "potential-based"):
      ##h5f.create_dataset('potential_energy',    data = potential_energy)
    
    ##if(plot_spatial_temperature_profile == "true"):
      ##h5f.create_dataset('temperature_spatial', data = temperature_spatial)

    ##h5f.close()


  h5f = h5py.File('data_files/timestepped_data/solution_'+str(time_index)+'.h5', 'w')
  h5f.create_dataset('x_coords',   data = x_coords)
  h5f.close()
