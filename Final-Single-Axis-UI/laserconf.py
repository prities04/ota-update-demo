import decimal
from decimal import Decimal


laser_type_1w = { 0.600 : 0.003,
                  0.700 : 0.093,
                  0.800 : 0.200,
                  0.900 : 0.304,
                  1.000 : 0.408,
                  1.100 : 0.510,
                  1.200 : 0.607,
                  1.300 : 0.703,
                  1.400 : 0.795,
                  1.500 : 0.883,
                  1.600 : 0.968,
                  1.700 : 1.050,
                  1.800 : 1.128,
                  1.892 : 1.194 }


laser_type_2w = { 0.200 : 0.00,
                  0.400 : 0.046,
                  0.600 : 0.262,
                  0.800 : 0.473,
                  1.000 : 0.696,
                  1.200 : 0.915,
                  1.400 : 1.128,
                  1.600 : 1.339,
                  1.800 : 1.545,
                  2.000 : 1.754,
                  2.200 : 1.961,
                  2.400 : 2.160,
                  2.500 : 2.255 }

laser_type_8w = { 2.0 : 0.16,
                  2.2 : 0.47,
                  2.4 : 0.89,
                  2.6 : 1.31,
                  2.8 : 1.72,
                  3.0 : 2.18,
                  3.2 : 2.58,
                  3.4 : 2.96,
                  3.6 : 3.40,
                  3.8 : 3.81,
                  4.0 : 4.20,
                  4.2 : 4.64,
                  4.4 : 5.02,
                  4.6 : 5.47,
                  4.8 : 5.85,
                  5.0 : 6.25,
                  5.2 : 6.67,
                  5.4 : 7.07,
                  5.6 : 7.43,
                  5.8 : 7.86,
                  6.0 : 8.27,
                  6.1 : 8.42 }

class Laser():
    def __init__(self, laser_option):
        self.type = ""
        self.type_1w = str(laser_option[0])
        self.type_2w = str(laser_option[1])
        self.type_8w = str(laser_option[2])
        self.slope_intercept_list_1w = self.getSlopeIntercept(self.type_1w)
        self.slope_intercept_list_2w = self.getSlopeIntercept(self.type_2w)
        self.slope_intercept_list_8w = self.getSlopeIntercept(self.type_8w)

    def getLaserDict(self, type):

        laser_dict_map = {
            self.type_1w : laser_type_1w,
            self.type_2w : laser_type_2w,
            self.type_8w : laser_type_8w
        }

        return laser_dict_map.get(type, laser_type_1w)
    
    def mapSlopeIntercept(self, type):

        slope_intercept_map = {
            self.type_1w : self.slope_intercept_list_1w,
            self.type_2w : self.slope_intercept_list_2w,
            self.type_8w : self.slope_intercept_list_8w
        }

        return slope_intercept_map.get(type, laser_type_1w)
    
    def convertDictToList(self, arg_dict):

        ret_list = [(str(k), str(v)) for k, v in arg_dict.items()]

        data_len = len(ret_list)

        return ret_list, data_len
    
    def getSlopeIntercept(self, type):
        slope_intercept_list = []
        
        laser_dict = self.getLaserDict(type)

        laser_list, list_len = self.convertDictToList(laser_dict)

        for i in range(len(laser_list)):
            if i > 0:
                dx = Decimal(laser_list[i][0]) - Decimal(laser_list[i - 1][0])
                dy = Decimal(laser_list[i][1]) - Decimal(laser_list[i - 1][1])
                m = Decimal(dy) / Decimal(dx)
                mx = m * Decimal(laser_list[i][0])
                c = Decimal(laser_list[i][1]) - Decimal(mx)

                tuple_element = (m, c)
                slope_intercept_list.append(tuple_element)

        return slope_intercept_list
    
    def setLaserType(self, type):
        self.type = type

    def getLaserType(self):
        return self.type

    def getPower(self, laser_current):
        current = float(laser_current)
        min_current = 0
        max_current = 0

        laser_type = self.getLaserType()

        laser_dict = self.getLaserDict(laser_type)
        
        laser_list, laser_list_len = self.convertDictToList(laser_dict)
        
        slope_intercept_list = self.mapSlopeIntercept(laser_type)

        min_current = Decimal(laser_list[0][0])
        max_current = Decimal(laser_list[laser_list_len - 1][0])

        result = any(i for i in laser_dict if i == current)        

        if result:
            power = laser_dict[current]
            power_status = "range"

        else:
            if min_current < current < max_current:
                index = len([i[0] for i in enumerate(laser_dict) if current > Decimal(i[1])])
                slope = slope_intercept_list[index - 1][0]
                intercept = slope_intercept_list[index - 1][1]

                power = (Decimal(str(slope)) * Decimal(str(current))) + Decimal(str(intercept))
                power_status = "range"
            
            elif current < min_current:
                power_status = "min"
                power = 0

            elif current > max_current:
                power_status = "max"
                power = 0

        return power_status, power
    
    def getDensity(self, current, diameter):
        decimal.getcontext().prec = 3
        radius = Decimal(str(diameter)) / Decimal(str(2))
        area = Decimal(str(3.14)) * Decimal(str(radius)) * Decimal(str(radius))
        density = 0
        density_status = ""

        power_status, power = self.getPower(current)

        if area > 0:
            try:
                if power_status == "range":
                    density = Decimal(str(float(power))) / Decimal(str(area)) * Decimal(100.0)
                    density_status = "valid"

                else:
                    density = 0
                    density_status = "invalid"

            except:
                density = 0
                density_status = "error"
        else:
            density = 0
            density_status = "undefined"
        
        return density_status, density
    
    def getLasersType(self):
        # Add other baud rate options dynamically if needed
        laser_type_list = ["1W", "2W", "8W"]
        return laser_type_list
