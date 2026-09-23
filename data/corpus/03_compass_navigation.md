# Compass Navigation Stack

Compass is Helix Robotics' proprietary navigation and fleet-coordination software. Version 1.0 shipped in September 2021. The current stable release is Compass 3.4, released in February 2026, and it runs on Ubuntu 22.04 with ROS 2 Humble.

Compass has three layers. The perception layer fuses lidar scans, fisheye camera images and wheel odometry into a pose estimate at 50 Hz. The planning layer uses a time-windowed A-star planner on a grid with 50 mm cells and replans every 200 milliseconds. The fleet layer, called Conductor, runs on the warehouse server and assigns tasks to robots using an auction-based allocator; each task is auctioned to the robot with the lowest estimated completion time.

Conductor can coordinate up to 400 robots per warehouse on a single server. Deadlock resolution is handled by a priority scheme in which robots carrying loaded shelves outrank empty robots, and among equals the robot that has waited longer wins. Emergency stop commands propagate to every robot within 150 milliseconds.

Compass exposes a REST API on port 8443 and a WebSocket event stream on port 8444. Authentication uses short-lived JWT tokens that expire after 15 minutes. All robot logs are retained on the fleet server for 90 days and then archived to object storage. The Compass team is led by Priya Nair, who joined Helix from an autonomous driving startup in 2020.
