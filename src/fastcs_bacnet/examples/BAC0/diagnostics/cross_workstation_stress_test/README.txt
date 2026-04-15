This directory is for running cross workstation stress tests (as the name suggests)
This runs a BACnet client that subscribes to several bacnet objects on the local network from various IPs, and ports
Comparing the processed subscriptions to the ones recieved by the computer (measured using wireshark) is the most
accurate stress test that can be performed without actual BACnet devices

This is done in 5 parts: Starting the server, starting wireshark, starting the client, saving output of wireshark and
running the comparison

Start the server(s):
Choose another machine (or machines) on the same network. Clone the repository to these machines and run
cross_workstation_server.py on each. Eventually these will allow command line arguments for the number of
devices and objects (per device) but this has not been implemented yet. For now users can change these variables
by editing the script on the server machine they are using.

Start wireshark:
Next, start wireshark. Packages should be filtered so that only BACnet ones are visible (type bacnet in the top
bar and press enter). The visible columns, as well as their names, must also be configured. Right click the
bar that holds the column names and click column preferences. Make sure only the following columns are visible:
Title   type
Source  Source Address
Info    Information
Time    UTC time (NOTE: this is NOT the default column type for the Time column)
Port    Source Port
Packets should show up until you start the bacnet client script

Run the client:
On the main machine run the cross_workstation_client.py script in this directory. Make sure to change the constants 
(and IP list) in this file to match the IP addresses, ports and objects started on other machines. You should now
start to see traffic coming through on wireshark. You can also change the time period of the test by adjusting the
value in the sleep function call (this will be made a variable in future). When the test is finnished a file will be
created called recieved_BAC0_updates.txt.

Save the wireshark output:
When the test finishes stop the wireshark process and save its output. File -> Export Packet Dissections -> As CSV.

Run the comparison script:
Change the parameters of the function call to match the paths of the client output file and the wireshark output File
respectively. Then run the python script. If all is done correctly some statistics about test will be output.



The statistics:
total updates: Every package matching the BAC0 subscription update format picked up by wireshark
missed objects: The number of subscriptions that never got a response (and were picked up by wireshark)
missed updates: The number of update packages picked up by wireshark but not processed by the BACnet client
    This does not include packages from missed objects as we assume there was something wrong with the object
mystery updates: The number of update packages processed by BAC0 but not picked up by wireshark
    Should never happen, thats why its a mystery when it does
reliability score: Total updates processed (excluding mystery updates) / total updates seen by wireshark
total unique IPs: self explanatory
total unique ports: This is just unique port numbers, not unique IP:port pairs
total unique object instance numbers: This is unique between all devices
