# global warming model - python
import pandas
import math
import json
import argparse

def loadDataToList(data, listToFill, divideByValue = 1.0):
    counter = 0
    while counter < len(data):
        listToFill.append(data[counter]/divideByValue)
        counter += 1

def findIndexOfItemInList(item, listToSearch):
    counter = 0
    while counter < len(listToSearch):
        if int(item) == int(listToSearch[counter]):
            break
        counter += 1
    return counter

class warmingModel:
    
    def __init__(self):
        pass
        
    def setCh4Fac(self, val):
        self.ch4Fac = val
        
    def setCo2Fac(self, val):
        self.co2Fac = val
        
    def setN2oFac(self, val):
        self.n2oFac = val

    def setEmissResidualFac(self, val):
        self.emissResidualFac = val

    def setAtmMolarDens(self, val):
        self.atmMolarDens = val
        
    def setAtmPathLength(self, val):
        self.atmPathLength = val
        
    def setLinCoeff(self, val):
        self.linCoeff = val

    def setA(self, val):
        self.A = val

    def setB(self, val):
        self.B = val

    def setS(self, val):
        self.S = val
        
    def setAlpha(self, val):
        self.alpha = val

    def loadGreenhouseGasesHistory(self, greenhouseGasesHistoryCsv, ch4ppb = 0, n2oppb = 0):
        data = pandas.read_csv(greenhouseGasesHistoryCsv, "\t")
        self.years = []
        loadDataToList(data["Year"], self.years, 1.0)
        self.ch4ppm = []
        if ch4ppb == 0:
            loadDataToList(data["CH4"], self.ch4ppm, 1.0)
        else:
            loadDataToList(data["CH4"], self.ch4ppm, 1000.0)
        self.co2ppm = []
        loadDataToList(data["CO2"], self.co2ppm, 1.0)
        self.n2oppm = []
        if n2oppb == 0:
            loadDataToList(data["N2O"], self.n2oppm, 1.0)
        else:
            loadDataToList(data["N2O"], self.n2oppm, 1000.0)
        start = self.years[0]
        end = self.years[-1]
        return start, end

    def emissivity(self, ch4ppm, co2ppm, n2oppm):
        x =  -self.ch4Fac * ch4ppm/1e6 * self.atmMolarDens * self.atmPathLength
        x += -self.co2Fac * co2ppm/1e6 * self.atmMolarDens * self.atmPathLength
        x += -self.n2oFac * n2oppm/1e6 * self.atmMolarDens * self.atmPathLength
        x += -self.emissResidualFac/1e6 * self.atmMolarDens * self.atmPathLength
        return 1.0 - math.exp(x)

    def calcTeq(self, emiss):
        temp = 1.0/self.B * ( (1.0-self.alpha) / ( 1.0-emiss/2.0 ) * self.S/4.0 - self.A )
        return temp

    def velocity(self, T, Teq):
        return -(T-Teq)*self.linCoeff

    def loadReferenceTemperatureHistory(self, fn):
        data = pandas.read_csv(fn, "\t")
        self.temperatureHistory = []
        self.temperatureHistoryYears = []
        loadDataToList(data["Year"], self.temperatureHistoryYears)
        loadDataToList(data["Temperature"], self.temperatureHistory)
        

    def runModel(self, initTime, initTemp, steps):
        f = open("results.dat", "w")
        counter = 0
        initTimeIndex = findIndexOfItemInList(initTime, self.years)
        try:
            len(self.temperatureHistoryYears)
            initTimeIndexTemperatureHistory = findIndexOfItemInList(initTime, self.temperatureHistoryYears)
        except:
            print("Start year not found in temperature dataset - there may be a problem with your input data")
            exit(0)
        temp = initTemp
        errors = 0.0
        while counter < steps:
            ch4ppm = 0.5 * (self.ch4ppm[initTimeIndex+counter] + self.ch4ppm[initTimeIndex+counter+1])
            co2ppm = 0.5 * (self.co2ppm[initTimeIndex+counter] + self.co2ppm[initTimeIndex+counter+1])
            n2oppm = 0.5 * (self.n2oppm[initTimeIndex+counter] + self.n2oppm[initTimeIndex+counter+1])
            # sens - fix concentrations at 1880 values
            #ch4ppm = 826.5 / 1000.0
            #co2ppm = 289.8
            #n2oppm = 275.8 / 1000.0
            emiss = self.emissivity(ch4ppm, co2ppm, n2oppm)
            teq = self.calcTeq(emiss)    # calc mid-timestep equilib temp
            v = self.velocity(temp, teq) # use equilib temperature to calc temperature velocity
            temp += v                    # update temperature
            refTemp = self.temperatureHistory[counter+initTimeIndexTemperatureHistory+1]
            errors += math.pow((temp - refTemp)/refTemp, 2.0)
            counter += 1
            f.write(str(self.years[counter+initTimeIndex]) + "\t" + str(temp) + "\t" + str(teq) + "\t" + str(emiss) + "\n")
        errors = math.sqrt(errors/float(steps))
        f.close()
        return errors

    
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--json", help="JSON file containing model params", action="store")
    parser.add_argument("--ghg_csv", help="csv file containing GHG data and temps", action="store")
    parser.add_argument("--start_year", help="Year in GHG datafile at which to start (defaults to first entry in data)", action="store")
    parser.add_argument("--end_year", help="Year in GHG datafile at which to end calc (defaults to last entry in data)", action="store")
    parser.add_argument("--init_temp", help="Initial temperature - take from temperature record for start year", action="store")
    args = parser.parse_args()
    if args.json != None:
        loadFromJson = 1

    if args.ghg_csv != None:
        ghg_csv = args.ghg_csv
    else:
        ghg_csv = "globalTempsAndConcentrations.csv"
    f = open(args.json, "r")
    params = json.load(f)
    f.close()
    model = warmingModel()
    model.setLinCoeff(params["linCoeff"])
    model.setEmissResidualFac(params["emissResidualFac"])
    model.setCh4Fac(params["ch4Fac"])
    model.setCo2Fac(params["co2Fac"])
    model.setN2oFac(params["n2oFac"])
    model.setAtmMolarDens(params["atmMolarDens"])
    model.setAtmPathLength(params["atmPathLength"])
    model.setA(params["a"])
    model.setB(params["b"])
    model.setS(params["s"])
    model.setAlpha(params["alpha"])

    start_year, end_year = model.loadGreenhouseGasesHistory(ghg_csv, 1, 1)
    model.loadReferenceTemperatureHistory(ghg_csv)
    
    if args.start_year != None:
        if int(args.start_year) >= start_year and int(args.start_year) < end_year:
            start_year = int(args.start_year)
        else:
            print("You supplied an invalid start year")
            exit(0)

    if args.end_year != None:
        if int(args.end_year) <= end_year and int(args.end_year) > start_year:
            end_year = int(args.end_year)
        else:
            print("You supplied an invalid end year")
            exit(0)

    if args.init_temp == None:
        print("An initial temperature must be supplied")
        exit(0)

    report_errors = 1
    if report_errors == 1:
        print(model.runModel(start_year, float(args.init_temp), end_year - start_year))  # minimum run is initial timepoint + the following year; = 1 step
    else:
        model.runModel(start_year, float(args.init_temp), end_year - start_year)


main()
