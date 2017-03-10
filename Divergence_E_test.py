import numpy as np
import h5py
import params
import arrayfire as af
import time as timer
import pylab as pl

print(af.device.device_info())

pl.rcParams['figure.figsize']  = 12, 7.5
pl.rcParams['lines.linewidth'] = 1.5
pl.rcParams['font.family']     = 'serif'
pl.rcParams['font.weight']     = 'bold'
pl.rcParams['font.size']       = 20
pl.rcParams['font.sans-serif'] = 'serif'
pl.rcParams['text.usetex']     = True
pl.rcParams['axes.linewidth']  = 1.5
pl.rcParams['axes.titlesize']  = 'medium'
pl.rcParams['axes.labelsize']  = 'medium'

pl.rcParams['xtick.major.size'] = 8
pl.rcParams['xtick.minor.size'] = 4
pl.rcParams['xtick.major.pad']  = 8
pl.rcParams['xtick.minor.pad']  = 8
pl.rcParams['xtick.color']      = 'k'
pl.rcParams['xtick.labelsize']  = 'medium'
pl.rcParams['xtick.direction']  = 'in'

pl.rcParams['ytick.major.size'] = 8
pl.rcParams['ytick.minor.size'] = 4
pl.rcParams['ytick.major.pad']  = 8
pl.rcParams['ytick.minor.pad']  = 8
pl.rcParams['ytick.color']      = 'k'
pl.rcParams['ytick.labelsize']  = 'medium'
pl.rcParams['ytick.direction']  = 'in'


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
vel_x_initial = af.to_array(vel_x_initial)

vel_y_initial = h5f['vel_y'][:]
vel_y_initial = af.to_array(vel_y_initial)

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
vel_z_initial     = af.to_array(vel_z_initial)

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
  from fields.current_depositor import dcd, Umeda_2003,\
  charge_b1_depositor, current_b1_depositor,direct_charge_deposition

  Ez = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  Bx = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  By = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)

  Bz = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  Ex = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  Ey = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)

  Ez_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)
  Bx_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)
  By_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)

  Bz_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)
  Ex_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)
  Ey_particle = af.data.constant(0, no_of_particles, dtype=af.Dtype.f64)

  Jx = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  Jy = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)
  Jz = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)

  rho = af.data.constant(0, y_center.elements(), x_center.elements(), dtype=af.Dtype.f64)

  X_center_physical = af.tile(af.reorder(x_center[ghost_cells:-ghost_cells],1), y_center[ghost_cells:-ghost_cells].elements(),1)

  X_right_physical  = af.tile(af.reorder(x_right[ghost_cells:-ghost_cells],1), y_center[ghost_cells:-ghost_cells].elements(),1)

  Y_center_physical = af.tile(y_center[ghost_cells:-ghost_cells], 1, x_center[ghost_cells:-ghost_cells].elements())

  Y_top_physical    = af.tile(y_top[ghost_cells:-ghost_cells], 1, x_center[ghost_cells:-ghost_cells].elements())

  ## Initializing the fields:

  dx = length_box_x/x_zones_field
  dy = length_box_y/y_zones_field


# Now we shall proceed to evolve the system with time:
from fields.interpolator import zone_finder, fraction_finder
from fields.PoissonSolver import SOR, compute_Electric_field,\
     compute_Electric_field, compute_divergence_E_minus_rho

