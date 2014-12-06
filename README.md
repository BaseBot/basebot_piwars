# piwars robot repo

This is a rough-and-ready working repository which I'll push to with reckless
abandon. It pulls in a bunch of different components which should be in
separate repos, but time is short and maintaining all the subprojects is a
chore.

## External Dependencies
 * You need ServoBlaster
   * (https://github.com/richardghirst/PiBits/tree/master/ServoBlaster)
	 * Set up the user-space daemon with a step size of 2 us
	   * ServoBlaster/user/servod --step-size=2us
	   * The full robot uses servos 0-6
 * You need the i2c driver and i2c-dev driver
   * insmod i2c-bcm2708.ko
   * insmod i2c-dev.ko
 * You need permissions to the i2c bus (it uses /dev/i2c-1 by default).
   i2c-1 is the i2c bus on the expansion header of the B+, on the model A and B
   use i2c-0 instead
 * We assume there are 2 TinyEncs on the i2c bus, at 0x40 and 0x41 (7-bit)
   * https://github.com/usedbytes/i2c_encoder
 * We assume there is a tiny_adc on the i2c bus at 0x10
   * With 5 infrared reflectance sensors on channels 0-4
   * https://github.com/usedbytes/tiny_adco

## How to run
 * You need to set the IP address for the server in main.py
 * The robot needs the serial port! Tell the kernel not to use it and don't
   getty on it!
 * Run the robot script:
   * python -i main.py
     * >>> robo.loop()
 * Either on the same box or somewhere else, run the client:
   * python -i stick_sampler.py

## Architecture

 * **main.py**
   * Contains description of the robot and its components in a dict
   * Initialises the logging infrastructure
   * Instantiates some peripherals:
     * i2c bus
     * wall sensor/line sensor
     * eyes
   * Has "macros" to do the autonomous challenges
   * Instantiates the main robot class:
     * **classrobot.Robot**
       * Sets up a packetcomms.Server to listen for commands "over the wire"
       * Instantiates a chassis:
         * **tanksteer.Tanksteer**
           * Maintains a dead-reckoning heading and position
           * Instantiates wheels
             * **wheel.Wheel**
               * Have a closed-loop controller to control speed
               * Instantiates **servo.Servo** for driving
               * Instantiates **tinyenc.TinyEnc** for sensing rotation
       * Has a current "task" which determines behaviour
         * **waypointtask.WaypointTask**: visits waypoints
             * Based purely on chassis dead-reckoning
         * **linetask.LineFollowerTask**: follows a line
             * Uses **linesensor.LineSensor** readings
         * **walltask.WallTask**: Drives until it senses a wall
             * Uses **wallsensor.WallSensor** readings
       * **Robot.loop()** continuously senses, plans and acts
         * *sense*: Read all sensors, determine current heading and position
         * *plan*: Ask current task to plan next move based on sensors
           * Commands over-the-wire override tasks
         * *act*: Do whatever the plan stage asked for
    * Sets up a **serialsocket.SerialSocket**:
      * Forwards data from the serial port to the **Robot** instance

