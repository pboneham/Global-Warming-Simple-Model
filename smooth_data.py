import scipy.signal as signal
import pandas

dataset = pandas.read_csv("../datasets_generated/globalTempsAndConcentrations.csv", "\t")

smoothed = signal.savgol_filter(dataset["Temperature"], 9, 2)

counter = 0
while counter < len(dataset["Year"]):
	print(dataset["Year"][counter], smoothed[counter])
	counter += 1