for time_index,t0 in enumerate(time):

  loop_entering = timer.time()
  #print('Entering time index loop',loop_entering-start)
  if(time_index%100==0):
    print("Computing for Time Index = ", time_index)
    print() # This is to print a blank line

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

    Jx[:, :], Jy[:, :], Jz[:, :] = 0, 0, 0
    # print('Before  current deposition, Jx = ', Jx)
    # print('x, y and v_x for the current deposition are ',x_initial-vel_x_initial*(dt/2), y_initial-vel_z_initial*(dt/2),vel_x_initial)

    if(time_index==0):

      Jx, Jy, Jz = dcd( charge, no_of_particles, x_initial-vel_x_initial*(dt/2), y_initial-vel_z_initial*(dt/2), \
                        z_initial-vel_z_initial*(dt/2), vel_x_initial, vel_y_initial, vel_z_initial, x_center, \
                        y_center, current_b1_depositor, ghost_cells,length_box_x, length_box_y, dx, dy \
                      )

      rho = direct_charge_deposition( charge, no_of_particles, x_initial, y_initial, \
                        z_initial, vel_x_initial, vel_y_initial, vel_z_initial, x_center, \
                        y_center, charge_b1_depositor, ghost_cells,length_box_x, length_box_y, dx, dy \
                      )

    #   print()

    #   print('rho is ', (rho))
    #   rho = rho/no_of_particles
    #   print('x_center elements ',x_center.dims())
    #   print('Rho elements ',rho.dims())
      V = SOR(rho, ghost_cells, dx, dy)
    #   input('check')
    #   print('V is ',V)
    #   input('V check')
      Ex, Ey = compute_Electric_field(V, dx, dy, ghost_cells)
    #   print('Ex is', Ex)
    #   input('Ex check')
      div_E_minus_rho = compute_divergence_E_minus_rho(Ex, Ey, (rho), dx, dy , ghost_cells)

    #   print('div_E_minus_rho is ',(div_E_minus_rho))

      pl.contourf(np.array(x_center), np.array(y_center), np.array(rho), 100)
      pl.colorbar()
      pl.title(r'$\rho$')
      pl.xlabel('$x$')
      pl.ylabel('$y$')
      pl.show()
      pl.clf()
      pl.contourf(np.array(x_center), np.array(y_center), np.array(V), 100)
      pl.colorbar()
      pl.title('V')
      pl.show()
      pl.clf()
    #   print('Ex last  point', Ex[-1, :])
    #   print('Ex 2nd last point', Ex[-2, :])
    #   print('Ex 3rd last point', Ex[-3, :])
    #   print('Ex 4th last point', Ex[-4, :])
      #
    #   pl.contourf(np.array(x_center[1:-1]), np.array(y_center[1:-1]), np.array(Ex[1:-1,1:-1]), 100)
    #   pl.colorbar()
    #   pl.title('Ex physical all')
    #   pl.xlabel('$x$')
    #   pl.ylabel('$y$')
    #   pl.show()
    #   pl.clf()
      #
    #   pl.contourf(np.array(x_center[2:-2]), np.array(y_center[2:-2]), np.array(Ex[2:-2,2:-2]), 100)
    #   pl.colorbar()
    #   pl.title('Ex')
    #   pl.xlabel('$x$')
    #   pl.ylabel('$y$')
    #   pl.show()
    #   pl.clf()

      pl.contourf(np.array(x_center), np.array(y_center), np.array(Ex), 100)
      pl.colorbar()
      pl.title('Ex')
      pl.xlabel('$x$')
      pl.ylabel('$y$')
      pl.show()
      pl.clf()

      pl.contourf(np.array(x_center), np.array(y_center), np.array(Ey), 100)
      pl.colorbar()
      pl.title('Ey')
      pl.xlabel('$x$')
      pl.ylabel('$y$')
      pl.show()
      pl.clf()
    #   print(div_E_minus_rho.dims())
      pl.contourf(np.array(x_center[1:-1]), np.array(y_center[1:-1]), np.array(div_E_minus_rho[1:-1, 1:-1]), 100)
      pl.colorbar()
      pl.xlabel('$x$')
      pl.ylabel('$y$')
      pl.title(r'$\nabla \cdot \textbf{E} - \rho$')
      pl.show()
      pl.clf()

      input('check')

    else:

      Jx, Jy, Jz = dcd( charge, no_of_particles, x_coords-vel_x*(dt/2), y_coords-vel_y*(dt/2), z_coords-vel_z*(dt/2),\
                        vel_x, vel_y, vel_z, x_center, y_center, current_b0_depositor, ghost_cells,\
                        length_box_x, length_box_y, dx, dy \
                      )


    Ex_updated, Ey_updated, Ez_updated, Bx_updated, By_updated, Bz_updated = fdtd( Ex, Ey, Ez, Bx, By, Bz, \
                                                                                   speed_of_light, length_box_x,\
                                                                                   length_box_y, ghost_cells, Jx, Jy,\
                                                                                   Jz, dt, no_of_particles\
                                                                                 )

    ## Updated fields info: Electric fields at (n+1)dt, and Magnetic fields at (n+0.5)dt from (E at ndt and B at (n-0.5)dt)

    ## E at ndt and B averaged at ndt to push v at (n-0.5)dt


    if(time_index==0):

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



    Ex_particle = af.signal.approx2(Ex, fracs_Ex_y, fracs_Ex_x)

    Ey_particle = af.signal.approx2(Ey, fracs_Ey_y, fracs_Ey_x)

    Ez_particle = af.signal.approx2(Ez, fracs_Ez_y, fracs_Ez_x)

    Bx_particle = af.signal.approx2(Bx, fracs_Bx_y, fracs_Bx_x)

    By_particle = af.signal.approx2(By, fracs_By_y, fracs_By_x)

    Bz_particle = af.signal.approx2(Bz, fracs_Bz_y, fracs_Bz_x)





    # UPDATING THE PARTICLE COORDINATES USING BORIS ALGORITHM

    (x_coords, y_coords, z_coords, vel_x, vel_y, vel_z) = integrator(mass_particle, charge, x_initial, y_initial, z_initial,\
                                                                     vel_x_initial, vel_y_initial, vel_z_initial, dt, \
                                                                     Ex_particle, Ey_particle, Ez_particle,\
                                                                     Bx_particle, By_particle, Bz_particle\
                                                                    )

    # SAVING THE FIELDS FOR NEXT TIME STEP

    Ex, Ey, Ez, Bx, By, Bz= Ex_updated.copy(), Ey_updated.copy(), Ez_updated.copy(), Bx_updated.copy(), By_updated.copy(), Bz_updated.copy()


    #
    # if(time_index == 10):
    #     diff_Ex =

  (x_coords, vel_x, vel_y, vel_z) = wall_x(x_coords, vel_x, vel_y, vel_z)
  (y_coords, vel_x, vel_y, vel_z) = wall_y(y_coords, vel_x, vel_y, vel_z)
  (z_coords, vel_x, vel_y, vel_z) = wall_z(z_coords, vel_x, vel_y, vel_z)

  ## Here, we shall set assign the values to variables which shall be used as a starting point for the next time-step

  old_x = x_coords
  old_y = y_coords
  old_z = z_coords

  old_vel_x = vel_x
  old_vel_y = vel_y
  old_vel_z = vel_z



  if(time_index%100==0):
    h5f = h5py.File('data_files/timestepped_data/solution_'+str(time_index)+'.h5', 'w')
    h5f.create_dataset('x_coords',   data = x_coords)
    h5f.create_dataset('Ex',   data = (Ex))
    h5f.close()
