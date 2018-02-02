import math
import numpy as np


class ISALayer:
    ''' in a layer, temperature changes linearly with temperature
    '''
    
    grav_const = 9.8066
    
    def __init__(self, height, lapse_rate, base_temp, base_press, gas_const=0.28704):
        self.height = height
        self.tbot = base_temp
        self.base_press = base_press
        self.gas_const = gas_const
        self.ttop = base_temp + lapse_rate * height

    def get_temperature_by_altitude(self, altitude):
        # allow some slack due to numerical errors when computing alt. from pressure
        slack = 1e-10
        assert -slack <= altitude <= self.height + slack, (altitude, self.height)
        return self.tbot + (self.ttop - self.tbot) * (altitude / self.height)

    def get_pressure_by_altitude(self, altitude):
        exp = -self.grav_const  * self.tbot * self.height / (self.gas_const * self.ttop)
        frac = 1 + altitude * self.ttop / (self.tbot**2 * self.height)
        return self.base_press * math.pow(frac, exp)

    def get_altitude_by_pressure(self, pressure):
        co = self.tbot**2 * self.height / self.ttop
        exp = self.gas_const * self.ttop / (self.grav_const * self.tbot * self.height)
        return co * (math.pow(self.base_press / pressure, exp) - 1)
    
    def get_temperature_by_pressure(self, pressure):
        altitude = self.get_altitude_by_pressure(pressure)
        return self.get_temperature_by_altitude(altitude)

class ISAModel:
    ''' atmospheric models made by a sequence of layers
        in which temperature changes linearly
         
        ttps://en.wikipedia.org/wiki/International_Standard_Atmosphere
    '''
    def __init__(self, layers=None):
        self.layers = layers or []

    @staticmethod
    def standard_config():
        atm = ISAModel()
        atm.add_layer(11.019, -6.5, 273.15 + 19.0, 101325)  # troposphere
        atm.add_layer(20.063 - 11.019, 0.0)                 # tropopause
        atm.add_layer(32.162 - 20.063, 1.0)                 # stratosphere
        atm.add_layer(47.350 - 32.162, 2.8)                 # stratosphere
        atm.add_layer(51.413 - 47.350, 0.0)                 # stratopause
        atm.add_layer(71.802 - 51.413, -2.8)                # mesosphere
        atm.add_layer(84.852 - 71.802, -2.0)                # mesosphere
        return atm

    @property
    def height(self):
        return sum(l.height for l in self.layers)

    def add_layer(self, height, lapse_rate, base_temp=None, base_press=None):
        base_temp = base_temp or self.layers[-1].get_temperature_by_altitude(self.layers[-1].height)
        base_press = base_press or self.layers[-1].get_pressure_by_altitude(self.layers[-1].height)
        
        self.layers.append(ISALayer(height, lapse_rate, base_temp, base_press))

    def _get_layer_by_altitude(self, altitude):
        alt = 0.0
        for layer in self.layers:
            alt += layer.height
            if altitude <= alt:
                return layer, altitude - alt + layer.height
        else:
            raise ValueError('%f is outside of the atmosphere, limit is %f' % (
                    altitude, alt))

    def _get_layer_by_pressure(self, pressure):
        for layer in self.layers:
            if pressure >= layer.get_pressure_by_altitude(layer.height):
                return layer
        else:
            raise ValueError('pressure outside of atmosphere: %f' % pressure)

    def get_temperature_by_altitude(self, altitude):
        layer, alt_within_layer = self._get_layer_by_altitude(altitude)
        return layer.get_temperature_by_altitude(alt_within_layer)

    def get_temperature_by_pressure(self, pressure):
        layer = self._get_layer_by_pressure(pressure)
        return layer.get_temperature_by_pressure(pressure)

    def get_pressure_by_altitude(self, altitude):
        layer, alt_within_layer = self._get_layer_by_altitude(altitude)
        return layer.get_pressure_by_altitude(alt_within_layer)
    
    def get_altitude_by_pressure(self, pressure):
        layer = self._get_layer_by_pressure(pressure)
        alt = layer.get_altitude_by_pressure(pressure)
        for l in self.layers:
            if l != layer:
                alt += l.height
            else:
                break
        return alt


if __name__ == '__main__':
    atm = ISAModel()
    atm.add_layer(12, -6.5, 273.15 + 19.0, 101325)
    atm.add_layer(2, 0.0)
    atm.add_layer(25, 2.5)
    atm.add_layer(9, -6.0)
    
    atm = ISAModel.standard_config()
    
    alts = np.arange(0, atm.height, 1)
    temps = [atm.get_temperature_by_altitude(a) for a in alts]
    press = [atm.get_pressure_by_altitude(a) / 100 for a in alts]
    
    min_ps = atm.get_pressure_by_altitude(atm.height)
    pss = np.arange(min_ps / 100, 1013.25, 0.1)
    tss = [atm.get_temperature_by_pressure(p * 100) for p in pss]
    
    import matplotlib.pyplot as plt
    plt.title('altitude by pressure'); plt.plot(press, alts); plt.show()
    plt.title('altitude by temperature'); plt.plot(temps, alts); plt.show()
    plt.title('pressure by temperature'); plt.plot(tss, pss); plt.gca().invert_yaxis(); plt.show()