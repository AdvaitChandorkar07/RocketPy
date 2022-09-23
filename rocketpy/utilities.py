# -*- coding: utf-8 -*-
__author__ = "Franz Masatoshi Yuri, Lucas Kierulff Balabram, Guilherme Fernandes Alves"
__copyright__ = "Copyright 20XX, RocketPy Team"
__license__ = "MIT"

import numpy as np
from scipy.integrate import solve_ivp

from .Environment import Environment
from .Function import Function


# TODO: Needs tests
def compute_CdS_from_drop_test(
    terminal_velocity, rocket_mass, air_density=1.225, g=9.80665
):
    """Returns the parachute's CdS calculated through its final speed, air
    density in the landing point, the rocket's mass and the force of gravity
    in the landing point.

    Parameters
    ----------
    terminal_velocity : float
        Rocket's speed in m/s when landing.
    rocket_mass : float
        Rocket's dry mass in kg.
    air_density : float, optional
        Air density, in kg/m^3, right before the rocket lands. Default value is 1.225.
    g : float, optional
        Gravitational acceleration experienced by the rocket and parachute during
        descent in m/s^2. Default value is the standard gravity, 9.80665.

    Returns
    -------
    CdS : float
        Number equal to drag coefficient times reference area for parachute.

    """

    return 2 * rocket_mass * g / ((terminal_velocity**2) * air_density)


# TODO: Needs tests


def calculateEquilibriumAltitude(
    rocket_mass,
    CdS,
    z0,
    v0=0,
    env=None,
    eps=1e-3,
    max_step=0.1,
    seeGraphs=True,
    g=9.80665,
    estimated_final_time=10,
):
    """Returns a dictionary containing the time, altitude and velocity of the
    system rocket-parachute in which the terminal velocity is reached.


    Parameters
    ----------
    rocket_mass : float
        Rocket's mass in kg.
    CdS : float
        Number equal to drag coefficient times reference area for parachute.
    z0 : float
        Initial altitude of the rocket in meters.
    v0 : float, optional
        Rocket's initial speed in m/s. Must be negative
    env : Environment, optional
        Environmental conditions at the time of the launch.
    eps : float, optional
        acceptable error in meters.
    max_step: float, optional
        maximum allowed time step size to solve the integration
    seeGraphs : boolean, optional
        True if you want to see time vs altitude and time vs speed graphs,
        False otherwise.
    g : float, optional
        Gravitational acceleration experienced by the rocket and parachute during
        descent in m/s^2. Default value is the standard gravity, 9.80665.
    estimated_final_time: float, optional
        Estimative of how much time (in seconds) will spend until vertical terminal
        velocity is reached. Must be positive. Default is 10. It can affect the final
        result if the value is not high enough. Increase the estimative in case the
        final solution is not founded.


    Returns
    -------
    altitudeFunction: Function
        Altitude as a function of time. Always a Function object.
    velocityFunction:
        Vertical velocity as a function of time. Always a Function object.
    final_sol : dictionary
        Dictionary containing the values for time, altitude and speed of
        the rocket when it reaches terminal velocity.
    """
    final_sol = {}

    if not v0 < 0:
        print("Please set a valid negative value for v0")
        return None

    # TODO: Improve docs
    def check_constant(f, eps):
        """_summary_

        Parameters
        ----------
        f : array, list
            _description_
        eps : float
            _description_

        Returns
        -------
        int, None
            _description_
        """
        for i in range(len(f) - 2):
            if abs(f[i + 2] - f[i + 1]) < eps and abs(f[i + 1] - f[i]) < eps:
                return i
        return None

    if env == None:
        environment = Environment(
            railLength=5.0,
            latitude=0,
            longitude=0,
            elevation=1000,
            date=(2020, 3, 4, 12),
        )
    else:
        environment = env

    # TODO: Improve docs
    def du(z, u):
        """_summary_

        Parameters
        ----------
        z : float
            _description_
        u : float
            velocity, in m/s, at a given z altitude

        Returns
        -------
        float
            _description_
        """
        return (
            u[1],
            -g + environment.density(z) * ((u[1]) ** 2) * CdS / (2 * rocket_mass),
        )

    u0 = [z0, v0]

    us = solve_ivp(
        fun=du,
        t_span=(0, estimated_final_time),
        y0=u0,
        vectorized=True,
        method="LSODA",
        max_step=max_step,
    )

    constant_index = check_constant(us.y[1], eps)

    # TODO: Improve docs by explaining what is happening below with constant_index
    if constant_index is not None:
        final_sol = {
            "time": us.t[constant_index],
            "altitude": us.y[0][constant_index],
            "velocity": us.y[1][constant_index],
        }

    altitudeFunction = Function(
        source=np.array(list(zip(us.t, us.y[0])), dtype=np.float64),
        inputs="Time (s)",
        outputs="Altitude (m)",
        interpolation="linear",
    )

    velocityFunction = Function(
        source=np.array(list(zip(us.t, us.y[1])), dtype=np.float64),
        inputs="Time (s)",
        outputs="Vertical Velocity (m/s)",
        interpolation="linear",
    )

    if seeGraphs:
        altitudeFunction()
        velocityFunction()

    return altitudeFunction, velocityFunction, final_sol


