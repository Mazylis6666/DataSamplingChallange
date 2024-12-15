from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
import re

class MeasType(Enum):
  SPO2 = 1
  HR = 2
  TEMP = 3

@dataclass
class Measurement:
  measurementTime: datetime = datetime.min
  measurementType: MeasType = MeasType.SPO2
  value: float = 0.0

def unsampledDataParser(raw_data: str, regex_pattern: str) -> list[Measurement]:
    """Parses raw measurement data using a regex pattern."""
    matched_data = re.findall(regex_pattern, raw_data)
    unsampled_measurements = []
    for match in matched_data:
        try:
            measurement_time = datetime.fromisoformat(match[0])
            measurement_type = MeasType[match[1]]
            value = float(match[2])
            unsampled_measurements.append(Measurement(measurement_time, measurement_type, value))
        except (ValueError, KeyError) as e:
            print(f"Invalid data: {match}, Error: {e}")
    return unsampled_measurements

def sampleMeasurement(
    startOfSampling: datetime,
    intervalLength: timedelta,
    unsampledMeasurements: list[Measurement]
)-> dict[MeasType, list[Measurement]]:
    """
    Samples measurements into fixed intervals and overwrites the timestamps with a intervalEnd.
    IntervalMap[IntervalEnd] on every loop overwrites the measurement object for a specific interval
    there fore only the last measurement object is left at the end.
    """
    if not unsampledMeasurements:
        return {meas_type: [] for meas_type in MeasType}
    sampledMeasurements = {}
    unsampledMeasurements.sort(key=lambda measurement: measurement.measurementTime)

    for meas_type in MeasType:
      sampledMeasurements[meas_type] = []

    for measurement in unsampledMeasurements:
      sampledMeasurements[measurement.measurementType].append(measurement)

    for measurementType, measurements in sampledMeasurements.items():
        intervalMap = {}
        for measurement in measurements:
            adjustedTime = measurement.measurementTime - timedelta(seconds=1) if measurement.measurementTime.second == 0 and measurement.measurementTime.minute % 5 == 0 else measurement.measurementTime
            timeDelta = adjustedTime - startOfSampling
            minutesSinceStart = (timeDelta.total_seconds() // intervalLength.total_seconds()) + 1
            intervalEnd = startOfSampling + timedelta(seconds=minutesSinceStart * intervalLength.total_seconds())
            intervalMap[intervalEnd] = measurement
            measurement.measurementTime = intervalEnd
        sampledMeasurements[measurementType] = list(intervalMap.values())

    return sampledMeasurements

#USAGE STARTS HERE
#Input preparation
rawData = """
{2017-01-03T10:04:45, TEMP, 35.79}
{2017-01-03T10:01:18, SPO2, 98.78}
{2017-01-03T10:09:07, TEMP, 35.01}
{2017-01-03T10:03:34, SPO2, 96.49}
{2017-01-03T10:02:01, TEMP, 35.82}
{2017-01-03T10:05:00, SPO2, 97.77}
{2017-01-03T10:05:01, SPO2, 95.08}
{2017-01-03T10:09:45, TEMP, 35.79}
{2017-01-03T10:06:18, SPO2, 98.78}
{2017-01-03T10:14:07, TEMP, 35.01}
{2017-01-03T10:08:34, SPO2, 96.49}
{2017-01-03T10:07:01, TEMP, 35.82}
{2017-01-03T10:10:00, SPO2, 97.17}
{2017-01-03T10:10:01, SPO2, 95.08}
"""
regexPattern = r"\{([\d\-T:]+), (\w+), ([\d.]+)\}"
startOfSampling = datetime(2017, 1, 3, 10, 0, 0)
intervalLength = timedelta(minutes=5)

#Call Functions
unsampledMeasurements = unsampledDataParser(rawData, regexPattern)
sampledMeasurements = sampleMeasurement(startOfSampling, intervalLength, unsampledMeasurements)

#Output is printed according to task output view
for measType, measurements in sampledMeasurements.items():
    for measurement in measurements:
      output = f"{{{measurement.measurementTime.strftime('%Y-%m-%dT%H:%M:%S')}, {measurement.measurementType.name}, {measurement.value:.2f}}}"
      print(output)
