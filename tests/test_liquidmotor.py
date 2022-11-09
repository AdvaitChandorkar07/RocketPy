from rocketpy import Fluid
from rocketpy.motors.LiquidMotor import Tank, LiquidMotor, MassBasedTank, UllageBasedTank, MassFlowRateBasedTank
from rocketpy.motors.Fluid import Fluid
from rocketpy.Function import Function
from math import isclose
from scipy.optimize import fmin
import numpy as np
import pandas as pd
import os


# @PBales1
def test_mass_based_motor():
    lox = Fluid(name = "LOx", density = 1141.7, quality = 1.0) #Placeholder quality value
    propane = Fluid(name = "Propane", density = 493, quality = 1.0) #Placeholder quality value
    n2 = Fluid(name = "Nitrogen Gas", density = 51.75, quality = 1.0) #Placeholder quality value; density value may be estimate
    
    example_motor = MassBasedTank("Example Tank", 0.1540, 0.66, 0.7, "Placeholder", "Placeholder", lox, n2) 


# @curtisjhu
def test_ullage_based_motor():

    lox = Fluid(name = "LOx", density=2, quality = 1.0)
    n2 = Fluid(name = "Nitrogen Gas", density=1, quality = 1.0)

    test_dir = '../data/e1-hotfires/test136/'

    top_endcap = lambda y: np.sqrt(0.0775 ** 2 - (y - 0.692300000000001) ** 2)
    bottom_endcap = lambda y: np.sqrt(0.0775 ** 2 - (0.0775 - y) ** 2)
    tank_geometry = {(0, 0.0559): bottom_endcap, (.0559, 0.7139): lambda y: 0.0744, (0.7139, 0.7698): top_endcap}

    ullage_data = pd.read_csv(os.path.abspath(test_dir+'loxUllage.csv')).to_numpy()
    ullageTank = UllageBasedTank("Ullage Tank", tank_geometry,
                                 gas=n2, liquid=lox, ullage=ullage_data)

    mass_data = pd.read_csv(test_dir+'loxMass.csv').to_numpy()
    mass_flow_rate_data = pd.read_csv(test_dir+'loxMFR.csv').to_numpy()

    def align_time_series(small_source, large_source):
        assert isinstance(small_source, np.ndarray) and isinstance(large_source, np.ndarray), "Must be np.ndarrays"
        if small_source.shape[0] > large_source.shape[0]:
            small_source, large_source = large_source, small_source

        result_larger_source = np.ndarray(small_source.shape)
        result_smaller_source = np.ndarray(small_source.shape)
        tolerance = .1
        for smallIndex, val in enumerate(small_source):
            time = val[0]
            delta_time_vector = abs(time-large_source[:, 0])
            largeIndex = np.argmin(delta_time_vector)
            delta_time = abs(time - large_source[largeIndex][0])

            if delta_time < tolerance:
                result_larger_source[smallIndex] = large_source[largeIndex]
                result_smaller_source[smallIndex] = val
        return result_larger_source, result_smaller_source

    assert np.allclose(ullageTank.liquidHeight().getSource(), ullage_data)
    ullage_tank_mass_data, mass_data = align_time_series(ullageTank.liquidMass().getSource(), mass_data)
    Function(ullage_tank_mass_data).plot1D()
    # assert np.allclose(ullage_tank_mass, mass_data, rtol=3)
    # assert np.allclose(ullageTank.netMassFlowRate().getSource(), mass_flow_rate_data)

# @gautamsaiy
def test_mfr_tank_basic1():
    def test(t, a):
        for i in np.arange(0, 10, .2):
            assert isclose(t.getValue(i), a(i), abs_tol=1e-5)
            # print(t.getValue(i), a(i))
            # print(t(i))

    def test_nmfr():
        nmfr = lambda x: liquid_mass_flow_rate_in + gas_mass_flow_rate_in - liquid_mass_flow_rate_out - gas_mass_flow_rate_out
        test(t.netMassFlowRate(), nmfr)

    def test_mass():
        m = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x) + \
            (initial_gas_mass + (gas_mass_flow_rate_in - gas_mass_flow_rate_out) * x)
        lm = t.mass()
        test(lm, m)

    def test_liquid_height():
        alv = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x) / lox.density
        alh = lambda x: alv(x) / (np.pi)
        tlh = t.liquidHeight()
        test(tlh, alh)

    def test_com():
        alv = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x) / lox.density
        alh = lambda x: alv(x) / (np.pi)
        alm = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x)
        agm = lambda x: (initial_gas_mass + (gas_mass_flow_rate_in - gas_mass_flow_rate_out) * x)

        alcom = lambda x: alh(x) / 2
        agcom = lambda x: (5 - alh(x)) / 2 + alh(x)
        acom = lambda x: (alm(x) * alcom(x) + agm(x) * agcom(x)) / (alm(x) + agm(x))

        tcom = t.centerOfMass
        test(tcom, acom)

    # def test_inertia():
    #     alv = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x) / lox.density
    #     alh = lambda x: alv(x) / (np.pi)
    #     m = lambda x: (initial_liquid_mass + (liquid_mass_flow_rate_in - liquid_mass_flow_rate_out) * x) + \
    #         (initial_gas_mass + (gas_mass_flow_rate_in - gas_mass_flow_rate_out) * x)
    #     r = 1
    #     iz = lambda x: (m(x) * r**2)/2
    #     ix = lambda x: (1/12)*m(x)*(3*r**2 + alh(x) **2)
    #     iy = lambda x: (1/12)*m(x)*(3*r**2 + alh(x) **2)
    #     test(i, 0)
    #


    tank_radius_function = {(0, 5): 1}
    lox = Fluid(name = "LOx", density = 1141, quality = 1.0) #Placeholder quality value
    n2 = Fluid(name = "Nitrogen Gas", density = 51.75, quality = 1.0) #Placeholder quality value; density value may be estimate
    initial_liquid_mass = 5
    initial_gas_mass = .1
    liquid_mass_flow_rate_in = .1
    gas_mass_flow_rate_in = .01
    liquid_mass_flow_rate_out = .2
    gas_mass_flow_rate_out = .02

    t = MassFlowRateBasedTank("Test Tank", tank_radius_function,
            initial_liquid_mass, initial_gas_mass, liquid_mass_flow_rate_in,
            gas_mass_flow_rate_in, liquid_mass_flow_rate_out, 
            gas_mass_flow_rate_out, lox, n2)

    test_nmfr()
    test_mass()
    test_liquid_height()
    test_com()
    # test_inertia()
