import requests
import datetime
import pytz
import sys 
from geopy.geocoders import Nominatim
from timezonefinder import TimezoneFinder

# API endpoint URL
url = "https://aa.usno.navy.mil/api/rstt/oneday"

# Search for coordinates using GeoPy
def find_latlong(city, state):
  """
  Find the latitude and longitude coordinates for a given city and state.

  Args:
      city (str): City name.
      state (str): State name or abbreviation.

  Returns:
      tuple: (latitude, longitude) coordinates.

  Raises:
      ValueError: If the city and state cannot be found.
  """
  geolocator = Nominatim(user_agent="moon_data_app")
  location = geolocator.geocode(f"{city}, {state}")
  if location is None:
      raise ValueError(f"Could not find coordinates for {city}, {state}")

  latitude = location.latitude
  longitude = location.longitude
  return latitude,longitude

# Get city and state from the user
def get_citystate():
    """
    Get city and state from user input.

    If the '-d' flag is provided on the command line, default to El Paso, TX.
    Otherwise, prompt the user for input. Strip and title the city name, and
    strip and upper the state name.

    Returns:
        tuple: (city, state)
    """
    if '-d' in sys.argv:
        city = "El Paso"
        state = "tx"
    else:
        city = input("Enter the city: ")
        state = input("Enter the state: ")

    city = city.title().strip()
    state = state.upper().strip()
    return city,state

def get_timezone(latitude, longitude):
    """
    Find the timezone and offset for a given latitude and longitude.

    Args:
        latitude (float): Latitude of the location.
        longitude (float): Longitude of the location.

    Returns:
        tuple: (tz_label, offset) where tz_label is the timezone string
          (e.g. "America/New_York"), and offset is the number of hours
          offset from UTC.

    Raises:
        pytz.UnknownTimeZoneError: If the timezone cannot be found.
    """
    tz_finder = TimezoneFinder()
    tz_label = tz_finder.timezone_at(lng=longitude, lat=latitude)
    tz = pytz.timezone(tz_label)
    offset = tz.utcoffset(datetime.datetime.now()).total_seconds() / 3600
    return tz_label,offset

def find_moon_data(data):
    """
    Find the moonrise and moonset times from the given moon data.

    Args:
        data (dict): The moon data returned from the API.

    Returns:
        tuple: (moonrise, moonset) where moonrise and moonset are the
          respective times of the moonrise and moonset, or "N/A" if the
          information is not available.
    """
    moonrise = "N/A"
    moonset = "N/A"
    for item in data['properties']["data"]["moondata"]:
        if item["phen"] == "Rise":
            moonrise = datetime.datetime.strptime(item["time"], "%H:%M").strftime("%I:%M %p")
        elif item["phen"] == "Set":
             moonset = datetime.datetime.strptime(item["time"], "%H:%M").strftime("%I:%M %p")
    return moonrise,moonset

def print_moon_data(today, tz_label, offset, moonrise, moonset):
    """
    Print the moonrise and moonset times for a specific date and location.

    Args:
        today (str): The current date in 'YYYY-MM-DD' format.
        tz_label (str): The timezone label (e.g. "America/New_York").
        offset (float): The timezone offset from UTC in hours.
        moonrise (str): The moonrise time in 'hh:mm AM/PM' format or "N/A".
        moonset (str): The moonset time in 'hh:mm AM/PM' format or "N/A".

    This function displays the moonrise and moonset times for the given date
    and timezone. If the '-d' flag is present in the command line arguments,
    it indicates that the program is running in debug mode and defaults to
    the city El Paso, TX.
    """
    if '-d' in sys.argv:
        print(f"Running in debug mode. Defaulting to city (El Paso, TX)") 
    offset_sign = "+" if offset >= 0 else "-"
    print(f"# Moon rise/set times in (Timezone: {tz_label} {offset_sign}{abs(offset)}) on {today}:")
    print(f"-  RISE: {moonrise}")
    print(f"-  SET: {moonset}")

def main():
  """
  Main entry point for the program.

  This function retrieves the city and state from the user, finds the
  latitude and longitude coordinates, and gets the timezone and offset.
  It then sends a request to the USNO API to retrieve the moon data and
  prints the moonrise and moonset times for the given date and location.

  If the '-d' flag is present on the command line, the program defaults to
  the city El Paso, TX.

  Raises:
      ConnectionError: If the request to the API fails.
  """
  city, state = get_citystate()
  latitude, longitude = find_latlong(city, state)
  today = datetime.date.today().strftime("%Y-%m-%d")
  tz_label, offset = get_timezone(latitude, longitude)

  # Define parameters
  params = {
      "date": today,
      "coords": f"{latitude:.2f},{longitude:.2f}",
      "tz": offset,
      "dst": "false"
  }

  # Send the request and get the response
  response = requests.get(url, params=params)
  # Check for errors
  if response.status_code != 200:
      raise ConnectionError(f"Failed to retrieve moon data. Status code: {response.status_code}")

  # Parse the JSON data
  data = response.json()
  moonrise, moonset = find_moon_data(data)

  print_moon_data(today, tz_label, offset, moonrise, moonset)


if __name__ == "__main__":
  main()

