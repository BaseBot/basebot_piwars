#!/bin/sh
# Copy all the files!

MOUNT_POINT=$HOME/mnt
TARGET_DIR=$MOUNT_POINT/robot
FILES_LIST="servo.py tinyenc.py wheel.py tanksteer.py\
	main.py classrobot.py packetcomms.py linesensor.py linetask.py \
	serialsocket.py waypointtask.py\
	wallsensor.py walltask.py PiWars eyemanager.py"


if mount | grep -E "pi@.* on $MOUNT_POINT"
then
	for file in $FILES_LIST
	do
		cp -urv $file $TARGET_DIR
	done
else
	echo "mount point not found!"
	exit 1
fi

