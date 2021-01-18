import time

from dronekit import connect, VehicleMode, LocationGlobalRelative, Command, LocationGlobal
from pymavlink import mavutil


# -----------FUNCTIONS----------#

#--------- Arm and takeoff--------#
def arm_and_takeoff(altitude):

    while not vehicle.is_armable:
        print("waiting to be armable")
        time.sleep(1)

    print("Arming motors")
    vehicle.mode = VehicleMode("GUIDED")
    vehicle.armed = True

def clear_mission(vehicle):
    #---- Clear the current mission ----#
    cmds = vehicle.commands
    cmds.clear()
    vehicle.flush()

    #----- download the mission again ------#
    download_mission(vehicle)

def download_mission(vehicle):
    cmds = vehicle.commands
    cmds.download()
    cmds.wait_read()

def get_current_mission(vehicle):
    #----- download the current mission, returns the number of waypoints and the list
    print ("Downloading the mission")
    download_mission(vehicle)
    missionList = []
    n_wp = 0

    for wp in vehicle.commands:
        missionList.append(wp)
        n_wp +=1
    
    return n_wp, missionList

def add_last_waypoint_to_mission(vehicle, lat, long, alt):
    #---- Adds a last waypoint to a mission list ----#
    download_mission()
    cmds = vehicle.commands

    #---- Save the mission to a temporary list ----#
    missionList = []
    for wp in cmds:
        missionList.append(wp)
    
    #---- Append a last waypoint ----#
    wp_last = Command(0, 0, 0, mavutil.mavlink.MAV_FRAME_GLOBAL_RELATIVE_ALT, mavutil.mavlink.MAV_CMD_NAV_WAYPOINT,
                      0, 0, 0, 0, 0, 0,
                      lat, long, alt)
    missionList.append(wp_last)

    #--- Clear the current mission ----#
    cmds.clear()

    #--- We write the new mission -----#
    for wp in missionList:
        cmds.add(wp)
    
    cmds.upload()

    return (cmds.count)

def ChangeMode(vehicle, mode):
    # ---- Change autopilot mode -----#
    while vehicle.mode != Vehicle(mode):
        vehicle.mode = VehicleMode(mode)
        time.sleep(0.5)

    return True


# ------------ INITIALIZE ------------#

gnd_speed = 10
mode = 'GROUND'

# ------------ CONNECT ---------------#

vehicle = connect('udp:127.0.0.1:14551')


# ------------ MAIN FUNCTION ---------#

while True:
    if mode == 'GROUND':
        # --- Wait until a valid mission has been upload --- #
        n_wp, missionList = get_current_mission(vehicle)
        time.sleep(2)

        if n_wp > 0:
            print ("A valid mission has been uploaded: takeoff")
            mode = 'TAKEOFF'

    elif mode == 'TAKEOFF':
        # --- add the current position as last waypoint ----#
        add_last_waypoint_to_mission(vehicle,
                                     vehicle.location.global_relative_frame.lat,
                                     vehicle.location.global_relative_frame.lon,
                                     vehicle.location.global_relative_frame.alt)
        
        print("Final waypoint added to the current mission")
        time.sleep(1)

        # ---- Takeoff ----- #
        arm_and_takeoff(10)

        # ---- Set the ground speed ---- #
        vehicle.groundspeed = gnd_speed

        mode = 'MISSION'
        print("Switch to MISSION mode")

    elif mode == 'MISSION':
        # ---- monitor the mission, when the current waypoint is equal to the number of wp
        # ---- we go back home, we clear the mission and land
        
        # ----                         current_waypoint_id         total_number
        print("Current WP: %d of %d "%(vehicle.commands.next, vehicle.commands.count)) 

        if (vehicle.commands.next == vehicle.commands.count):
            print ("Final wp reached: go back home")

            # ---- Clear the mission ----#
            clear_mission(vehicle)
            print ("Mission deleted")

            ChangeMode(vehicle, "RTL")     

            mode = "BACK"

    elif mode == "BACK":
        # --- when the altitude is below 1, switch to GROUND ----- #
        if vehicle.location.global_relative_frame.alt < 1.0:
            print("Vehicle landed, back to GROUND")
            mode = "GROUND"


    time.sleep(0.5)




