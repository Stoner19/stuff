# stuff
General things

# backupvcash.sh

Bash shell script that I use to backup the .Vcash directory before an update or just for general use

This is best run when the vcash wallet daemon is stopped
Otherwise it will report errors if open files are changed whilst the tar file is created.

Usage

1. Download the script or use copy paste into a suitable text editor and save the file into the root of your home directory
2. Edit the script and change the backup location or just create a folder in your home directory called "backups"
 
My "backups" folder is actually a symlink to a network share on another host but that's another story

3. Ensure the file attributes allow execution e.g run chmod +x backupvcash.sh

4. Run the script from the home directory using the terminal command:

./backupvcash.sh

5. The output progress should be displayed on your screen but if you wish to log output to a file for later review then use:

./backupvcash > logfilename.txt
