# piwars robot repo

This is a rough-and-ready working repository which I'll push to with reckless
abandon. It pulls in a bunch of different components which should be in
separate repos, but time is short and maintaining all the subprojects is a
chore.


Very short summary of this:
 * You need ServoBlaster
   * (https://github.com/richardghirst/PiBits/tree/master/ServoBlaster)
 * Set up the user-space daemon with a step size of 2 us
   * ServoBlaster/user/servod --step-size=2us
   * The script uses servos 0 and 1 (P1-7 and P1-11)
 * You need the i2c driver and i2c-dev driver
   * insmod i2c-bcm2708.ko
   * insmod i2c-dev.ko
 * The script needs permissions to the i2c bus (it uses /dev/i2c-1 by default).
   i2c-1 is the i2c bus on the expansion header of the B+, on the model A and B
   use i2c-0 instead
 * The script assumes there are 2 TinyEncs on the i2c bus, at 0x40 and 0x41
   (7-bit)
 * You need to set the IP address for the client/server
 * Run the robot script:
   * python -i robot.py
 * Either on the same box or somewhere else, run the client:
   * python -i stick_handler.py

The script sets up a server listening on port 9000 which is listened to for
TelecommandPackets telling the robot what to do.

stick_listener.py is a very basic client which reads from /dev/js0 (which it
assumes is an xpad xbox controller) and uses the left thumbstick to
sendcommands.
