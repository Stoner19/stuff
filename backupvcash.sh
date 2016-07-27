#!/bin/sh

#Add timestamp

TS=$(date +"%Y-%m-%d")
echo $TS

echo "<-- START BACKUP"

#Specify how the tar archive will be named

BKPNAME="vcashbackup-$TS"
BKFOLDER="$HOME/backups/" # specify the folder location for the backup here - edit this as needed
BKSOURCE="$HOME/.Vcash"

echo "Variables Created"


#Tar it
tar -zcvf "$BKFOLDER$BKPNAME.tar.gz" "$BKSOURCE"

echo "Backup completed and stored in file $BKFOLDER$BKPNAME.tar.gz"
echo "END BACKUP-->"