def create_dispersion_dictionary(dic):
    """creates a dictinary with the rocket data in a excel .csv file.

    Parameters
    ----------
    dic : string
        String with the path to the .csv file.

    Returns
    -------
    dictionary
        Dictionary with all rocket data used in dispersion analysis.
    """
<<<<<<< HEAD
    try:
        file = np.genfromtxt(dic, usecols=(1, 2, 3), delimiter=",", dtype=str)
    except:
        file = np.genfromtxt(dic, usecols=(1, 2, 3), delimiter=";", dtype=str)
    analysis_parameters = dict()
    for list in file:
        if list[0] != "":
            if list[2] == "":
                analysis_parameters[list[0]] = float(list[1])
            else:
                analysis_parameters[list[0]] = (float(list[1]), float(list[2]))
    return analysis_parameters
=======
    dataframe = pd.read_csv(dic, skiprows=[0, 1], header=None)

    rocketKeys = list(dataframe[1].dropna())
    rocketValues = list(dataframe[2].dropna())
    rocketSD = list(dataframe[3])

    motorKeys = list(dataframe[7].dropna())
    motorValues = list(dataframe[8].dropna())
    motorSD = list(dataframe[9])

    launchKeys = list(dataframe[13].dropna())
    launchValues = list(dataframe[14].dropna())
    launchSD = list(dataframe[15])

    parachuteKeys = list(dataframe[19].dropna())
    parachuteValues = list(dataframe[20].dropna())
    parachuteSD = list(dataframe[21])

    allValues = []
    # crating the dictionary

    for i in range(0, len(rocketKeys)):

        if pd.isnull(rocketSD[i]):
            allValues.append(rocketValues[i])
        else:
            allValues.append(((rocketValues[i]), (rocketSD[i])))

    for j in range(0, len(motorKeys)):

        if pd.isnull(motorSD[j]):
            allValues.append(motorValues[j])
        else:
            allValues.append(((motorValues[j]), (motorSD[j])))

    for k in range(0, len(parachuteKeys)):

        if pd.isnull(parachuteSD[k]):
            allValues.append(parachuteValues[k])
        else:
            allValues.append(((parachuteValues[k]), (parachuteSD[k])))

    for l in range(0, len(launchKeys)):

        if pd.isnull(launchSD[l]):
            allValues.append(launchValues[l])
        else:
            allValues.append(((launchValues[l]), (launchSD[l])))

    allKeys = rocketKeys + motorKeys + parachuteKeys + launchKeys

    analysis_parameters = dict(zip(allKeys, allValues))
    return analysis_parameters
>>>>>>> 05ff0662ddda29e74b6019797ab710725d91831b
