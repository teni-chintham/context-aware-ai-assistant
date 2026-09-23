# Orbit 2 Technical Specification

The Orbit 2 is Helix's heavy-duty shelf-carrying autonomous mobile robot. It measures 1080 mm long, 780 mm wide and 310 mm tall in its lowered state, and lifts shelves by 60 mm using a screw-jack mechanism driven by a 400 W brushless motor.

Rated payload is 600 kg. Maximum unloaded speed is 2.0 metres per second and maximum loaded speed is 1.5 metres per second. The robot runs on a 48 V lithium iron phosphate battery pack with a capacity of 30 Ah, which gives roughly 9 hours of mixed operation. Charging from 20 percent to 90 percent takes 55 minutes on the Helix DockPro charger. The robot automatically returns to a dock when charge falls below 22 percent.

Positioning accuracy is plus or minus 5 mm against floor fiducial markers, and plus or minus 20 mm in free navigation using lidar and camera fusion. The lidar is a Hokuyo UST-10LX with a 10 metre range. Obstacle detection uses two forward-facing depth cameras and a rear ultrasonic array. The safety controller is certified to Performance Level d under ISO 13849.

The Orbit 2 communicates with the fleet server over Wi-Fi 6 and falls back to a 4G module if Wi-Fi is lost for more than 30 seconds. Firmware updates are delivered over the air and take about 4 minutes, during which the robot must be docked. The operating temperature range is 0 to 45 degrees Celsius. Each unit ships with a 24-month warranty, extendable to 48 months.
